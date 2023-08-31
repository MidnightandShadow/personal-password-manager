from sqlite3 import Connection

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

from Utils.database import get_login_password_by_user_id


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
