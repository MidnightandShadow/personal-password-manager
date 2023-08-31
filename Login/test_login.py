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


