from sqlite3 import Connection

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

from Utils.database import get_login_password_by_email


class Login:
    """
    A Login represents the email and password used to log into the password manager.
    The email serves as a unique identifier for the User and the password serves as their "master password" for the
    password manager. The password is hashed upon instantiation using argon2.
    """
    def __init__(self, email: str, plaintext_password: str) -> None:
        """
        Initializes the login with the given email and an argon2 hash of the given password.
        :param email: the email for the user's login to the application
        :param plaintext_password: the password for the user's login to the application
        """
        self.__email = email

        ph = PasswordHasher()
        self.__password = ph.hash(plaintext_password)

    def __repr__(self):
        return f"{self.__class__.__name__}({self.__email}, {self.__password})"

    @staticmethod
    def is_valid_login(email: str, password: str, connection: Connection) -> bool:
        """
        When a user attempts to sign in, verifies their account info. Returns True if there is a Login with a matching
        email and password (using verification of the hash for the password). Returns False otherwise.
        :param email: the given email when a user signs in
        :param password: the given password when a user signs in (plaintext)
        :param connection: the database connection to use
        :return: True if there is an existing Login with the corresponding email and password, False otherwise
        """
        ph = PasswordHasher()
        hashed_password = get_login_password_by_email(email=email, connection=connection)

        try:
            return hashed_password and ph.verify(hashed_password, password)
        except VerifyMismatchError:
            return False
