import unittest
from typing import Tuple

import argon2.exceptions
from argon2 import PasswordHasher

from Utils.cryptography import derive_256_bit_salt_and_key, encrypt_aes_256_gcm
from Utils.database import get_login_password_by_user_id, get_account_id_by_account_name_and_user_id, db_setup, \
    get_decrypted_account_password, get_all_account_names_and_logins_by_user_id, get_user_id_by_email, is_valid_login, \
    get_all_decrypted_account_passwords_by_user_id, rehash_and_reencrypt_passwords


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
        self.cursor.execute("INSERT INTO accounts VALUES (:id, :name, :login, :password, :salt, :nonce, :tag, :user_id)",
                       {'id': None,
                        'name': 'Company 1',
                        'login': 'testemail@gmail.com',
                        'password': b'password',
                        'salt': b'salt',
                        'nonce': b'nonce',
                        'tag': b'tag',
                        'user_id': 1})

        self.cursor.execute("INSERT INTO accounts VALUES (:id, :name, :login, :password, :salt, :nonce, :tag, :user_id)",
                       {'id': None,
                        'name': 'Company 2',
                        'login': 'testemail@gmail.com',
                        'password': b'password',
                        'salt': b'salt',
                        'nonce': b'nonce',
                        'tag': b'tag',
                        'user_id': 1})

        self.cursor.execute("INSERT INTO accounts VALUES (:id, :name, :login, :password, :salt, :nonce, :tag, :user_id)",
                       {'id': None,
                        'name': 'Company 1',
                        'login': 'otheremail@gmail.com',
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
        self.cursor.execute("INSERT INTO accounts VALUES (:id, :name, :login, :password, :salt, :nonce, :tag, :user_id)",
                       {'id': None,
                        'name': 'Company 1',
                        'login': 'testemail@gmail.com',
                        'password': b'password',
                        'salt': b'salt',
                        'nonce': b'nonce',
                        'tag': b'tag',
                        'user_id': 1})

        account_id = get_account_id_by_account_name_and_user_id(account_name='Company 1', user_id=2, connection=self.connection)

        self.assertIsNone(account_id)

    def test_get_all_account_names_and_logins_by_user_successful(self):
        """
        When a User has associated Accounts, the name and login of each are returned.
        """
        self.cursor.execute("INSERT INTO accounts VALUES (:id, :name, :login, :password, :salt, :nonce, :tag, :user_id)",
                       {'id': None,
                        'name': 'Company 1',
                        'login': 'testemail@gmail.com',
                        'password': b'password',
                        'salt': b'salt',
                        'nonce': b'nonce',
                        'tag': b'tag',
                        'user_id': 1})

        self.cursor.execute("INSERT INTO accounts VALUES (:id, :name, :login, :password, :salt, :nonce, :tag, :user_id)",
                       {'id': None,
                        'name': 'Company 2',
                        'login': 'testemail@gmail.com',
                        'password': b'password',
                        'salt': b'salt',
                        'nonce': b'nonce',
                        'tag': b'tag',
                        'user_id': 1})

        self.cursor.execute("INSERT INTO accounts VALUES (:id, :name, :login, :password, :salt, :nonce, :tag, :user_id)",
                       {'id': None,
                        'name': 'Company 1',
                        'login': 'otheremail@gmail.com',
                        'password': b'password',
                        'salt': b'salt',
                        'nonce': b'nonce',
                        'tag': b'tag',
                        'user_id': 2})

        user_1_account_names_and_logins = get_all_account_names_and_logins_by_user_id(user_id=1, connection=self.connection)
        user_2_account_names_and_logins = get_all_account_names_and_logins_by_user_id(user_id=2, connection=self.connection)

        self.assertEquals([('Company 1', 'testemail@gmail.com'), ('Company 2', 'testemail@gmail.com'),], user_1_account_names_and_logins)
        self.assertEquals([('Company 1', 'otheremail@gmail.com'),], user_2_account_names_and_logins)

    def test_get_all_account_names_and_logins_by_user_non_existent(self):
        """
        When a User has no associated Accounts, None is returned.
        """
        user_1_account_names_and_logins = get_all_account_names_and_logins_by_user_id(user_id=1, connection=self.connection)

        self.assertIsNone(user_1_account_names_and_logins)

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
            "INSERT INTO accounts VALUES (:id, :name, :login, :password, :salt, :nonce, :tag, :user_id)",
            {'id': None,
             'name': 'Company 1',
             'login': 'testemail@gmail.com',
             'password': ciphertext,
             'salt': salt,
             'nonce': nonce,
             'tag': tag,
             'user_id': user_id})

        self.cursor.execute(
            "INSERT INTO accounts VALUES (:id, :name, :login, :password, :salt, :nonce, :tag, :user_id)",
            {'id': None,
             'name': 'Company 2',
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
            self.assertEquals('There is no account with the given id', str(e))
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
            self.assertEquals('There are no Users with the given user_id', str(e))
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
            self.assertEquals('There are no Users with the given user_id', str(e))
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




