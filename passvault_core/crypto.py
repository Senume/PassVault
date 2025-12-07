import os
import json
import base64
from typing import Tuple

try:
    from argon2.low_level import hash_secret_raw, Type
except Exception as e:
    hash_secret_raw = None  # type: ignore

try:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
except Exception as e:
    AESGCM = None  # type: ignore

from .errors import DecryptionError


DEFAULT_TIME = 2
DEFAULT_MEMORY = 65536  # KiB (64 MiB)
DEFAULT_PARALLELISM = 1
DEFAULT_KEY_LEN = 32


def derive_key(password: str, salt: bytes, time_cost: int = DEFAULT_TIME, memory_cost: int = DEFAULT_MEMORY, parallelism: int = DEFAULT_PARALLELISM, key_len: int = DEFAULT_KEY_LEN) -> bytes:
    """Derive a binary key from password and salt using Argon2id.

    Requires `argon2-cffi` to be installed. Raises ImportError if not available.
    """
    if hash_secret_raw is None:
        raise ImportError("argon2.low_level.hash_secret_raw is required (install argon2-cffi)")
    if isinstance(password, str):
        password = password.encode("utf-8")
    return hash_secret_raw(password, salt, time_cost, memory_cost, parallelism, key_len, Type.ID)


def encrypt(key: bytes, plaintext: bytes) -> Tuple[bytes, bytes]:
    """Encrypt plaintext with AES-GCM. Returns (nonce, ciphertext).

    Requires `cryptography` package.
    """
    if AESGCM is None:
        raise ImportError("cryptography AESGCM is required (install cryptography)")
    aesgcm = AESGCM(key)
    nonce = os.urandom(12)
    ct = aesgcm.encrypt(nonce, plaintext, associated_data=None)
    return nonce, ct


def decrypt(key: bytes, nonce: bytes, ciphertext: bytes) -> bytes:
    """Decrypt AES-GCM ciphertext. Raises DecryptionError on auth failure."""
    if AESGCM is None:
        raise ImportError("cryptography AESGCM is required (install cryptography)")
    aesgcm = AESGCM(key)
    try:
        pt = aesgcm.decrypt(nonce, ciphertext, associated_data=None)
    except Exception as e:
        raise DecryptionError("decryption failed") from e
    return pt
