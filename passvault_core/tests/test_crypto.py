import pytest

cryptography = pytest.importorskip("cryptography")
argon2 = pytest.importorskip("argon2.low_level")

from passvault_core.crypto import derive_key, encrypt, decrypt


def test_derive_encrypt_decrypt_roundtrip():
    password = "correct horse battery staple"
    salt = b"\x00" * 16
    key = derive_key(password, salt, time_cost=1, memory_cost=32768, parallelism=1, key_len=32)
    assert isinstance(key, bytes) and len(key) == 32
    plaintext = b"hello world"
    nonce, ct = encrypt(key, plaintext)
    assert isinstance(nonce, bytes)
    pt = decrypt(key, nonce, ct)
    assert pt == plaintext
