from Utils.cryptography import encrypt_aes_256_gcm


class Account:
    """
    An Account represents an external account that a user wants to save their login information for.
    """
    def __init__(self, account_name: str, username: str, plaintext_password: str, encryption_key: bytes) -> None:
        """
        Initializes the account with the given account name, username, and password, where the password is encrypted
        using AES-256-GCM with the given key. The related nonce, tag, and encryption key are also stored in the object.
        :param account_name: the name of the related account
        :param username: the username for the account
        :param plaintext_password: the password for the account
        :param encryption_key: the key to use to encrypt the given plaintext username and password
        """
        self.__account_name = account_name
        self.__username = username
        self.__encryption_key = encryption_key
        self.__password, self.__nonce, self.__tag = encrypt_aes_256_gcm(self.__encryption_key, plaintext_password)

    def __repr__(self):
        return f'{self.__class__.__name__}({self.__account_name}, {self.__username}, {self.__password}, {self.__nonce}, {self.__tag}, {self.__encryption_key})'

    def edit_account_info(self, account_name: str = None, username: str = None, plaintext_password: str = None) -> None:
        """
        Changes the account info to match the given account_name, username, and/or password. Only changes the fields
        provided, otherwise the corresponding field does not change.
        :param account_name: the name of the related account
        :param username: the username for the account
        :param plaintext_password: the password for the account
        """
        if account_name:
            self.__account_name = account_name

        if username:
            self.__username = username

        if plaintext_password:
            self.__password, self.__nonce, self.__tag = encrypt_aes_256_gcm(self.__encryption_key, plaintext_password)
