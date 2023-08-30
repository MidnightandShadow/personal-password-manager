from sqlite3 import Connection, Cursor, connect, Row
from typing import Union, Tuple, List

from argon2.exceptions import HashingError

from Utils.cryptography import derive_256_bit_salt_and_key, decrypt_aes_256_gcm


def get_user_id_by_email(email: str, connection: Connection) -> Union[int, None]:
    """
    Returns the corresponding user_id if a User with the given email exists, else None.
    :param email: the email to query the Users table with
    :param connection: the database connection to use
    :return: the associated user_id if the User exists, None if not
    """
    cursor = connection.cursor()

    cursor.execute("SELECT id FROM users WHERE email=?", (email,))

    result = cursor.fetchone()

    user_id = result[0] if result else None

    return user_id


def get_login_password_by_email(email: str, connection: Connection) -> Union[str, None]:
    """
    Returns the hashed login password for a User by a given email if a User with the email exists, else None.
    :param email: the email to query the Users table with
    :param connection: the database connection to use
    :return: the associated password if the User exists, None if not
    """
    cursor = connection.cursor()

    cursor.execute("SELECT password FROM users WHERE email=?", (email,))

    result = cursor.fetchone()

    password = result[0] if result else None

    return password


def get_account_id_by_account_name_and_user_id(account_name: str, user_id: int, connection: Connection) -> Union[int, None]:
    """
    Returns the id of the Account with the given account_name and user_id if the Account exists, else None.
    :param account_name: the name of the Account
    :param user_id: the id of the associated user
    :param connection: the database connection to use
    :return: the id of the corresponding Account if it exists, else None
    """
    cursor = connection.cursor()

    cursor.execute("SELECT id FROM accounts WHERE name=:name AND user_id=:user_id",
                   {'name': account_name, 'user_id': user_id})

    result = cursor.fetchone()

    account_id = result[0] if result else None

    return account_id


def get_all_account_names_and_logins_by_user(user_id: int, connection: Connection) -> Union[List[Tuple[str, str]], None]:
    """
    Returns the name and login of all Accounts for the User with the given id, else None.
    :param user_id: the id of the associated user
    :param connection: the database connection to use
    :return: all name and login of all Accounts for the User with the given id, else None
    """
    cursor = connection.cursor()

    cursor.execute("SELECT name, login FROM accounts WHERE user_id=?", (user_id,))

    result = cursor.fetchall()

    user_account_names_and_logins = result if result else None

    return user_account_names_and_logins


def get_decrypted_account_password(account_id: int, master_password: str, connection: Connection) -> str:
    """
    Returns the decrypted account password for an Account given the account id and the user's master password.
    :param account_id: the id of the account to decrypt the password for
    :param master_password: the user's master password
    :param connection: the database connection to use
    :return: the decrypted Account password
    :raise ValueError: if there is no account with the given id or if a cryptography error occurs
    """
    cursor = connection.cursor()

    cursor.execute("SELECT password, salt, nonce, tag FROM accounts WHERE id=?", (account_id,))

    row = cursor.fetchone()

    if not row:
        raise ValueError('There is no account with the given id')

    password, salt, nonce, tag = row

    try:
        key = derive_256_bit_salt_and_key(password=master_password, salt=salt)[1]
    except HashingError as e:
        raise ValueError(f'An error occurred while generating the key: {e}')

    try:
        plaintext = decrypt_aes_256_gcm(key=key, ciphertext=password, nonce=nonce, tag=tag)
    except ValueError as e:
        raise ValueError(f'An error occurred while decrypting the password: {e}')

    return plaintext


# Utils for testing:
def db_setup() -> Tuple[Connection, Cursor]:
    """
    Creates an in-memory database with the necessary tables, used for testing, and returns the corresponding
    Connection and Cursor.
    :return: (connection, cursor), where connection and cursor relate to the created in-memory database
    """
    connection = connect(":memory:")
    # connection.row_factory = Row
    cursor = connection.cursor()
    cursor.execute("PRAGMA foreign_keys = ON;")

    cursor.execute("""CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT UNIQUE,
                    password TEXT
                    ) STRICT ;""")

    cursor.execute("""CREATE TABLE IF NOT EXISTS accounts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT,
                    login TEXT,
                    password BLOB,
                    salt BLOB,
                    nonce BLOB,
                    tag BLOB,
                    user_id INTEGER,
                    FOREIGN KEY(user_id) REFERENCES users(id),
                    UNIQUE(name, user_id)
                    ) STRICT ;""")

    connection.commit()

    return connection, cursor
