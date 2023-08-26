import unittest

from Utils.cryptography import derive_256_bit_key, encrypt_aes_256_cbc, decrypt_aes_256_cbc


class CryptographyUtilsTests(unittest.TestCase):
    def test_derive_256_bit_key(self):
        """
        Derives a 256-bit key from any given string or bytes.
        """
        passwords = ['', 'TestPass', b'BytePass', "Unfathomably Extremely Long Test Password That Has 63 Characters"]

        for password in passwords:
            key = derive_256_bit_key(password)
            self.assertEquals(256, len(key) * 8)  # len(key) is 32 bytes * 8 bits/byte = 256 bits

    def test_encrypt_and_decrypt_aes_256_cbc(self):
        """
        Encrypting plaintext and decrypting the resulting ciphertext should result in the original plaintext (in string
        form).
        """
        plaintext = b'plaintext'
        key = derive_256_bit_key('password')
        ciphertext, iv = encrypt_aes_256_cbc(key, plaintext)
        decrypted_plaintext = decrypt_aes_256_cbc(key, ciphertext, iv)

        self.assertEquals(plaintext.decode('utf-8'), decrypted_plaintext)

    def test_encrypt_and_decrypt_aes_256_cbc_str_plaintext(self):
        """
        Encrypting plaintext and decrypting the resulting ciphertext should result in the original plaintext even if the
        given plaintext is a string instead of bytes.
        """
        plaintext = 'plaintext'
        key = derive_256_bit_key('password')
        ciphertext, iv = encrypt_aes_256_cbc(key, plaintext)
        decrypted_plaintext = decrypt_aes_256_cbc(key, ciphertext, iv)

        self.assertEquals(plaintext, decrypted_plaintext)

    def test_encrypt_aes_256_cbc_invalid_key(self):
        """
        Encrypting should fail when given an invalid key.
        """
        try:
            encrypt_aes_256_cbc(b'hello', b'plaintext')
        except ValueError as e:
            self.assertEquals('Incorrect AES key length (5 bytes)', str(e))
        else:
            self.fail('ValueError should have occurred for an invalid key.')

    def test_decrypt_aes_256_cbc_key_incorrect_length(self):
        """
        Decrypting should fail when given key is not 256-bit (32 bytes long).
        """
        try:
            decrypt_aes_256_cbc(b'hello', b'ciphertext', b'iv')
        except ValueError as e:
            self.assertEquals('Incorrect AES key length (5 bytes)', str(e))
        else:
            self.fail('ValueError should have occurred for incorrect key length.')

    def test_decrypt_aes_256_cbc_ciphertext_zero_length(self):
        """
        Decrypting should fail when given empty/zero-length ciphertext.
        """
        plaintext = 'plaintext'
        key = derive_256_bit_key('password')
        ciphertext, iv = encrypt_aes_256_cbc(key, plaintext)

        try:
            decrypt_aes_256_cbc(key, b'', iv)
        except ValueError as e:
            self.assertEquals('Zero-length input cannot be unpadded', str(e))
        else:
            self.fail('ValueError should have occurred for an invalid ciphertext.')

    def test_decrypt_aes_256_cbc_wrong_ciphertext(self):
        """
        Decrypting should fail when given ciphertext made from a differently initialized encryption.
        """
        plaintext = 'plaintext'
        key_1 = derive_256_bit_key('password')
        key_2 = derive_256_bit_key('password')
        ciphertext_1, iv_1 = encrypt_aes_256_cbc(key_1, plaintext)
        ciphertext_2, iv_2 = encrypt_aes_256_cbc(key_2, plaintext)

        try:
            decrypt_aes_256_cbc(key_2, ciphertext_1, iv_2)
        except ValueError as e:
            self.assertEquals('Padding is incorrect.', str(e))
        else:
            self.fail('Padding should be incorrect due to a mismatch between the ciphertext and the key and iv used.')

    def test_decrypt_aes_256_cbc_iv_incorrect_length(self):
        """
        Decrypting should fail when given iv is not 16 bytes long.
        """
        plaintext = 'plaintext'
        key = derive_256_bit_key('password')
        ciphertext, iv = encrypt_aes_256_cbc(key, plaintext)

        try:
            decrypt_aes_256_cbc(key, ciphertext, b'')
        except ValueError as e:
            self.assertEquals('Incorrect IV length (it must be 16 bytes long)', str(e))
        else:
            self.fail('ValueError should have occurred for incorrect iv length.')
