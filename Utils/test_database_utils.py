import unittest
from typing import Tuple

from argon2 import PasswordHasher

from Utils.cryptography import derive_256_bit_salt_and_key, encrypt_aes_256_gcm
from Utils.database import get_login_password_by_email, get_account_id_by_account_name_and_user_id, db_setup, \
    get_decrypted_account_password, get_all_account_names_and_logins_by_user, get_user_id_by_email


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
    def test_get_login_password_by_email_successful(self):
        """
        When the given User with the given email exists, the corresponding password is returned.
        """
        password_1 = get_login_password_by_email(email="testemail@gmail.com", connection=self.connection)
        password_2 = get_login_password_by_email(email="testemail2@gmail.com", connection=self.connection)

        self.assertEquals('123abc', password_1)
        self.assertEquals('456def', password_2)

    def test_get_login_password_by_email_non_existent(self):
        """
        When the given User with the given email does not exist, None is returned.
        """
        password = get_login_password_by_email(email="secondtestemail@gmail.com", connection=self.connection)

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

        password = get_login_password_by_email(email="secondtestemail@gmail.com", connection=self.connection)

        self.assertIsNone(password)

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

        user_1_account_names_and_logins = get_all_account_names_and_logins_by_user(user_id=1, connection=self.connection)
        user_2_account_names_and_logins = get_all_account_names_and_logins_by_user(user_id=2, connection=self.connection)

        self.assertEquals([('Company 1', 'testemail@gmail.com'), ('Company 2', 'testemail@gmail.com'),], user_1_account_names_and_logins)
        self.assertEquals([('Company 1', 'otheremail@gmail.com'),], user_2_account_names_and_logins)

    def test_get_all_account_names_and_logins_by_user_non_existent(self):
        """
        When a User has no associated Accounts, None is returned.
        """
        user_1_account_names_and_logins = get_all_account_names_and_logins_by_user(user_id=1, connection=self.connection)

        self.assertIsNone(user_1_account_names_and_logins)

    def get_decrypted_account_password_set_up(self) -> Tuple[str, str]:
        """
        Abstracts the setup for the get_decrypted_account_password tests.
        :return: the master and account passwords
        """
        ph = PasswordHasher()
        master_password = 'TestPassword'
        account_password = 'AccountPassword'

        self.cursor.execute("INSERT INTO users VALUES (:id, :email, :password)", {'id': 3,
                                                                                  'email': 'coolemail@gmail.com',
                                                                                  'password': ph.hash(master_password)})

        salt, key = derive_256_bit_salt_and_key(master_password)

        ciphertext, nonce, tag = encrypt_aes_256_gcm(key, account_password)

        self.cursor.execute(
            "INSERT INTO accounts VALUES (:id, :name, :login, :password, :salt, :nonce, :tag, :user_id)",
            {'id': None,
             'name': 'Company 1',
             'login': 'testemail@gmail.com',
             'password': ciphertext,
             'salt': salt,
             'nonce': nonce,
             'tag': tag,
             'user_id': 3})

        return master_password, account_password

    def test_get_decrypted_account_password_successful(self):
        """
        When given fully valid inputs, the plaintext Account password is returned.
        """
        master_password, account_password = self.get_decrypted_account_password_set_up()

        plaintext = get_decrypted_account_password(account_id=1, master_password=master_password, connection=self.connection)

        self.assertEquals(account_password, plaintext)

    def test_get_decrypted_account_password_non_existent_account(self):
        """
        When an Account with the given id does not exist, Value Error is raised.
        """
        master_password, account_password = self.get_decrypted_account_password_set_up()

        try:
            get_decrypted_account_password(account_id=2, master_password=master_password, connection=self.connection)
        except ValueError as e:
            self.assertEquals('There is no account with the given id', str(e))
        else:
            self.fail('Value error was not raised when the account was non-existent')

    def test_get_decrypted_account_password_wrong_master_password(self):
        """
        When an Account with the given id does not exist, Value Error is raised.
        """
        self.get_decrypted_account_password_set_up()

        try:
            get_decrypted_account_password(account_id=1, master_password='wrong_password', connection=self.connection)
        except ValueError as e:
            self.assertEquals('An error occurred while decrypting the password: MAC check failed', str(e))
        else:
            self.fail('Value error was not raised when the wrong master password was given')
