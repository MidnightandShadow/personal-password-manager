import sqlite3
from sqlite3 import Connection, Cursor, connect
from typing import Tuple, List, Dict, Optional

from argon2 import PasswordHasher
from argon2.exceptions import HashingError, VerifyMismatchError, VerificationError, InvalidHashError

from Utils.cryptography import derive_256_bit_salt_and_key, decrypt_aes_256_gcm, encrypt_aes_256_gcm
from re import match as regex_match

from config import VALID_EMAIL_PATTERN


def create_user(email: str, password: str, connection: Connection) -> int:
    """
    Creates a new User in the database with the given email and a hash of the given password, returns the
    corresponding User id.
    :return: the id of the created User
    :raise ValueError: if the given email is invalid or an empty string, or if the given password is an empty string
    :raise argon2.exceptions.HashingError: if hashing fails
    """
    if not email:
        raise ValueError('The given email was an empty string')

    valid_email_format = regex_match(pattern=VALID_EMAIL_PATTERN, string=email)

    if not valid_email_format:
        raise ValueError(f'The given email ({email}) is invalid')

    if not password:
        raise ValueError('The given password was an empty string')

    cursor = connection.cursor()

    ph = PasswordHasher()
    hashed_password = ph.hash(password)

    cursor.execute("INSERT INTO users VALUES (:id, :email, :password) RETURNING id", {'id': None,
                                                                                      'email': email,
                                                                                      'password': hashed_password})

    user_id = cursor.fetchone()[0]

    connection.commit()
    cursor.close()

    return user_id


def create_account(user_id: int, master_password: str, name: str, url: Optional[str], username: str, password: str,
                   connection: Connection) -> int:
    """
    Creates a new Account in the database for the User with the given user_id and master_password using the given
    Account name, url (if provided), username, and password. The password is encrypted before storage and the
    accompanying cryptographic info is stored as well. Returns the corresponding Account id.
    :return: the id of the created Account
    :raise ValueError: if the given user_id is invalid or if the name, username, master_password, or password are empty
    strings (or if raised by a called cryptographic function)
    :raise Sqlite3.IntegrityError: if the passed name is already in use for another Account
    :raise argon2.exceptions.HashingError: if hashing fails
    :raise argon2.exceptions.VerifyMismatchError: if the User's hashed_password is not valid for the given
    master password
    :raise argon2.exceptions.InvalidHashError: if hash is invalid
    :raise argon2.exceptions.VerificationError: if there was a miscellaneous verification error (if the argon
    verification raised VerificationError as opposed to VerifyMismatchError or InvalidHashError)
    """
    cursor = connection.cursor()
    
    cursor.execute("SELECT EXISTS (SELECT 1 FROM users WHERE id=?)", (user_id,))

    user_exists = cursor.fetchone()[0]

    if not user_exists:
        raise ValueError(f'There is no User with the given user_id ({user_id})')

    if not master_password:
        raise ValueError('The given master_password was an empty string')
    
    if not name:
        raise ValueError('The given name was an empty string')

    if not username:
        raise ValueError('The given username was an empty string')

    if not password:
        raise ValueError('The given password was an empty string')

    ph = PasswordHasher()

    hashed_password = get_login_password_by_user_id(user_id, connection)

    ph.verify(hash=hashed_password, password=master_password)

    salt, key = derive_256_bit_salt_and_key(master_password)
    encrypted_password, nonce, tag = encrypt_aes_256_gcm(key, password)

    try:
        cursor.execute("""INSERT INTO accounts VALUES (:id, :name, :url, :username, :password, :salt, :nonce, :tag,
        :user_id) RETURNING id""",
                       {'id': None,
                        'name': name,
                        'url': url,
                        'username': username,
                        'password': encrypted_password,
                        'salt': salt,
                        'nonce': nonce,
                        'tag': tag,
                        'user_id': user_id})
    except sqlite3.IntegrityError as e:
        raise sqlite3.IntegrityError(f'The Account could not be created because this Account name is already '
                                     f'being used for this user: {e}')

    account_id = cursor.fetchone()[0]

    connection.commit()
    cursor.close()

    return account_id


