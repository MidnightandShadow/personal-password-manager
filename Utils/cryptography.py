import base64
from typing import Union, Tuple

from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from argon2 import PasswordHasher


def derive_256_bit_key(password: Union[str, bytes]) -> bytes:
    """
    Derives 256-bit key from the given password using Argon2 and returns it as bytes.
    :param password: the given password to derive the key from
    :return: the 256-bit key
    """
    ph = PasswordHasher()
    encoded_hash = ph.hash(password).split('$')[-1]  # argon2 format puts the base64 encoded hash after the last $ delim
    key = base64.urlsafe_b64decode(f'{encoded_hash}==')  # argon2 does not use padding in its base64, so we add it back

    return key


def encrypt_aes_256_cbc(key: bytes, plaintext: Union[bytes, str]) -> Tuple[bytes, Union[bytes, bytearray, memoryview]]:
    """
    Encrypts data using AES-256-CBC utilizing PyCryptodome. If the plaintext is a string instead of bytes, it will be
    encoded to bytes using utf-8. This is done out of convenience so calls to this method can simply pass in plaintext
    in string form without needing to convert it each time.
    :param key: the key to use for encryption
    :param plaintext: the data to be encrypted
    :return: the ciphertext and the cipher initialization vector
    """
    if isinstance(plaintext, str):
        plaintext = plaintext.encode('utf-8')
    cipher = AES.new(key, AES.MODE_CBC)
    ciphertext = cipher.encrypt(pad(plaintext, AES.block_size))
    ciphertext = ciphertext

    return ciphertext, cipher.iv


def decrypt_aes_256_cbc(key: bytes, ciphertext: Union[bytes, bytearray, memoryview], iv: Union[bytes, bytearray, memoryview]) -> str:
    """
    Decrypts data using AES-256-CBC utilizing PyCryptodome and returns a utf-8 string representation.
    :param key: the key to use for decryption
    :param ciphertext: the data to be decrypted
    :param iv: the initialization vector of the cipher
    :return: the decrypted plaintext as a string
    """
    decrypt_cipher = AES.new(key, AES.MODE_CBC, iv)
    plaintext = unpad(decrypt_cipher.decrypt(ciphertext), AES.block_size)

    return plaintext.decode('utf-8')
