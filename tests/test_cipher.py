import pytest
from douyinpay._cipher import aes_decrypt, aes_encrypt
from douyinpay._errors import DecryptionError


class TestAESGCM:
    def test_roundtrip(self):
        key = bytes.fromhex("01" * 32)
        plaintext = b'{"appid":"test","mchid":"123"}'
        nonce, ciphertext = aes_encrypt(key, plaintext, b"")
        result = aes_decrypt(key, ciphertext, nonce, b"")
        assert result == plaintext

    def test_roundtrip_with_aad(self):
        key = bytes.fromhex("01" * 32)
        plaintext = b"hello"
        aad = b"associated_data"
        nonce, ciphertext = aes_encrypt(key, plaintext, aad)
        result = aes_decrypt(key, ciphertext, nonce, aad)
        assert result == plaintext

    def test_wrong_key_raises(self):
        key1 = bytes.fromhex("01" * 32)
        key2 = bytes.fromhex("02" * 32)
        _, ciphertext = aes_encrypt(key1, b"test", b"")
        with pytest.raises(DecryptionError):
            aes_decrypt(key2, ciphertext, b"\x00" * 12, b"")

    def test_wrong_nonce_raises(self):
        key = bytes.fromhex("01" * 32)
        _, ciphertext = aes_encrypt(key, b"test", b"")
        with pytest.raises(DecryptionError):
            aes_decrypt(key, ciphertext, b"\x01" * 12, b"")

    def test_encrypt_nonce_length(self):
        key = bytes.fromhex("01" * 32)
        nonce, ciphertext = aes_encrypt(key, b"payload", b"extra")
        assert len(nonce) == 12
        assert len(ciphertext) > 0
        assert aes_decrypt(key, ciphertext, nonce, b"extra") == b"payload"

    def test_empty_plaintext(self):
        key = bytes.fromhex("01" * 32)
        nonce, ciphertext = aes_encrypt(key, b"", b"")
        assert aes_decrypt(key, ciphertext, nonce, b"") == b""