def edit_account(account_id: int, connection: Connection, master_password: Optional[str] = None,
                 name: Optional[str] = None, url: Optional[str] = None, username: Optional[str] = None,
                 password: Optional[str] = None) -> None:
    """
    Edits the Account in the database with the given id using the given Account name, url, username, and password.
    Each field is optional to allow only changing one aspect of the Account. However, if the password is passed, the
    master_password must also be passed for re-encryption purposes. The changes are only committed if there is not
    an error.
    :raise ValueError: if the given account_id is invalid or if the password is passed without the master_password
    (or if raised by a called cryptographic function)
    :raise Sqlite3.IntegrityError: if the passed name is already in use for another Account
    :raise argon2.exceptions.HashingError: if hashing fails
    :raise argon2.exceptions.VerifyMismatchError: if the User's hashed_password is not valid for the given
    master password
    :raise argon2.exceptions.InvalidHashError: if hash is invalid
    :raise argon2.exceptions.VerificationError: if there was a miscellaneous verification error (if the argon
    verification raised VerificationError as opposed to VerifyMismatchError or InvalidHashError)
    """
    cursor = connection.cursor()

    cursor.execute("SELECT EXISTS (SELECT 1 FROM accounts WHERE id=?)", (account_id,))

    account_exits = cursor.fetchone()[0]

    if not account_exits:
        raise ValueError(f'There is no Account with the given id ({account_id})')

    if password and not master_password:
        raise ValueError('The given master_password was an empty string or was not provided')

    if name:
        try:
            cursor.execute("UPDATE accounts SET name=:name WHERE id=:account_id", {'name': name,
                                                                                   'account_id': account_id})
        except sqlite3.IntegrityError as e:
            raise sqlite3.IntegrityError(f'The name could not be updated because this Account name is already '
                                         f'being used for this user: {e}')

    if url:
        cursor.execute("UPDATE accounts SET url=:url WHERE id=:account_id", {'url': url,
                                                                             'account_id': account_id})

    if username:
        cursor.execute("UPDATE accounts SET username=:username WHERE id=:account_id",
                       {'username': username, 'account_id': account_id})

    if password and master_password:
        ph = PasswordHasher()

        cursor.execute("SELECT user_id FROM accounts WHERE id=?", (account_id,))
        user_id = cursor.fetchone()[0]

        hashed_password = get_login_password_by_user_id(user_id, connection)

        ph.verify(hash=hashed_password, password=master_password)

        salt, key = derive_256_bit_salt_and_key(master_password)
        encrypted_password, nonce, tag = encrypt_aes_256_gcm(key, password)

        cursor.execute("""UPDATE accounts SET password=:password, salt=:salt, nonce=:nonce, tag=:tag WHERE
        id=:account_id""", {'password': encrypted_password, 'salt': salt, 'nonce': nonce, 'tag': tag,
                            'account_id': account_id})

    connection.commit()
    cursor.close()


def delete_account(account_id: int, connection: Connection) -> None:
    """
    Removes the Account with the given id from the database.
    :param account_id: the id for the Account to be removed
    :param connection: the database connection to use
    :raise ValueError: if the given account_id is invalid
    """
    cursor = connection.cursor()

    cursor.execute("SELECT EXISTS (SELECT 1 FROM accounts WHERE id=?)", (account_id,))

    account_exits = cursor.fetchone()[0]

    if not account_exits:
        raise ValueError(f'There is no Account with the given id ({account_id})')

    cursor.execute("DELETE FROM accounts WHERE id=?", (account_id,))

    connection.commit()

    cursor.close()


def get_user_id_by_email(email: str, connection: Connection) -> Optional[int]:
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


def get_login_password_by_user_id(user_id: int, connection: Connection) -> Optional[str]:
    """
    Returns the hashed login password for a User if the User with the given id exists, else None.
    :param user_id: the id of the desired User
    :param connection: the database connection to use
    :return: the associated password if the User exists, None if not
    """
    cursor = connection.cursor()

    cursor.execute("SELECT password FROM users WHERE id=?", (user_id,))

    result = cursor.fetchone()

    password = result[0] if result else None

    cursor.close()

    return password


def get_account_id_by_account_name_and_user_id(account_name: str, user_id: int, connection: Connection)\
        -> Optional[int]:
    """
    Returns the id of the Account with the given account_name and user_id if the Account exists, else None.
    :param account_name: the name of the Account
    :param user_id: the id of the associated User
    :param connection: the database connection to use
    :return: the id of the corresponding Account if it exists, else None
    """
    cursor = connection.cursor()

    cursor.execute("SELECT id FROM accounts WHERE name=:name AND user_id=:user_id",
                   {'name': account_name, 'user_id': user_id})

    result = cursor.fetchone()

    account_id = result[0] if result else None

    return account_id


