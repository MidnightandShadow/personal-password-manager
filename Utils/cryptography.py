import base64
from typing import Union, Tuple

from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from argon2 import PasswordHasher


def derive_256_bit_key(password: Union[str, bytes], salt: Union[str, bytes] = None) -> Tuple[bytes, bytes]:
    """
    Derives 256-bit key from the given password (and the given salt if provided) using Argon2, and returns the
    corresponding salt and key.
    :param salt: the salt to use to derive the password (automatically generated if none provided)
    :param password: the given password to derive the key from
    :return: the corresponding salt and the 256-bit key
    """
    if isinstance(salt, str):
        salt = salt.encode('utf-8')

    ph = PasswordHasher()
    full_hash = ph.hash(password, salt=salt)

    if not salt:
        salt = full_hash.split('$')[-2]  # argon2 format puts the salt after the second-to-last $ delim
        salt = base64.urlsafe_b64decode(f'{salt}==')  # argon2 does not use padding in its base64, so we add it back

    encoded_hash = full_hash.split('$')[-1]  # argon2 format puts the base64 encoded hash after the last $ delim
    key = base64.urlsafe_b64decode(f'{encoded_hash}==')  # argon2 does not use padding in its base64, so we add it back

    return salt, key


def encrypt_aes_256_gcm(key: bytes, plaintext: Union[bytes, str]) -> Tuple[bytes, Union[bytes, bytearray, memoryview], bytes]:
    """
    Encrypts data using AES-256-GCM utilizing PyCryptodome and returns the corresponding ciphertext, nonce, and tag.
    If the plaintext is a string instead of bytes, it will be encoded to bytes using utf-8. This is done out of
    convenience so calls to this method can simply pass in plaintext in string form without needing to convert it each
    time.
    :param key: the key to use for encryption
    :param plaintext: the data to be encrypted
    :return: the ciphertext, the nonce, and the tag
    """
    if isinstance(plaintext, str):
        plaintext = plaintext.encode('utf-8')
    cipher = AES.new(key=key, mode=AES.MODE_GCM)
    ciphertext, tag = cipher.encrypt_and_digest(pad(data_to_pad=plaintext, block_size=AES.block_size))
    nonce = cipher.nonce

    return ciphertext, nonce, tag


def decrypt_aes_256_gcm(key: bytes, ciphertext: Union[bytes, bytearray, memoryview], nonce: bytes, tag: bytes) -> str:
    """
    Decrypts data using AES-256-GCM utilizing PyCryptodome, verifies the result, and returns a utf-8 string
    representation of the plaintext.
    :param key: the key to use for decryption
    :param ciphertext: the data to be decrypted
    :param nonce: the cryptographic nonce
    :param tag: the MAC/authentication tag
    :return: the decrypted plaintext as a string
    """
    decrypt_cipher = AES.new(key=key, mode=AES.MODE_GCM, nonce=nonce)
    plaintext = unpad(padded_data=decrypt_cipher.decrypt_and_verify(ciphertext, tag), block_size=AES.block_size)

    return plaintext.decode('utf-8')
