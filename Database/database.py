import os
import sqlite3

from argon2 import PasswordHasher

from Database.db_constants import DBConstants
from Utils.cryptography import encrypt_aes_256_cbc, derive_256_bit_key

# This is a file to mess around with setting up an example database and querying it to simulate the structure
# of the final product

# Database structure:
# Users - id, email (unique), password (should already be hashed when stored)
#
# Accounts - id, fk:User, title (unique together with user), login, password (encrypted)

db_file = "personal_password_manager.db"
if os.path.isfile(db_file):
    os.remove(db_file)
else:
    print(f'Error: {db_file} file not found')

connection = sqlite3.connect(DBConstants.DB_NAME)
# connection.row_factory = sqlite3.Row

cursor = connection.cursor()

cursor.execute("""CREATE TABLE users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE,
                password TEXT
                ) STRICT ;""")

cursor.execute("""CREATE TABLE accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                login TEXT,
                password BLOB,
                user_id INTEGER,
                FOREIGN KEY(user_id) REFERENCES users(id),
                UNIQUE(title, user_id)
                ) STRICT ;""")


# Create test passwords
ph = PasswordHasher()
hashed_password = ph.hash('TestPassword')
key = derive_256_bit_key('TestPassword')
encrypted_password, encrypted_password_iv = encrypt_aes_256_cbc(key, 'AccountPassword')

# Create test users
cursor.execute("INSERT INTO users VALUES (:id, :email, :password)", {'id': None,
                                                                     'email': 'testemail@gmail.com',
                                                                     'password': hashed_password})

cursor.execute("INSERT INTO users VALUES (:id, :email, :password)", {'id': None,
                                                                     'email': 'secondemail@gmail.com',
                                                                     'password': hashed_password})

# Create test accounts
cursor.execute("INSERT INTO accounts VALUES (:id, :title, :login, :password, :user_id)", {'id': None,
                                                                     'title': 'Company 1',
                                                                     'login': 'testemail@gmail.com', 'password':encrypted_password,
                                                                                          'user_id': 1})

cursor.execute("INSERT INTO accounts VALUES (:id, :title, :login, :password, :user_id)", {'id': None,
                                                                     'title': 'Company 2',
                                                                     'login': 'otheremail@gmail.com', 'password':encrypted_password,
                                                                                          'user_id': 1})

# This should not work since it breaks unique(title, user_id)
try:
    cursor.execute("INSERT INTO accounts VALUES (:id, :title, :login, :password, :user_id)", {'id': None,
                                                                         'title': 'Company 2',
                                                                         'login': 'otheremail@gmail.com', 'password':encrypted_password,
                                                                                              'user_id': 1})
except sqlite3.IntegrityError as e:
    print(f'This insert failed because of the following: {e} - UNIQUE(Company2, user_id 1)')

cursor.execute("INSERT INTO accounts VALUES (:id, :title, :login, :password, :user_id)", {'id': None,
                                                                     'title': 'Company 1',
                                                                     'login': 'otheremail@gmail.com', 'password':encrypted_password,
                                                                                          'user_id': 2})

# This should not work since it breaks unique(title, user_id)
try:
    cursor.execute("INSERT INTO accounts VALUES (:id, :title, :login, :password, :user_id)", {'id': None,
                                                                         'title': 'Company 2',
                                                                         'login': 'otheremail@gmail.com', 'password':encrypted_password,
                                                                                              'user_id': 2})
except sqlite3.IntegrityError as e:
    print(f'This insert failed because of the following: {e}')

connection.commit()

# # Query test info
cursor.execute("SELECT id FROM users WHERE email=:email", {'email': "secondemail@gmail.com"})

user_id = cursor.fetchone()[0]
company = 'Company 1'

cursor.execute("SELECT id FROM accounts WHERE title=:title AND user_id=:user_id", {'title': company, 'user_id': user_id})

account_id = cursor.fetchall()[0][0]

print(f'account_id where the title is {company} and the user_id is {user_id}: {account_id}')

cursor.execute("SELECT * FROM accounts WHERE id=:id", {'id': account_id})
print(f'Account with id {account_id}: {cursor.fetchone()}')

cursor.close()
connection.close()