def get_account_name_url_and_username_by_account_id(account_id: int, connection: Connection)\
        -> Optional[Tuple[str, Optional[str], str]]:
    """
    Returns the name, url, and username of the Account with the given id if the Account exists, else None.
    :param account_id: the id of the Account to be queried
    :param connection: the database connection to use
    :return: the name and username of the Account with the given id if the Account exists, else None
    """
    cursor = connection.cursor()

    cursor.execute("SELECT name, url, username FROM accounts WHERE id=?", (account_id, ))

    result = cursor.fetchone()

    user_account_name_url_and_username = result if result else None

    cursor.close()

    return user_account_name_url_and_username


def get_all_account_names_urls_and_usernames_by_user_id(user_id: int, connection: Connection)\
        -> Optional[List[Tuple[str, Optional[str], str]]]:
    """
    Returns the name, url, and username of all Accounts for the User with the given id if they have Accounts, else None.
    :param user_id: the id of the associated user
    :param connection: the database connection to use
    :return: all name and username of all Accounts for the User with the given id if they have Accounts, else None
    """
    cursor = connection.cursor()

    cursor.execute("SELECT name, url, username FROM accounts WHERE user_id=?", (user_id,))

    result = cursor.fetchall()

    user_account_names_urls_and_usernames = result if result else None

    cursor.close()

    return user_account_names_urls_and_usernames


def get_decrypted_account_password(account_id: int, master_password: str, connection: Connection) -> str:
    """
    Returns the decrypted account password for an Account given the Account id and the User's master password.
    :param account_id: the id of the Account to decrypt the password for
    :param master_password: the User's master password
    :param connection: the database connection to use
    :return: the decrypted Account password
    :raise ValueError: if there is no Account with the given id or if a cryptography error occurs
    """
    cursor = connection.cursor()

    cursor.execute("SELECT password, salt, nonce, tag FROM accounts WHERE id=?", (account_id,))

    result = cursor.fetchone()

    if not result:
        raise ValueError(f'There is no account with the given id ({account_id})')

    password, salt, nonce, tag = result

    try:
        key = derive_256_bit_salt_and_key(password=master_password, salt=salt)[1]
    except HashingError as e:
        raise HashingError(f'An error occurred while generating the key: {e}')

    try:
        plaintext = decrypt_aes_256_gcm(key=key, ciphertext=password, nonce=nonce, tag=tag)
    except ValueError as e:
        raise ValueError(f'An error occurred while decrypting the password: {e}')

    cursor.close()

    return plaintext


def get_all_decrypted_account_passwords_by_user_id(user_id: int, master_password: str, connection: Connection)\
        -> Optional[Dict[int, str]]:
    """
    Returns a dictionary keyed by Account id with the decrypted Account passwords for all Accounts of the User with the
    given user id. If the User does not have any Accounts, returns None.
    :param user_id: the id of the User to get the decrypted Account passwords for
    :param master_password: the user's master password
    :param connection: the database connection to use
    :return: a dictionary keyed by Account id with the corresponding decrypted Account passwords if the User has
    Accounts, else None
    :raise argon2.exceptions.HashingError: if an error occurs during hashing
    :raise ValueError: if there is no User with the given id or if a cryptography error occurs
    """
    cursor = connection.cursor()

    cursor.execute("SELECT EXISTS (SELECT 1 FROM users WHERE id=?)", (user_id,))

    user_exists = cursor.fetchone()[0]

    if not user_exists:
        raise ValueError(f'There is no User with the given user_id ({user_id})')

    cursor.execute("SELECT id, password, salt, nonce, tag FROM accounts WHERE user_id=?", (user_id,))

    result = cursor.fetchall()

    if not result:
        return None

    decrypted_account_passwords = {}

    for account_info in result:
        account_id, password, salt, nonce, tag = account_info

        try:
            key = derive_256_bit_salt_and_key(password=master_password, salt=salt)[1]
        except HashingError as e:
            raise HashingError(f'An error occurred while generating the key: {e}')

        try:
            plaintext = decrypt_aes_256_gcm(key=key, ciphertext=password, nonce=nonce, tag=tag)
        except ValueError as e:
            raise ValueError(f'An error occurred while decrypting the password: {e}')

        decrypted_account_passwords[account_id] = plaintext

    cursor.close()

    return decrypted_account_passwords


