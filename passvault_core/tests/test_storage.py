import pytest
import tempfile
import os

cryptography = pytest.importorskip("cryptography")
argon2 = pytest.importorskip("argon2.low_level")

from passvault_core.storage import create_vault, open_vault


def test_create_and_open_vault(tmp_path):
    path = tmp_path / "vault.json"
    master = "mysecret"
    data = {"items": [{"name": "example", "username": "u", "password": "p"}]}
    create_vault(str(path), master, initial_data=data, time=1, memory=32768, parallelism=1)
    # file permissions check (owner only)
    st = os.stat(str(path))
    assert oct(st.st_mode & 0o777) == oct(0o600)
    loaded = open_vault(str(path), master)
    assert loaded == data
