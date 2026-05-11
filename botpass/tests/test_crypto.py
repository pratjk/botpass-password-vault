import unittest
import os
import json
from botpass.core.crypto import derive_key, encrypt_entry, decrypt_entry, hmac_domain

class TestCrypto(unittest.TestCase):
    def setUp(self):
        self.master_pw = "hunter2"
        self.salt = os.urandom(32)
        self.pepper = b"test_pepper"
        self.key = derive_key(self.master_pw, self.salt, self.pepper)

    def test_key_derivation_deterministic(self):
        key2 = derive_key(self.master_pw, self.salt, self.pepper)
        self.assertEqual(self.key, key2)

    def test_key_derivation_different_salt(self):
        salt2 = os.urandom(32)
        key2 = derive_key(self.master_pw, salt2, self.pepper)
        self.assertNotEqual(self.key, key2)

    def test_encrypt_decrypt(self):
        plaintext = "secret_message"
        ad = b"test_ad"
        
        ciphertext, nonce = encrypt_entry(plaintext, self.key, ad)
        self.assertNotEqual(plaintext.encode('utf-8'), ciphertext)
        
        decrypted = decrypt_entry(ciphertext, nonce, self.key, ad)
        self.assertEqual(plaintext, decrypted)

    def test_decrypt_fails_with_wrong_ad(self):
        plaintext = "secret_message"
        ad = b"test_ad"
        
        ciphertext, nonce = encrypt_entry(plaintext, self.key, ad)
        
        with self.assertRaises(Exception):
            decrypt_entry(ciphertext, nonce, self.key, b"wrong_ad")

    def test_hmac_domain(self):
        domain = "github.com"
        h1 = hmac_domain(domain, self.key)
        h2 = hmac_domain("GITHUB.COM", self.key)
        self.assertEqual(h1, h2) # Should handle casing
        
if __name__ == '__main__':
    unittest.main()
