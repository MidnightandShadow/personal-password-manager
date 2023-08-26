import base64
import unittest

import argon2.low_level
from argon2 import PasswordHasher

from Utils.cryptography import derive_256_bit_key, encrypt_aes_256_gcm, decrypt_aes_256_gcm


class CryptographyUtilsTests(unittest.TestCase):
    def test_derive_256_bit_key(self):
        """
        Derives a 256-bit key from a password of any given string or bytes.
        """
        passwords = ['', 'TestPass', b'BytePass', "Unfathomably Extremely Long Test Password That Has 63 Characters"]

        for password in passwords:
            salt, key = derive_256_bit_key(password)
            self.assertEquals(256, len(key) * 8)  # len(key) is 32 bytes * 8 bits/byte = 256 bits

        password = 'TestPass'

        salt, key_1 = derive_256_bit_key(password)
        ph = PasswordHasher()
        full = ph.hash(password=password, salt=salt)
        encoded_hash = full.split('$')[-1]  # argon2 format puts the base64 encoded hash after the last $ delim
        key_2 = base64.urlsafe_b64decode(f'{encoded_hash}==')  # argon2 does not use padding in its base64, so we add it back

        self.assertEquals(key_1, key_2)

    def test_derive_256_bit_key_given_valid_salt(self):
        """
        Derives identical 256-bit keys from the same given password when the salts are identical.
        """
        password = 'TestPass'

        # Precompute original salt to use from function call without providing a salt
        original_salt, original_key = derive_256_bit_key(password=password)

        # Use the function with the salt
        salt_1, key_1 = derive_256_bit_key(password=password, salt=original_salt)

        # Returned salt and key should be the same
        self.assertEquals(original_salt, salt_1)
        self.assertEquals(original_key, key_1)

    def test_derive_256_bit_key_given_invalid_salt(self):
        """
        Deriving the key should fail when the given salt is too short.
        """
        password = 'TestPass'
        salt = 'short'

        try:
            derive_256_bit_key(password=password, salt=salt)
        except argon2.exceptions.HashingError as e:
            self.assertEquals('Salt is too short', str(e))
        else:
            self.fail('Deriving a key with too short of a salt should have failed')

    def test_encrypt_and_decrypt_aes_256_gcm(self):
        """
        Encrypting plaintext and decrypting the resulting ciphertext should result in the original plaintext (in string
        form).
        """
        plaintext = b'plaintext'
        salt, key = derive_256_bit_key('password')
        ciphertext, nonce, tag = encrypt_aes_256_gcm(key, plaintext)
        decrypted_plaintext = decrypt_aes_256_gcm(key, ciphertext, nonce, tag)

        self.assertEquals(plaintext.decode('utf-8'), decrypted_plaintext)

    def test_encrypt_and_decrypt_aes_256_gcm_str_plaintext(self):
        """
        Encrypting plaintext and decrypting the resulting ciphertext should result in the original plaintext even if the
        given plaintext is a string instead of bytes.
        """
        plaintext = 'plaintext'
        salt, key = derive_256_bit_key('password')
        ciphertext, nonce, tag = encrypt_aes_256_gcm(key, plaintext)
        decrypted_plaintext = decrypt_aes_256_gcm(key, ciphertext, nonce, tag)

        self.assertEquals(plaintext, decrypted_plaintext)

    def test_encrypt_aes_256_gcm_invalid_key(self):
        """
        Encrypting should fail when given an invalid key.
        """
        try:
            encrypt_aes_256_gcm(b'hello', b'plaintext')
        except ValueError as e:
            self.assertEquals('Incorrect AES key length (5 bytes)', str(e))
        else:
            self.fail('ValueError should have occurred for an invalid key.')

    def test_decrypt_aes_256_gcm_key_incorrect_length(self):
        """
        Decrypting should fail when given key is not 256-bit (32 bytes long).
        """
        plaintext = 'plaintext'
        salt, key = derive_256_bit_key('password')
        ciphertext, nonce, tag = encrypt_aes_256_gcm(key, plaintext)

        try:
            decrypt_aes_256_gcm(b'hello', ciphertext, nonce, tag)
        except ValueError as e:
            self.assertEquals('Incorrect AES key length (5 bytes)', str(e))
        else:
            self.fail('ValueError should have occurred for incorrect key length.')

    def test_decrypt_aes_256_gcm_ciphertext_zero_length(self):
        """
        Decrypting should fail when given empty/zero-length ciphertext.
        """
        plaintext = 'plaintext'
        salt, key = derive_256_bit_key('password')
        ciphertext, nonce, tag = encrypt_aes_256_gcm(key, plaintext)

        try:
            decrypt_aes_256_gcm(key, b'', nonce, tag)
        except ValueError as e:
            self.assertEquals('MAC check failed', str(e))
        else:
            self.fail('ValueError should have occurred for failed MAC check.')

    def test_decrypt_aes_256_gcm_wrong_ciphertext(self):
        """
        Decrypting should fail when given ciphertext made from a differently initialized encryption.
        """
        plaintext = 'plaintext'
        salt, key_1 = derive_256_bit_key('password')
        salt, key_2 = derive_256_bit_key('password')
        ciphertext_1, nonce_1, tag_1 = encrypt_aes_256_gcm(key_1, plaintext)
        ciphertext_2, nonce_2, tag_2 = encrypt_aes_256_gcm(key_2, plaintext)

        try:
            decrypt_aes_256_gcm(key_2, ciphertext_1, nonce_2, tag_2)
        except ValueError as e:
            self.assertEquals('MAC check failed', str(e))
        else:
            self.fail('ValueError should have occurred for failed MAC check.')

    def test_decrypt_aes_256_gcm_nonce_zero_length(self):
        """
        Decrypting should fail when given nonce is empty.
        """
        plaintext = 'plaintext'
        salt, key = derive_256_bit_key('password')
        ciphertext, nonce, tag = encrypt_aes_256_gcm(key, plaintext)

        try:
            decrypt_aes_256_gcm(key, ciphertext, b'', tag)
        except ValueError as e:
            self.assertEquals('Nonce cannot be empty', str(e))
        else:
            self.fail('ValueError should have occurred for nonce needing to be non-empty.')

    def test_decrypt_aes_256_gcm_invalid_nonce(self):
        """
        Decrypting should fail when given nonce is invalid.
        """
        plaintext = 'plaintext'
        salt, key = derive_256_bit_key('password')
        ciphertext, nonce, tag = encrypt_aes_256_gcm(key, plaintext)

        try:
            decrypt_aes_256_gcm(key, ciphertext, b'nonce', tag)
        except ValueError as e:
            self.assertEquals('MAC check failed', str(e))
        else:
            self.fail('ValueError should have occurred for failed MAC check.')

    def test_decrypt_aes_256_gcm_invalid_tag(self):
        """
        Decrypting should fail when given tag is invalid.
        """
        plaintext = 'plaintext'
        salt, key = derive_256_bit_key('password')
        ciphertext, nonce, tag = encrypt_aes_256_gcm(key, plaintext)

        try:
            decrypt_aes_256_gcm(key, ciphertext, nonce, b'tag')
        except ValueError as e:
            self.assertEquals('MAC check failed', str(e))
        else:
            self.fail('ValueError should have occurred for failed MAC check.')
