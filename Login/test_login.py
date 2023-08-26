import unittest

from argon2 import PasswordHasher

from Login.login import Login
from Utils.database import db_setup

# TODO:
# Scenarios to test:
# For login function for login gui:
# missing email, missing password


class LoginTests(unittest.TestCase):
    def setUp(self) -> None:
        self.connection, self.cursor = db_setup()

        # Create test password
        ph = PasswordHasher()
        hashed_password = ph.hash('TestPassword')

        # Create test user
        self.cursor.execute("INSERT INTO users VALUES (:id, :email, :password)", {'id': None,
                                                                             'email': 'testemail@gmail.com',
                                                                             'password': hashed_password})

    def tearDown(self) -> None:
        self.cursor.close()
        self.connection.close()

    def test_is_valid_login(self):
        """
        is_valid_login returns True when the given login is already associated with a user in the database
        """
        self.assertTrue(Login.is_valid_login(email='testemail@gmail.com', password='TestPassword', connection=self.connection))

    def test_is_valid_login_invalid_email(self):
        """
        is_valid_login returns False when the given login is not associated with any user email in the database
        """
        self.assertFalse(Login.is_valid_login(email='wrongemail@gmail.com', password='TestPassword', connection=self.connection))

    def test_is_valid_login_invalid_password(self):
        """
        is_valid_login returns False when the given password does not match the email/login of the given user
        """
        self.assertFalse(Login.is_valid_login(email='testemail@gmail.com', password='WrongPassword', connection=self.connection))
