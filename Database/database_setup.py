import sqlite3

from config import DB_NAME


# Database structure:
# Users - id, email (unique), password (hashed)
#
# Accounts - id, name (unique together with User), url (optional), username, password (ciphertext),
# salt (of the hash used to derive the encryption key from the plaintext User password), nonce, tag, fk:User (user_id)

def setup_database():
    """
    Connect to the database and setup tables if needed
    """
    connection = sqlite3.connect(DB_NAME)

    cursor = connection.cursor()
    cursor.execute("PRAGMA foreign_keys = ON;")

    cursor.execute("""CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL
                    ) STRICT ;""")

    cursor.execute("""CREATE TABLE IF NOT EXISTS accounts (
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

    cursor.close()
    connection.close()
