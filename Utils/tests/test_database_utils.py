import sqlite3
import unittest
from typing import Tuple

import argon2.exceptions
from argon2 import PasswordHasher

from Utils.cryptography import derive_256_bit_salt_and_key, encrypt_aes_256_gcm
from Utils.database import get_login_password_by_user_id, get_account_id_by_account_name_and_user_id, db_setup, \
    get_decrypted_account_password, get_all_account_names_urls_and_usernames_by_user_id, get_user_id_by_email, \
    is_valid_login, \
    get_all_decrypted_account_passwords_by_user_id, rehash_and_reencrypt_passwords, create_user, create_account, \
    get_account_name_url_and_username_by_account_id, edit_account


class DatabaseUtilsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.connection, self.cursor = db_setup()

        self.cursor.execute("INSERT INTO users VALUES (:id, :email, :password)", {'id': None,
                                                                                  'email': 'testemail@gmail.com',
                                                                                  'password': '123abc'})

        self.cursor.execute("INSERT INTO users VALUES (:id, :email, :password)", {'id': None,
                                                                                  'email': 'testemail2@gmail.com',
                                                                                  'password': '456def'})

    def tearDown(self) -> None:
        self.cursor.close()
        self.connection.close()

    def test_create_user_successful(self):
        """
        Creates a User with the given inputs, their id is returned, and that User can then be queried for.
        """
        ph = PasswordHasher()
        email = 'newemail@gmail.com'
        password = 'ShortPassword'

        user_id = create_user(email=email, password=password, connection=self.connection)

        self.cursor.execute("SELECT * FROM users WHERE id=?", (user_id, ))

        queried_user_email, queried_hashed_password = self.cursor.fetchone()[1:3]

        self.assertEquals(email, queried_user_email)
        self.assertTrue(ph.verify(hash=queried_hashed_password, password=password))

    def test_create_user_invalid_email(self):
        """
        Raises ValueError when the given email is invalid
        """
        emails = ['not-email@com', '@gmail.com',  'not-email@.com', 'not-email.com', '@.', 'not-email', 'not-email.']
        password = 'ShortPassword'

        for email in emails:
            try:
                create_user(email=email, password=password, connection=self.connection)
            except ValueError as e:
                self.assertEquals(f'The given email ({email}) is invalid', str(e))
            else:
                self.fail('ValueError should have been raised for invalid email')

    def test_create_user_empty_email(self):
        """
        Raises ValueError when the given email is an empty string
        """
        email = ''
        password = 'ShortPassword'

        try:
            create_user(email=email, password=password, connection=self.connection)
        except ValueError as e:
            self.assertEquals('The given email was an empty string', str(e))
        else:
            self.fail('ValueError should have been raised for empty email')

    def test_create_user_empty_password(self):
        """
        Raises ValueError when the given email is an empty string
        """
        email = 'first-last@gmail.com'
        password = ''

        try:
            create_user(email=email, password=password, connection=self.connection)
        except ValueError as e:
            self.assertEquals('The given password was an empty string', str(e))
        else:
            self.fail('ValueError should have been raised for empty password')

    def test_create_account_successful(self):
        """
        Creates an Account with the given inputs, the Account id is returned, and that Account can then be queried for.
        """
        master_password = 'MasterPassword'
        name = 'Google'
        url = 'https://www.example.com'
        username = 'username@gmail.com'
        password = 'TheAccountPassword'

        user_id = create_user(email='new-email@gmail.com', password=master_password, connection=self.connection)

        account_id = create_account(user_id=user_id, master_password=master_password, name=name, url=url,
                                    username=username, password=password, connection=self.connection)

        self.cursor.execute("SELECT * FROM accounts WHERE id=?", (account_id, ))

        (queried_name, queried_url, queried_username, queried_encrypted_password, queried_salt, queried_nonce,
         queried_tag, queried_user_id) = self.cursor.fetchone()[1:]

        self.assertEquals(name, queried_name)
        self.assertEquals(url, queried_url)
        self.assertEquals(username, queried_username)
        self.assertEquals(password, get_decrypted_account_password(account_id, master_password, self.connection))
        self.assertEquals(user_id, queried_user_id)

    def test_create_account_non_existent_user_id(self):
        """
        Fails to create an Account due to receiving a non-existent user id.
        """
        master_password = 'MasterPassword'
        name = 'Google'
        username = 'username@gmail.com'
        password = 'TheAccountPassword'

        try:
            create_account(user_id=4500, master_password=master_password, name=name, url=None, username=username,
                           password=password, connection=self.connection)
        except ValueError as e:
            self.assertEquals('There is no User with the given user_id (4500)', str(e))
        else:
            self.fail('Should have failed due to receiving a non-existent user_id')

    def test_create_account_empty_name(self):
        """
        Fails to create an Account due to receiving an empty string for the given name.
        """
        master_password = 'MasterPassword'
        name = ''
        username = 'username@gmail.com'
        password = 'TheAccountPassword'

        user_id = create_user(email='new-email@gmail.com', password=master_password, connection=self.connection)

        try:
            create_account(user_id=user_id, master_password=master_password, name=name, url=None, username=username,
                           password=password, connection=self.connection)
        except ValueError as e:
            self.assertEquals('The given name was an empty string', str(e))
        else:
            self.fail('Should have failed due to receiving an empty string for the given name')

    def test_create_account_empty_username(self):
        """
        Fails to create an Account due to receiving an empty string for the given name.
        """
        master_password = 'MasterPassword'
        name = 'Google'
        username = ''
        password = 'TheAccountPassword'

        user_id = create_user(email='new-email@gmail.com', password=master_password, connection=self.connection)

        try:
            create_account(user_id=user_id, master_password=master_password, name=name, url=None, username=username,
                           password=password, connection=self.connection)
        except ValueError as e:
            self.assertEquals('The given username was an empty string', str(e))
        else:
            self.fail('Should have failed due to receiving an empty string for the given username')

    def test_create_account_empty_password(self):
        """
        Fails to create an Account due to receiving an empty string for the given Account password.
        """
        master_password = 'MasterPassword'
        name = 'Google'
        username = 'new-email@gmail.com'
        password = ''

        user_id = create_user(email='new-email@gmail.com', password=master_password, connection=self.connection)

        try:
            create_account(user_id=user_id, master_password=master_password, name=name, url=None, username=username,
                           password=password, connection=self.connection)
        except ValueError as e:
            self.assertEquals('The given password was an empty string', str(e))
        else:
            self.fail('Should have failed due to receiving an empty string for the given password')

    def test_create_account_empty_master_password(self):
        """
        Fails to create an Account due to receiving an empty string for the given master_password.
        """
        master_password = ''
        name = 'Google'
        username = 'new-email@gmail.com'
        password = 'TheAccountPassword'

        user_id = create_user(email='new-email@gmail.com', password='Master Password', connection=self.connection)

        try:
            create_account(user_id=user_id, master_password=master_password, name=name, url=None, username=username,
                           password=password, connection=self.connection)
        except ValueError as e:
            self.assertEquals('The given master_password was an empty string', str(e))
        else:
            self.fail('Should have failed due to receiving an empty string for the given master_password')

    def edit_account_setup(self) -> Tuple[str, int, int, str, str, str, str]:
        """
        Creates an Account to use in the edit account testing. Returns the master_password, the Account's id, the
        corresponding user_id, the name, the url, the username, and the password used to make the Account.
        Creates an additional account for the user with the name 'NAME' for unique name testing purposes.
        """
        master_password = 'MasterPassword'
        name = 'Google'
        url = 'https://www.example.com'
        username = 'username@gmail.com'
        password = 'TheAccountPassword'

        user_id = create_user(email='new-email@gmail.com', password=master_password, connection=self.connection)

        account_id = create_account(user_id=user_id, master_password=master_password, name=name, url=url,
                                    username=username, password=password, connection=self.connection)

        create_account(user_id=user_id, master_password=master_password, name='NAME', url=url,
                       username=username, password=password, connection=self.connection)

        return master_password, account_id, user_id, name, url, username, password

    def test_edit_account_successful(self):
        """
        When all fields are passed, all Account info changes.
        """
        name = 'New Name'
        url = 'https://www.example.net'
        username = 'new-username@gmail.com'
        password = 'NewAccountPassword'
        master_password, account_id, user_id = self.edit_account_setup()[0:3]

        edit_account(account_id=account_id, master_password=master_password, name=name, url=url, username=username,
                     password=password, connection=self.connection)

        self.cursor.execute("SELECT * FROM accounts WHERE id=?", (account_id, ))

        (new_queried_name, new_queried_url, new_queried_username, new_queried_encrypted_password, new_queried_salt,
         new_queried_nonce, new_queried_tag, new_queried_user_id) = self.cursor.fetchone()[1:]

        self.assertEquals(name, new_queried_name)
        self.assertEquals(url, new_queried_url)
        self.assertEquals(username, new_queried_username)
        self.assertEquals(password, get_decrypted_account_password(account_id, master_password, self.connection))
        self.assertEquals(user_id, new_queried_user_id)

    def test_edit_account_name_successful(self):
        """
        When name field is passed, name changes.
        """
        name = 'New Name'
        master_password, account_id, user_id, old_name, old_url, old_username, old_password = self.edit_account_setup()

        edit_account(account_id=account_id, name=name, connection=self.connection)

        self.cursor.execute("SELECT * FROM accounts WHERE id=?", (account_id, ))

        (new_queried_name, new_queried_url, new_queried_username, new_queried_encrypted_password, new_queried_salt,
         new_queried_nonce, new_queried_tag, new_queried_user_id) = self.cursor.fetchone()[1:]

        self.assertEquals(name, new_queried_name)
        self.assertEquals(old_url, new_queried_url)
        self.assertEquals(old_username, new_queried_username)
        self.assertEquals(old_password, get_decrypted_account_password(account_id, master_password, self.connection))
        self.assertEquals(user_id, new_queried_user_id)

    def test_edit_account_url_successful(self):
        """
        When url field is passed, url changes.
        """
        url = 'https://www.example.com'
        master_password, account_id, user_id, old_name, old_url, old_username, old_password = self.edit_account_setup()

        edit_account(account_id=account_id, url=url, connection=self.connection)

        self.cursor.execute("SELECT * FROM accounts WHERE id=?", (account_id, ))

        (new_queried_name, new_queried_url, new_queried_username, new_queried_encrypted_password, new_queried_salt,
         new_queried_nonce, new_queried_tag, new_queried_user_id) = self.cursor.fetchone()[1:]

        self.assertEquals(old_name, new_queried_name)
        self.assertEquals(url, new_queried_url)
        self.assertEquals(old_username, new_queried_username)
        self.assertEquals(old_password, get_decrypted_account_password(account_id, master_password, self.connection))
        self.assertEquals(user_id, new_queried_user_id)

    def test_edit_account_username_successful(self):
        """
        When username field is passed, username changes.
        """
        username = 'New Username'
        master_password, account_id, user_id, old_name, old_url, old_username, old_password = self.edit_account_setup()

        edit_account(account_id=account_id, username=username, connection=self.connection)

        self.cursor.execute("SELECT * FROM accounts WHERE id=?", (account_id, ))

        (new_queried_name, new_queried_url, new_queried_username, new_queried_encrypted_password, new_queried_salt,
         new_queried_nonce, new_queried_tag, new_queried_user_id) = self.cursor.fetchone()[1:]

        self.assertEquals(old_name, new_queried_name)
        self.assertEquals(old_url, new_queried_url)
        self.assertEquals(username, new_queried_username)
        self.assertEquals(old_password, get_decrypted_account_password(account_id, master_password, self.connection))
        self.assertEquals(user_id, new_queried_user_id)

    def test_edit_account_password_successful(self):
        """
        When password and master_password field is passed, password changes.
        """
        password = 'NewAccountPassword'
        master_password, account_id, user_id, old_name, old_url, old_username, old_password = self.edit_account_setup()

        edit_account(account_id=account_id, password=password, master_password=master_password,
                     connection=self.connection)

        self.cursor.execute("SELECT * FROM accounts WHERE id=?", (account_id, ))

        (new_queried_name, new_queried_url, new_queried_username, new_queried_encrypted_password, new_queried_salt,
         new_queried_nonce, new_queried_tag, new_queried_user_id) = self.cursor.fetchone()[1:]

        self.assertEquals(old_name, new_queried_name)
        self.assertEquals(old_url, new_queried_url)
        self.assertEquals(old_username, new_queried_username)
        self.assertEquals(password, get_decrypted_account_password(account_id, master_password, self.connection))
        self.assertEquals(user_id, new_queried_user_id)

    def test_edit_account_password_no_master_password(self):
        """
        When password field is passed, but not the master_password field, raises a ValueError.
        """
        password = 'NewAccountPassword'
        master_password, account_id, user_id, old_name, old_url, old_username, old_password = self.edit_account_setup()

        try:
            edit_account(account_id=account_id, password=password, connection=self.connection)
        except ValueError as e:
            self.assertEquals('The given master_password was an empty string or was not provided', str(e))
        else:
            self.fail('ValueError was not raised for missing master_password')

        self.cursor.execute("SELECT * FROM accounts WHERE id=?", (account_id, ))

        (new_queried_name, new_queried_url, new_queried_username, new_queried_encrypted_password, new_queried_salt,
         new_queried_nonce, new_queried_tag, new_queried_user_id) = self.cursor.fetchone()[1:]

        self.assertEquals(old_name, new_queried_name)
        self.assertEquals(old_url, new_queried_url)
        self.assertEquals(old_username, new_queried_username)
        self.assertEquals(old_password, get_decrypted_account_password(account_id, master_password, self.connection))
        self.assertEquals(user_id, new_queried_user_id)

    def test_edit_account_password_empty_master_password(self):
        """
        When password field is passed, but the master_password field is an empty string, raises a ValueError.
        """
        password = 'NewAccountPassword'
        master_password, account_id, user_id, old_name, old_url, old_username, old_password = self.edit_account_setup()

        try:
            edit_account(account_id=account_id, password=password, master_password='', connection=self.connection)
        except ValueError as e:
            self.assertEquals('The given master_password was an empty string or was not provided', str(e))
        else:
            self.fail('ValueError was not raised for empty string master_password')

        self.cursor.execute("SELECT * FROM accounts WHERE id=?", (account_id, ))

        (new_queried_name, new_queried_url, new_queried_username, new_queried_encrypted_password, new_queried_salt,
         new_queried_nonce, new_queried_tag, new_queried_user_id) = self.cursor.fetchone()[1:]

        self.assertEquals(old_name, new_queried_name)
        self.assertEquals(old_url, new_queried_url)
        self.assertEquals(old_username, new_queried_username)
        self.assertEquals(old_password, get_decrypted_account_password(account_id, master_password, self.connection))
        self.assertEquals(user_id, new_queried_user_id)

    def test_edit_account_password_incorrect_master_password(self):
        """
        When password field is passed, but the master_password field is incorrect, raises an
        argon2.exceptions.VerifyMismatchError.
        """
        password = 'NewAccountPassword'
        master_password, account_id, user_id, old_name, old_url, old_username, old_password = self.edit_account_setup()

        try:
            edit_account(account_id=account_id, password=password, master_password='Wrong', connection=self.connection)
        except argon2.exceptions.VerifyMismatchError as e:
            self.assertEquals('The password does not match the supplied hash', str(e))
        else:
            self.fail('argon2.exceptions.VerifyMismatchError was not raised for incorrect master_password')

        self.cursor.execute("SELECT * FROM accounts WHERE id=?", (account_id, ))

        (new_queried_name, new_queried_url, new_queried_username, new_queried_encrypted_password, new_queried_salt,
         new_queried_nonce, new_queried_tag, new_queried_user_id) = self.cursor.fetchone()[1:]

        self.assertEquals(old_name, new_queried_name)
        self.assertEquals(old_url, new_queried_url)
        self.assertEquals(old_username, new_queried_username)
        self.assertEquals(old_password, get_decrypted_account_password(account_id, master_password, self.connection))
        self.assertEquals(user_id, new_queried_user_id)

    def test_edit_account_name_not_unique(self):
        """
        When name field is passed, but the name field is not unique, raises a Sqlite3.IntegrityError.
        """
        name = 'NAME'
        master_password, account_id, user_id, old_name, old_url, old_username, old_password = self.edit_account_setup()

        try:
            edit_account(account_id=account_id, name=name, connection=self.connection)
        except sqlite3.IntegrityError as e:
            self.assertEquals('The name could not be updated because this Account name is already '
                              'being used: UNIQUE constraint failed: accounts.name, accounts.user_id', str(e))
        else:
            self.fail('Sqlite3.IntegrityError was not raised for non-unique account name')

        self.cursor.execute("SELECT * FROM accounts WHERE id=?", (account_id, ))

        (new_queried_name, new_queried_url, new_queried_username, new_queried_encrypted_password, new_queried_salt,
         new_queried_nonce, new_queried_tag, new_queried_user_id) = self.cursor.fetchone()[1:]

        self.assertEquals(old_name, new_queried_name)
        self.assertEquals(old_url, new_queried_url)
        self.assertEquals(old_username, new_queried_username)
        self.assertEquals(old_password, get_decrypted_account_password(account_id, master_password, self.connection))
        self.assertEquals(user_id, new_queried_user_id)



    def test_get_user_id_by_email_successful(self):
        """
        When a User with the given email exists, the corresponding user_id is returned.
        """
        user_id_1 = get_user_id_by_email(email="testemail@gmail.com", connection=self.connection)
        user_id_2 = get_user_id_by_email(email="testemail2@gmail.com", connection=self.connection)

        self.assertEquals(1, user_id_1)
        self.assertEquals(2, user_id_2)

    def test_get_user_id_by_email_non_existent(self):
        """
        When a User with the given email does not exist, None is returned.
        """
        user_id = get_user_id_by_email(email="fakeemail@gmail.com", connection=self.connection)

        self.assertIsNone(user_id)

    def test_get_login_password_by_user_id_successful(self):
        """
        When a User with the given id exists, the corresponding password is returned.
        """
        password_1 = get_login_password_by_user_id(user_id=1, connection=self.connection)
        password_2 = get_login_password_by_user_id(user_id=2, connection=self.connection)

        self.assertEquals('123abc', password_1)
        self.assertEquals('456def', password_2)

    def test_get_login_password_by_user_id_non_existent(self):
        """
        When a User with the given id does not exist, None is returned.
        """
        password = get_login_password_by_user_id(user_id=45, connection=self.connection)

        self.assertIsNone(password)

    def test_get_account_id_by_account_name_and_user_id_successful(self):
        """
        When an Account with the given name and foreign key user_id exists, the corresponding account id is returned.
        """
        self.cursor.execute("INSERT INTO accounts VALUES (:id, :name, :url, :username, :password, :salt, :nonce, :tag, :user_id)",
                       {'id': None,
                        'name': 'Company 1',
                        'url': 'https://www.example.com',
                        'username': 'testemail@gmail.com',
                        'password': b'password',
                        'salt': b'salt',
                        'nonce': b'nonce',
                        'tag': b'tag',
                        'user_id': 1})

        self.cursor.execute("INSERT INTO accounts VALUES (:id, :name, :url, :username, :password, :salt, :nonce, :tag, :user_id)",
                       {'id': None,
                        'name': 'Company 2',
                        'url': None,
                        'username': 'testemail@gmail.com',
                        'password': b'password',
                        'salt': b'salt',
                        'nonce': b'nonce',
                        'tag': b'tag',
                        'user_id': 1})

        self.cursor.execute("INSERT INTO accounts VALUES (:id, :name, :url, :username, :password, :salt, :nonce, :tag, :user_id)",
                       {'id': None,
                        'name': 'Company 1',
                        'url': None,
                        'username': 'otheremail@gmail.com',
                        'password': b'password',
                        'salt': b'salt',
                        'nonce': b'nonce',
                        'tag': b'tag',
                        'user_id': 2})

        account_id_1 = get_account_id_by_account_name_and_user_id(account_name='Company 1', user_id=1, connection=self.connection)
        account_id_2 = get_account_id_by_account_name_and_user_id(account_name='Company 2', user_id=1, connection=self.connection)
        account_id_3 = get_account_id_by_account_name_and_user_id(account_name='Company 1', user_id=2, connection=self.connection)

        self.assertEquals(1, account_id_1)
        self.assertEquals(2, account_id_2)
        self.assertEquals(3, account_id_3)

    def test_get_account_id_by_account_name_and_user_id_non_existent(self):
        """
        When an Account with the given name and foreign key user_id does not exist, None is returned.
        """
        self.cursor.execute("INSERT INTO accounts VALUES (:id, :name, :url, :username, :password, :salt, :nonce, :tag, :user_id)",
                       {'id': None,
                        'name': 'Company 1',
                        'url': None,
                        'username': 'testemail@gmail.com',
                        'password': b'password',
                        'salt': b'salt',
                        'nonce': b'nonce',
                        'tag': b'tag',
                        'user_id': 1})

        account_id = get_account_id_by_account_name_and_user_id(account_name='Company 1', user_id=2, connection=self.connection)

        self.assertIsNone(account_id)

    def test_get_account_name_url_and_username_by_account_id_successful(self):
        """
        When an Account with the given id exists, returns the name, url, and username.
        """
        self.cursor.execute("INSERT INTO accounts VALUES (:id, :name, :url, :username, :password, :salt, :nonce, :tag, :user_id)",
                       {'id': None,
                        'name': 'Company 1',
                        'url': 'https://www.example.com',
                        'username': 'testemail@gmail.com',
                        'password': b'password',
                        'salt': b'salt',
                        'nonce': b'nonce',
                        'tag': b'tag',
                        'user_id': 1})

        self.cursor.execute("INSERT INTO accounts VALUES (:id, :name, :url, :username, :password, :salt, :nonce, :tag, :user_id)",
                       {'id': None,
                        'name': 'Company 2',
                        'url': None,
                        'username': 'otheremail@gmail.com',
                        'password': b'password',
                        'salt': b'salt',
                        'nonce': b'nonce',
                        'tag': b'tag',
                        'user_id': 2})

        account_name_url_and_username = get_account_name_url_and_username_by_account_id(account_id=1, connection=self.connection)
        account_name_url_and_username_2 = get_account_name_url_and_username_by_account_id(account_id=2, connection=self.connection)

        self.assertEquals(('Company 1', 'https://www.example.com', 'testemail@gmail.com'), account_name_url_and_username)
        self.assertEquals(('Company 2', None, 'otheremail@gmail.com'), account_name_url_and_username_2)

    def test_get_account_name_url_and_username_by_account_id_non_existent(self):
        """
        When there is no existing Account with the given id, returns None.
        """
        account_name_and_username = get_account_name_url_and_username_by_account_id(account_id=1, connection=self.connection)

        self.assertIsNone(account_name_and_username)


    def test_get_all_account_names_urls_and_usernames_by_user_successful(self):
        """
        When a User has associated Accounts, the name, url, and username of each are returned.
        """
        self.cursor.execute("INSERT INTO accounts VALUES (:id, :name, :url, :username, :password, :salt, :nonce, :tag, :user_id)",
                       {'id': None,
                        'name': 'Company 1',
                        'url': 'https://www.example.com',
                        'username': 'testemail@gmail.com',
                        'password': b'password',
                        'salt': b'salt',
                        'nonce': b'nonce',
                        'tag': b'tag',
                        'user_id': 1})

        self.cursor.execute("INSERT INTO accounts VALUES (:id, :name, :url, :username, :password, :salt, :nonce, :tag, :user_id)",
                       {'id': None,
                        'name': 'Company 2',
                        'url': None,
                        'username': 'testemail@gmail.com',
                        'password': b'password',
                        'salt': b'salt',
                        'nonce': b'nonce',
                        'tag': b'tag',
                        'user_id': 1})

        self.cursor.execute("INSERT INTO accounts VALUES (:id, :name, :url, :username, :password, :salt, :nonce, :tag, :user_id)",
                       {'id': None,
                        'name': 'Company 1',
                        'url': None,
                        'username': 'otheremail@gmail.com',
                        'password': b'password',
                        'salt': b'salt',
                        'nonce': b'nonce',
                        'tag': b'tag',
                        'user_id': 2})

        user_1_account_names_urls_and_usernames = get_all_account_names_urls_and_usernames_by_user_id(user_id=1, connection=self.connection)
        user_2_account_names_urls_and_usernames = get_all_account_names_urls_and_usernames_by_user_id(user_id=2, connection=self.connection)

        self.assertEquals([('Company 1', 'https://www.example.com', 'testemail@gmail.com'),
                           ('Company 2', None, 'testemail@gmail.com'), ], user_1_account_names_urls_and_usernames)

        self.assertEquals([('Company 1', None, 'otheremail@gmail.com'), ], user_2_account_names_urls_and_usernames)

    def test_get_all_account_names_urls_and_usernames_by_user_non_existent(self):
        """
        When a User has no associated Accounts, None is returned.
        """
        user_1_account_names_urls_and_usernames = get_all_account_names_urls_and_usernames_by_user_id(user_id=1, connection=self.connection)

        self.assertIsNone(user_1_account_names_urls_and_usernames)

    def get_decrypted_account_password_set_up(self) -> Tuple[str, str, str, int, int, int]:
        """
        Abstracts the setup for the get_decrypted_account_password tests.
        :return: the master and Account passwords, as well as the user_id and account ids, in that order
        """
        ph = PasswordHasher()
        master_password = 'TestPassword'
        account_password = 'AccountPassword'
        account_password_2 = 'SecondAccountPassword'
        user_id = 3

        self.cursor.execute("INSERT INTO users VALUES (:id, :email, :password)", {'id': user_id,
                                                                                  'email': 'coolemail@gmail.com',
                                                                                  'password': ph.hash(master_password)})

        salt, key = derive_256_bit_salt_and_key(master_password)
        ciphertext, nonce, tag = encrypt_aes_256_gcm(key, account_password)

        salt_2, key_2 = derive_256_bit_salt_and_key(master_password)
        ciphertext_2, nonce_2, tag_2 = encrypt_aes_256_gcm(key_2, account_password_2)

        self.cursor.execute(
            "INSERT INTO accounts VALUES (:id, :name, :url, :login, :password, :salt, :nonce, :tag, :user_id)",
            {'id': None,
             'name': 'Company 1',
             'url': None,
             'login': 'testemail@gmail.com',
             'password': ciphertext,
             'salt': salt,
             'nonce': nonce,
             'tag': tag,
             'user_id': user_id})

        self.cursor.execute(
            "INSERT INTO accounts VALUES (:id, :name, :url, :login, :password, :salt, :nonce, :tag, :user_id)",
            {'id': None,
             'name': 'Company 2',
             'url': None,
             'login': 'testemail@gmail.com',
             'password': ciphertext_2,
             'salt': salt_2,
             'nonce': nonce_2,
             'tag': tag_2,
             'user_id': user_id})

        account_id = get_account_id_by_account_name_and_user_id(user_id=user_id, account_name='Company 1', connection=self.connection)
        account_id_2 = get_account_id_by_account_name_and_user_id(user_id=user_id, account_name='Company 2', connection=self.connection)

        return master_password, account_password, account_password_2, user_id, account_id, account_id_2

    def test_get_decrypted_account_password_successful(self):
        """
        When given fully valid inputs, the plaintext Account password is returned.
        """
        master_password, account_password, account_password_2 = self.get_decrypted_account_password_set_up()[0:3]

        plaintext = get_decrypted_account_password(account_id=1, master_password=master_password, connection=self.connection)

        self.assertEquals(account_password, plaintext)

    def test_get_decrypted_account_password_non_existent_account(self):
        """
        When an Account with the given id does not exist, Value Error is raised.
        """
        master_password, account_password, account_password_2 = self.get_decrypted_account_password_set_up()[0:3]

        try:
            get_decrypted_account_password(account_id=44, master_password=master_password, connection=self.connection)
        except ValueError as e:
            self.assertEquals('There is no account with the given id (44)', str(e))
        else:
            self.fail('Value error was not raised when the account was non-existent')

    def test_get_decrypted_account_password_wrong_master_password(self):
        """
        When the given master password is incorrect, Value Error is raised.
        """
        self.get_decrypted_account_password_set_up()

        try:
            get_decrypted_account_password(account_id=1, master_password='wrong_password', connection=self.connection)
        except ValueError as e:
            self.assertEquals('An error occurred while decrypting the password: MAC check failed', str(e))
        else:
            self.fail('Value error was not raised when the wrong master password was given')

    def test_get_all_decrypted_account_passwords_by_user_id_successful(self):
        """
        When given fully valid inputs, the plaintext Account passwords are returned.
        """
        master_password, account_password, account_password_2 = self.get_decrypted_account_password_set_up()[0:3]

        decrypted_account_passwords = get_all_decrypted_account_passwords_by_user_id(user_id=3, master_password=master_password, connection=self.connection)

        self.assertEquals(account_password, decrypted_account_passwords[1])
        self.assertEquals(account_password_2, decrypted_account_passwords[2])

    def test_get_all_decrypted_account_passwords_by_user_id_non_existent_user(self):
        """
        When a User with the given id does not exist, Value Error is raised.
        """
        master_password, account_password, account_password_2 = self.get_decrypted_account_password_set_up()[0:3]

        try:
            get_all_decrypted_account_passwords_by_user_id(user_id=814, master_password=master_password, connection=self.connection)
        except ValueError as e:
            self.assertEquals('There is no User with the given user_id (814)', str(e))
        else:
            self.fail('Value error was not raised when the User was non-existent')

    def test_get_all_decrypted_account_passwords_by_user_id_no_associated_accounts(self):
        """
        When the User has no associated Accounts, None is returned.
        """
        master_password, account_password, account_password_2 = self.get_decrypted_account_password_set_up()[0:3]

        decrypted_account_passwords = get_all_decrypted_account_passwords_by_user_id(user_id=1, master_password=master_password, connection=self.connection)

        self.assertIsNone(decrypted_account_passwords)



    def test_get_all_decrypted_account_passwords_by_user_id_wrong_master_password(self):
        """
        When the given master password is incorrect, Value Error is raised.
        """
        self.get_decrypted_account_password_set_up()

        try:
            get_all_decrypted_account_passwords_by_user_id(user_id=3, master_password='wrong_password', connection=self.connection)
        except ValueError as e:
            self.assertEquals('An error occurred while decrypting the password: MAC check failed', str(e))
        else:
            self.fail('Value error was not raised when the wrong master password was given')

    def is_valid_login_setup(self):
        """
        Abstracts the setup for the is_valid_login tests that need to test against an actual argon-hashed password.
        """
        # Create test password
        ph = PasswordHasher()
        hashed_password = ph.hash('TestPassword')

        # Create test user
        self.cursor.execute("INSERT INTO users VALUES (:id, :email, :password)", {'id': None,
                                                                             'email': 'superemail@gmail.com',
                                                                             'password': hashed_password})

    def test_is_valid_login_successful(self):
        """
        is_valid_login returns True when the given login is already associated with a User in the database.
        """
        self.is_valid_login_setup()

        self.assertTrue(is_valid_login(email='superemail@gmail.com', entered_password='TestPassword', connection=self.connection))

    def test_is_valid_login_invalid_email(self):
        """
        is_valid_login returns False when the given login is not associated with any User email in the database.
        """
        self.is_valid_login_setup()

        self.assertFalse(is_valid_login(email='wrongemail@gmail.com', entered_password='TestPassword', connection=self.connection))

    def test_is_valid_login_invalid_password(self):
        """
        is_valid_login returns False when the given password does not match the email/login of the corresponding User.
        """
        self.is_valid_login_setup()

        self.assertFalse(is_valid_login(email='superemail@gmail.com', entered_password='WrongPassword', connection=self.connection))

    def test_is_valid_login_invalid_hash(self):
        """
        is_valid_login returns False when the hashed password for the User with the given email is not an argon hash.
        """
        self.assertFalse(is_valid_login(email='testemail@gmail.com', entered_password='123abc', connection=self.connection))

    def get_account_password_and_related_info(self, account_id: int) -> Tuple[bytes, bytes, bytes, bytes]:
        """
        Helper method to abstract a query needed for the rehash_and_reencrypt test below. Returns, in order,
        the ciphertext, salt, nonce, and tag from an Account with the given id if they exist.
        """
        self.cursor.execute("SELECT password, salt, nonce, tag FROM accounts WHERE id=?", (account_id,))
        ciphertext, salt, nonce, tag = self.cursor.fetchone()
        return ciphertext, salt, nonce, tag

    def test_rehash_and_reencrypt_passwords_successful(self):
        """
        Rehashes the User's hashed password and re-encrypts their Account passwords.
        """
        master_password, account_password, account_password_2, user_id, account_id, account_id_2 = self.get_decrypted_account_password_set_up()

        # Pre-mutation:
        previous_hashed_password = get_login_password_by_user_id(user_id=user_id, connection=self.connection)

        previous_ciphertext, previous_salt, previous_nonce, previous_tag = self.get_account_password_and_related_info(account_id)

        previous_ciphertext_2, previous_salt_2, previous_nonce_2, previous_tag_2 = self.get_account_password_and_related_info(account_id_2)

        # Mutation:
        rehash_and_reencrypt_passwords(user_id=user_id, entered_password=master_password, connection=self.connection)

        # Post-mutation:
        new_hashed_password = get_login_password_by_user_id(user_id=user_id, connection=self.connection)

        new_ciphertext, new_salt, new_nonce, new_tag = self.get_account_password_and_related_info(account_id)

        new_ciphertext_2, new_salt_2, new_nonce_2, new_tag_2 = self.get_account_password_and_related_info(account_id_2)

        # Hashes are different for the old and new hash
        self.assertNotEquals(previous_hashed_password, new_hashed_password)

        # Encrypted passwords and associated info are different for the Account passwords
        self.assertNotEquals(previous_ciphertext, new_ciphertext)
        self.assertNotEquals(previous_ciphertext_2, new_ciphertext_2)
        self.assertNotEquals(previous_salt, new_salt)
        self.assertNotEquals(previous_salt_2, new_salt_2)
        self.assertNotEquals(previous_nonce, new_nonce)
        self.assertNotEquals(previous_nonce_2, new_nonce_2)
        self.assertNotEquals(previous_tag, new_tag)
        self.assertNotEquals(previous_tag_2, new_tag_2)

        # Decrypt to the same original passwords
        self.assertEquals(account_password, get_decrypted_account_password(account_id=account_id, master_password=master_password, connection=self.connection))
        self.assertEquals(account_password_2, get_decrypted_account_password(account_id=account_id_2, master_password=master_password, connection=self.connection))

    def test_rehash_and_reencrypt_passwords_non_existent_user_id(self):
        """
        Raises a ValueError when the User does not exist.
        """
        try:
            rehash_and_reencrypt_passwords(user_id=3400, entered_password='master_password', connection=self.connection)
        except ValueError as e:
            self.assertEquals('There is no User with the given user_id (3400)', str(e))
        else:
            self.fail('A ValueError should have been returned since there is no User with the given id')

    def test_rehash_and_reencrypt_passwords_user_with_no_accounts(self):
        """
        When a User has no Accounts, still rehashes their hashed password.
        """
        # Setup
        ph = PasswordHasher()
        user_id = 3
        self.cursor.execute("INSERT INTO users VALUES (:id, :email, :password)", {'id': user_id,
                                                                                  'email': 'coolemail@gmail.com',
                                                                                  'password': ph.hash('master_password')})

        # Pre-mutation:
        previous_hashed_password = get_login_password_by_user_id(user_id=user_id, connection=self.connection)

        # Mutation:
        rehash_and_reencrypt_passwords(user_id=user_id, entered_password='master_password', connection=self.connection)

        # Post-mutation:
        new_hashed_password = get_login_password_by_user_id(user_id=user_id, connection=self.connection)

        # Hashes are different for the old and new hash
        self.assertNotEquals(previous_hashed_password, new_hashed_password)




