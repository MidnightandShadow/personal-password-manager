import sqlite3
from sqlite3 import Connection, Cursor, connect, Row
from typing import Union, Tuple


def get_login_password_by_email(email: str, connection: Connection) -> Union[str, None]:
    """
    Returns the login password for a User by a given email if a User with the email exists, else None.
    :param email: the email to query the Users table with
    :param connection: the database connection to use
    :return: the associated password if the User exists, None if not
    """
    cursor = connection.cursor()

    cursor.execute("SELECT password FROM users WHERE email=?", (email,))

    result = cursor.fetchone()

    password = result[0] if result else None

    return password


# Utils for testing:
def db_setup() -> Tuple[Connection, Cursor]:
    """
    Creates an in-memory database with the necessary tables, used for testing, and returns the corresponding
    Connection and Cursor.
    :return: (connection, cursor), where connection and cursor relate to the created in-memory database
    """
    connection = connect(":memory:")
    connection.row_factory = Row
    cursor = connection.cursor()

    cursor.execute("""CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT UNIQUE,
                    password TEXT
                    );""")

    cursor.execute("""CREATE TABLE IF NOT EXISTS accounts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT,
                    login TEXT,
                    password TEXT,
                    user_id INTEGER,
                    FOREIGN KEY(user_id) REFERENCES users(id)
                    );""")

    connection.commit()

    return connection, cursor
