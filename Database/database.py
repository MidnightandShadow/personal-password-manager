import os
import sqlite3

from argon2 import PasswordHasher

from config import DB_NAME
from Utils.cryptography import encrypt_aes_256_gcm, derive_256_bit_salt_and_key

# This is a file to mess around with setting up an example database and querying it to simulate the structure
# of the final product

# Database structure:
# Users - id, email (unique), password (should already be hashed when stored)
#
# Accounts - id, fk:User, name (unique together with user), login, password (encrypted), salt, nonce, tag

db_file = DB_NAME
if os.path.isfile(db_file):
    os.remove(db_file)
else:
    print(f'Error: {db_file} file not found')

connection = sqlite3.connect(DB_NAME)
# connection.row_factory = sqlite3.Row

cursor = connection.cursor()
cursor.execute("PRAGMA foreign_keys = ON;")

cursor.execute("""CREATE TABLE users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE,
                password TEXT
                ) STRICT ;""")

cursor.execute("""CREATE TABLE accounts (
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


# Create test passwords
ph = PasswordHasher()
hashed_password = ph.hash('a')
salt, key = derive_256_bit_salt_and_key('a')
encrypted_password, nonce, tag = encrypt_aes_256_gcm(key, 'My word, this is an unordinarily long password, I wonder what it might look like in the table display')
encrypted_password_2, nonce_2, tag_2 = encrypt_aes_256_gcm(key, 'OtherAccountPassword')

# Create test users
cursor.execute("INSERT INTO users VALUES (:id, :email, :password)", {'id': None,
                                                                     'email': 'a',
                                                                     'password': hashed_password})

cursor.execute("INSERT INTO users VALUES (:id, :email, :password)", {'id': None,
                                                                     'email': 'secondemail@gmail.com',
                                                                     'password': hashed_password})

for i in range(1, 41):
    cursor.execute("INSERT INTO accounts VALUES (:id, :name, :login, :password, :salt, :nonce, :tag, :user_id)",
                   {'id': None,
                    'name': f'Company {i}',
                    'login': f'testemail{i}@gmail.com',
                    'password': encrypted_password,
                    'salt': salt,
                    'nonce': nonce,
                    'tag': tag,
                    'user_id': 1})

# Create test accounts
# cursor.execute("INSERT INTO accounts VALUES (:id, :name, :login, :password, :salt, :nonce, :tag, :user_id)",
#                {'id': None,
#                 'name': 'Company 1',
#                 'login': 'testemail@gmail.com',
#                 'password': encrypted_password,
#                 'salt': salt,
#                 'nonce': nonce,
#                 'tag': tag,
#                 'user_id': 1})

# cursor.execute("INSERT INTO accounts VALUES (:id, :name, :login, :password, :salt, :nonce, :tag, :user_id)",
#                {'id': None,
#                 'name': 'Company 2',
#                 'login': 'otheremail@gmail.com',
#                 'password': encrypted_password_2,
#                 'salt': salt,
#                 'nonce': nonce_2,
#                 'tag': tag_2,
#                 'user_id': 1})

# This should not work since it breaks unique(name, user_id)
try:
    cursor.execute("INSERT INTO accounts VALUES (:id, :name, :login, :password, :salt, :nonce, :tag, :user_id)",
                   {'id': None,
                    'name': 'Company 2',
                    'login': 'otheremail@gmail.com',
                    'password': encrypted_password,
                    'salt': salt,
                    'nonce': nonce,
                    'tag': tag,
                    'user_id': 1})
except sqlite3.IntegrityError as e:
    print(f'This insert failed as expected because of the following: {e} - UNIQUE(Company2, user_id 1)')

cursor.execute("INSERT INTO accounts VALUES (:id, :name, :login, :password, :salt, :nonce, :tag, :user_id)",
               {'id': None,
                'name': 'Company 1',
                'login': 'otheremail@gmail.com',
                'password': encrypted_password_2,
                'salt': salt,
                'nonce': nonce_2,
                'tag': tag_2,
                'user_id': 2})


cursor.execute("INSERT INTO accounts VALUES (:id, :name, :login, :password, :salt, :nonce, :tag, :user_id)",
               {'id': None,
                'name': 'Company 2',
                'login': 'otheremail@gmail.com',
                'password': encrypted_password,
                'salt': salt,
                'nonce': nonce,
                'tag': tag,
                'user_id': 2})

connection.commit()

# # Query test info
cursor.execute("SELECT id FROM users WHERE email=:email", {'email': "secondemail@gmail.com"})

user_id = cursor.fetchone()[0]
company = 'Company 1'

cursor.execute("SELECT id FROM accounts WHERE name=:name AND user_id=:user_id", {'name': company, 'user_id': user_id})

account_id = cursor.fetchall()[0][0]

print(f'account_id where the name is {company} and the user_id is {user_id}: {account_id}')

cursor.execute("SELECT * FROM accounts WHERE id=:id", {'id': account_id})
print(f'Account with id {account_id}: {cursor.fetchone()}')

cursor.close()
connection.close()
