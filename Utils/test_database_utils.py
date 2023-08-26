import unittest

from Utils.database import get_login_password_by_email, db_setup


class DatabaseUtilsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.connection, self.cursor = db_setup()

    def tearDown(self) -> None:
        self.cursor.close()
        self.connection.close()

    def test_get_login_password_by_email_successful(self):
        """
        When the given User with the given email exists, the corresponding password is returned.
        """
        # Create test user
        self.cursor.execute("INSERT INTO users VALUES (:id, :email, :password)", {'id': None,
                                                                                  'email': 'testemail@gmail.com',
                                                                                  'password': '123abc'})

        password = get_login_password_by_email(email="testemail@gmail.com", connection=self.connection)

        self.assertEquals('123abc', password)

    def test_get_login_password_by_email_non_existent(self):
        """
        When the given User with the given email does not exist, None is returned.
        """
        # Create test user
        self.cursor.execute("INSERT INTO users VALUES (:id, :email, :password)", {'id': None,
                                                                                  'email': 'testemail@gmail.com',
                                                                                  'password': '123abc'})

        password = get_login_password_by_email(email="secondtestemail@gmail.com", connection=self.connection)

        self.assertIsNone(password)