def is_valid_login(email: str, entered_password: str, connection: Connection) -> bool:
    """
    When a user attempts to sign in, verifies their account info. Returns True if there is a User with a matching
    email and password (using verification of the hash for the password). Additionally, rehashes their password
    if the argon2 default configuration changes and re-encrypts their Account passwords.
    Returns False otherwise or raises a ValueError if there was a miscellaneous verification error.
    :param email: the given email when a user signs in
    :param entered_password: the given password when a user signs in (plaintext)
    :param connection: the database connection to use
    :return: True if there is an existing User with the corresponding email and password, False otherwise
    :raise argon2.exceptions.VerificationError: if there was a miscellaneous verification error (if the argon
    verification raised VerificationError as opposed to VerifyMismatchError or InvalidHashError)
    """
    ph = PasswordHasher()
    user_id = get_user_id_by_email(email=email, connection=connection)
    hashed_password = get_login_password_by_user_id(user_id=user_id, connection=connection)

    if not hashed_password:
        return False

    try:
        is_valid = ph.verify(hash=hashed_password, password=entered_password)

    except (VerifyMismatchError, InvalidHashError):
        return False

    except VerificationError as e:
        raise VerificationError(f'The login could not be verified for miscellaneous reasons: {e}')

    if ph.check_needs_rehash(hashed_password):
        rehash_and_reencrypt_passwords(user_id=user_id, entered_password=entered_password, connection=connection)

    return is_valid


def rehash_and_reencrypt_passwords(user_id: int, entered_password: str, connection: Connection) -> None:
    """
    For the User with the given id:
    1. Decrypts all their Account passwords using their original User hashed password
    2. Rehashes their given User password (plaintext)
    3. Replaces their previous password field in the User table with the new hashed password
    4. Encrypts all their decrypted Account passwords using new keys
    5. Replaces the Account passwords in the database with the newly encrypted passwords (other cryptographic info
    is also updated)
    :return: None
    :raise argon2.exceptions.HashingError: if an error occurs during hashing
    :raise ValueError: if an error occurs during encryption or decryption of the Account passwords
    """
    cursor = connection.cursor()

    # Hashing steps
    ph = PasswordHasher()

    hashed_password = ph.hash(entered_password)

    cursor.execute("UPDATE users SET password=:password WHERE id=:user_id", ({'password': hashed_password,
                                                                              'user_id': user_id}))

    # Encryption steps
    plaintext_account_passwords = get_all_decrypted_account_passwords_by_user_id(user_id=user_id,
                                                                                 master_password=entered_password,
                                                                                 connection=connection)

    # Return early if the User has no Accounts
    if not plaintext_account_passwords:
        return

    ciphertext_account_passwords = []

    for account_id, account_password in plaintext_account_passwords.items():
        salt, key = derive_256_bit_salt_and_key(entered_password)
        ciphertext, nonce, tag = encrypt_aes_256_gcm(key=key, plaintext=account_password)

        ciphertext_account_password_dict = {'password': ciphertext, 'salt': salt, 'nonce': nonce, 'tag': tag,
                                            'account_id': account_id}

        ciphertext_account_passwords.append(ciphertext_account_password_dict)

    update_query = "UPDATE accounts SET password=:password, salt=:salt, nonce=:nonce, tag=:tag WHERE id=:account_id"
    cursor.executemany(update_query, ciphertext_account_passwords)

    connection.commit()
    cursor.close()


# Utils for testing:
def db_setup() -> Tuple[Connection, Cursor]:
    """
    Creates an in-memory database with the necessary tables, used for testing, and returns the corresponding
    Connection and Cursor.
    :return: (connection, cursor), where connection and cursor relate to the created in-memory database
    """
    connection = connect(":memory:")
    cursor = connection.cursor()
    cursor.execute("PRAGMA foreign_keys = ON;")

    cursor.execute("""CREATE TABLE users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL
                    ) STRICT ;""")

    cursor.execute("""CREATE TABLE accounts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL COLLATE NOCASE,
                    url TEXT COLLATE NOCASE,
                    username TEXT NOT NULL,
                    password BLOB NOT NULL,
                    salt BLOB NOT NULL,
                    nonce BLOB NOT NULL,
                    tag BLOB NOT NULL,
                    user_id INTEGER NOT NULL,
                    FOREIGN KEY(user_id) REFERENCES users(id),
                    UNIQUE(name, user_id)
                    ) STRICT ;""")

    connection.commit()

    return connection, cursor
