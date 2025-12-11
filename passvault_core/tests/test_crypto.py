"""Tests for passvault_core.crypto module."""
import os
import pytest
from passvault_core.crypto import (
    derive_key,
    encrypt,
    decrypt,
    DEFAULT_TIME,
    DEFAULT_MEMORY,
    DEFAULT_PARALLELISM,
    DEFAULT_KEY_LEN,
)
from passvault_core.errors import DecryptionError


class TestDeriveKey:
    """Test key derivation using Argon2id."""

    def test_derive_key_basic(self):
        """Test basic key derivation."""
        password = "test_password"
        salt = os.urandom(16)
        key = derive_key(password, salt)
        assert isinstance(key, bytes)
        assert len(key) == DEFAULT_KEY_LEN

    def test_derive_key_same_inputs_same_output(self):
        """Test that same password + salt produce same key."""
        password = "test_password"
        salt = os.urandom(16)
        key1 = derive_key(password, salt)
        key2 = derive_key(password, salt)
        assert key1 == key2

    def test_derive_key_different_passwords(self):
        """Test that different passwords produce different keys."""
        salt = os.urandom(16)
        key1 = derive_key("password1", salt)
        key2 = derive_key("password2", salt)
        assert key1 != key2

    def test_derive_key_different_salts(self):
        """Test that different salts produce different keys."""
        password = "test_password"
        key1 = derive_key(password, os.urandom(16))
        key2 = derive_key(password, os.urandom(16))
        assert key1 != key2

    def test_derive_key_custom_params(self):
        """Test key derivation with custom KDF parameters."""
        password = "test_password"
        salt = os.urandom(16)
        key = derive_key(password, salt, time_cost=3, memory_cost=131072, parallelism=2)
        assert isinstance(key, bytes)
        assert len(key) == DEFAULT_KEY_LEN

    def test_derive_key_custom_key_len(self):
        """Test key derivation with custom key length."""
        password = "test_password"
        salt = os.urandom(16)
        key = derive_key(password, salt, key_len=64)
        assert len(key) == 64

    def test_derive_key_bytes_password(self):
        """Test key derivation with bytes password."""
        password = b"test_password"
        salt = os.urandom(16)
        key = derive_key(password, salt)
        assert isinstance(key, bytes)

    def test_derive_key_empty_password(self):
        """Test key derivation with empty password."""
        password = ""
        salt = os.urandom(16)
        key = derive_key(password, salt)
        assert isinstance(key, bytes)


class TestEncrypt:
    """Test encryption using AES-GCM."""

    def test_encrypt_basic(self):
        """Test basic encryption."""
        key = os.urandom(32)
        plaintext = b"Hello, World!"
        nonce, ciphertext = encrypt(key, plaintext)
        assert isinstance(nonce, bytes)
        assert isinstance(ciphertext, bytes)
        assert len(nonce) == 12
        assert len(ciphertext) > 0

    def test_encrypt_empty_plaintext(self):
        """Test encryption of empty plaintext."""
        key = os.urandom(32)
        plaintext = b""
        nonce, ciphertext = encrypt(key, plaintext)
        assert isinstance(nonce, bytes)
        assert isinstance(ciphertext, bytes)

    def test_encrypt_large_plaintext(self):
        """Test encryption of large plaintext."""
        key = os.urandom(32)
        plaintext = b"x" * (1024 * 1024)  # 1 MB
        nonce, ciphertext = encrypt(key, plaintext)
        assert isinstance(nonce, bytes)
        assert isinstance(ciphertext, bytes)

    def test_encrypt_different_nonces(self):
        """Test that encrypt produces different nonces each call."""
        key = os.urandom(32)
        plaintext = b"test"
        nonce1, _ = encrypt(key, plaintext)
        nonce2, _ = encrypt(key, plaintext)
        assert nonce1 != nonce2


class TestDecrypt:
    """Test decryption using AES-GCM."""

    def test_decrypt_basic(self):
        """Test basic decrypt of encrypted data."""
        key = os.urandom(32)
        plaintext = b"Hello, World!"
        nonce, ciphertext = encrypt(key, plaintext)
        decrypted = decrypt(key, nonce, ciphertext)
        assert decrypted == plaintext

    def test_decrypt_empty_plaintext(self):
        """Test decrypt of empty plaintext."""
        key = os.urandom(32)
        plaintext = b""
        nonce, ciphertext = encrypt(key, plaintext)
        decrypted = decrypt(key, nonce, ciphertext)
        assert decrypted == plaintext

    def test_decrypt_large_plaintext(self):
        """Test decrypt of large plaintext."""
        key = os.urandom(32)
        plaintext = b"x" * (1024 * 1024)  # 1 MB
        nonce, ciphertext = encrypt(key, plaintext)
        decrypted = decrypt(key, nonce, ciphertext)
        assert decrypted == plaintext

    def test_decrypt_wrong_key(self):
        """Test decrypt with wrong key raises DecryptionError."""
        key1 = os.urandom(32)
        key2 = os.urandom(32)
        plaintext = b"Hello, World!"
        nonce, ciphertext = encrypt(key1, plaintext)
        with pytest.raises(DecryptionError):
            decrypt(key2, nonce, ciphertext)

    def test_decrypt_corrupted_ciphertext(self):
        """Test decrypt with corrupted ciphertext raises DecryptionError."""
        key = os.urandom(32)
        plaintext = b"Hello, World!"
        nonce, ciphertext = encrypt(key, plaintext)
        corrupted = bytes([ciphertext[0] ^ 1]) + ciphertext[1:]
        with pytest.raises(DecryptionError):
            decrypt(key, nonce, corrupted)

    def test_decrypt_wrong_nonce(self):
        """Test decrypt with wrong nonce raises DecryptionError."""
        key = os.urandom(32)
        plaintext = b"Hello, World!"
        nonce, ciphertext = encrypt(key, plaintext)
        wrong_nonce = os.urandom(12)
        with pytest.raises(DecryptionError):
            decrypt(key, wrong_nonce, ciphertext)


class TestRoundTrip:
    """Test encrypt/decrypt round trips."""

    def test_roundtrip_various_plaintexts(self):
        """Test roundtrip for various plaintexts."""
        key = os.urandom(32)
        plaintexts = [
            b"",
            b"a",
            b"Hello, World!",
            b'{"key": "value"}',
            bytes(range(256)),
        ]
        for plaintext in plaintexts:
            nonce, ciphertext = encrypt(key, plaintext)
            decrypted = decrypt(key, nonce, ciphertext)
            assert decrypted == plaintext

    def test_roundtrip_with_derived_key(self):
        """Test roundtrip with derived key from password."""
        password = "my_secure_password"
        salt = os.urandom(16)
        plaintext = b"Secret data"
        key = derive_key(password, salt)
        nonce, ciphertext = encrypt(key, plaintext)
        decrypted = decrypt(key, nonce, ciphertext)
        assert decrypted == plaintext
