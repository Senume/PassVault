import os
import json
import base64
from typing import Any, Dict
from .crypto import derive_key, encrypt, decrypt, DEFAULT_TIME, DEFAULT_MEMORY, DEFAULT_PARALLELISM
from .utils import atomic_write
from .errors import DecryptionError


def _b64(x: bytes) -> str:
    return base64.b64encode(x).decode("ascii")


def _u8(s: str) -> bytes:
    return base64.b64decode(s.encode("ascii"))


def create_vault(path: str, master_password: str, initial_data: Dict[str, Any] = None, *, time: int = DEFAULT_TIME, memory: int = DEFAULT_MEMORY, parallelism: int = DEFAULT_PARALLELISM) -> None:
    """Create a new encrypted vault file containing `initial_data` (dict).

    The vault is written as a JSON envelope with base64 fields. File perms are set to 0o600.
    """
    if initial_data is None:
        initial_data = {}
    salt = os.urandom(16)
    key = derive_key(master_password, salt, time, memory, parallelism)
    plaintext = json.dumps(initial_data, ensure_ascii=False).encode("utf-8")
    nonce, ciphertext = encrypt(key, plaintext)
    env = {
        "version": 1,
        "kdf": {"time": time, "memory": memory, "parallelism": parallelism},
        "salt": _b64(salt),
        "nonce": _b64(nonce),
        "ciphertext": _b64(ciphertext),
    }
    data = json.dumps(env, indent=2).encode("utf-8")
    atomic_write(path, data, mode=0o600)


def open_vault(path: str, master_password: str) -> Dict[str, Any]:
    """Open and decrypt a vault file. Returns the stored JSON object (dict).

    Raises DecryptionError if auth fails.
    """
    with open(path, "rb") as f:
        env = json.load(f)
    salt = _u8(env["salt"])
    params = env.get("kdf", {})
    time = params.get("time", DEFAULT_TIME)
    memory = params.get("memory", DEFAULT_MEMORY)
    parallelism = params.get("parallelism", DEFAULT_PARALLELISM)
    key = derive_key(master_password, salt, time, memory, parallelism)
    nonce = _u8(env["nonce"])
    ciphertext = _u8(env["ciphertext"])
    try:
        plaintext = decrypt(key, nonce, ciphertext)
    except DecryptionError:
        raise
    return json.loads(plaintext.decode("utf-8"))


def save_vault(path: str, master_password: str, data: Dict[str, Any]) -> None:
    """Overwrite an existing vault file with updated `data`.

    This function preserves the vault's KDF parameters and salt so the same
    password continues to work. It generates a fresh nonce for encryption.
    """
    # Read existing envelope
    with open(path, "rb") as f:
        env = json.load(f)

    # Extract existing kdf params and salt
    salt = _u8(env["salt"])
    params = env.get("kdf", {})
    time = params.get("time", DEFAULT_TIME)
    memory = params.get("memory", DEFAULT_MEMORY)
    parallelism = params.get("parallelism", DEFAULT_PARALLELISM)

    # Derive key and encrypt new plaintext
    key = derive_key(master_password, salt, time, memory, parallelism)
    plaintext = json.dumps(data, ensure_ascii=False).encode("utf-8")
    nonce, ciphertext = encrypt(key, plaintext)

    new_env = {
        "version": env.get("version", 1),
        "kdf": {"time": time, "memory": memory, "parallelism": parallelism},
        "salt": _b64(salt),
        "nonce": _b64(nonce),
        "ciphertext": _b64(ciphertext),
    }
    atomic_write(path, json.dumps(new_env, indent=2).encode("utf-8"), mode=0o600)
