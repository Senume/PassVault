"""Tests for passvault_core.schema module."""
import json
import pytest
from passvault_core.schema import (
    CredentialSchema,
    KDFParamsSchema,
    PointerSchema,
    VaultSchema,
)


class TestCredentialSchema:
    """Test CredentialSchema model."""

    def test_create_credential(self):
        """Test creating a credential."""
        cred = CredentialSchema(username="user1", password="pass123")
        assert cred.username == "user1"
        assert cred.password == "pass123"

    def test_credential_to_dict(self):
        """Test credential to_dict method."""
        cred = CredentialSchema(username="user1", password="pass123")
        d = cred.to_dict()
        assert d == {"username": "user1", "password": "pass123"}

    def test_credential_to_str(self):
        """Test credential to_str method."""
        cred = CredentialSchema(username="user1", password="pass123")
        s = cred.to_str()
        assert isinstance(s, str)
        parsed = json.loads(s)
        assert parsed["username"] == "user1"
        assert parsed["password"] == "pass123"

    def test_credential_from_str(self):
        """Test credential from_str classmethod."""
        original = CredentialSchema(username="user1", password="pass123")
        s = original.to_str()
        restored = CredentialSchema.from_str(s)
        assert restored.username == original.username
        assert restored.password == original.password

    def test_credential_from_str_invalid(self):
        """Test credential from_str with invalid JSON."""
        with pytest.raises(json.JSONDecodeError):
            CredentialSchema.from_str("invalid json")

    def test_credential_from_str_missing_field(self):
        """Test credential from_str with missing required field."""
        with pytest.raises(Exception):  # Pydantic validation error
            CredentialSchema.from_str('{"username": "user1"}')


class TestKDFParamsSchema:
    """Test KDFParamsSchema model."""

    def test_create_kdf_params_defaults(self):
        """Test creating KDF params with defaults."""
        params = KDFParamsSchema()
        assert params.time_cost == 2
        assert params.memory_cost == 65536
        assert params.parallelism == 1

    def test_create_kdf_params_custom(self):
        """Test creating KDF params with custom values."""
        params = KDFParamsSchema(time_cost=3, memory_cost=131072, parallelism=2)
        assert params.time_cost == 3
        assert params.memory_cost == 131072
        assert params.parallelism == 2

    def test_kdf_params_to_dict(self):
        """Test KDF params to_dict method."""
        params = KDFParamsSchema(time_cost=3, memory_cost=131072, parallelism=2)
        d = params.to_dict()
        assert d == {"time_cost": 3, "memory_cost": 131072, "parallelism": 2}


class TestPointerSchema:
    """Test PointerSchema model."""

    def test_create_pointer(self):
        """Test creating a pointer."""
        nonce = b"test_nonce_1234"
        ptr = PointerSchema(id="ptr1", vault_id="vault1", nonce=nonce)
        assert ptr.id == "ptr1"
        assert ptr.vault_id == "vault1"
        assert ptr.nonce == nonce

    def test_pointer_to_dict(self):
        """Test pointer to_dict method."""
        nonce = b"test_nonce_1234"
        ptr = PointerSchema(id="ptr1", vault_id="vault1", nonce=nonce)
        d = ptr.to_dict()
        assert d["id"] == "ptr1"
        assert d["vault_id"] == "vault1"
        assert d["nonce"] == nonce

    def test_pointer_from_dict(self):
        """Test pointer from_dict classmethod."""
        nonce = b"test_nonce_1234"
        data = {"id": "ptr1", "vault_id": "vault1", "nonce": nonce}
        ptr = PointerSchema.from_dict(data)
        assert ptr.id == "ptr1"
        assert ptr.vault_id == "vault1"
        assert ptr.nonce == nonce

    def test_pointer_from_dict_invalid(self):
        """Test pointer from_dict with missing field."""
        data = {"id": "ptr1"}
        with pytest.raises(Exception):  # Pydantic validation error
            PointerSchema.from_dict(data)


class TestVaultSchema:
    """Test VaultSchema model."""

    def test_create_vault_defaults(self):
        """Test creating a vault with defaults."""
        salt = b"salt_value_12345"
        vault = VaultSchema(id="vault1", salt=salt)
        assert vault.id == "vault1"
        assert vault.salt == salt
        assert vault.encrypted_pointers == []
        assert isinstance(vault.kdf_params, KDFParamsSchema)

    def test_create_vault_with_pointers(self):
        """Test creating a vault with pointers."""
        salt = b"salt_value_12345"
        nonce = b"nonce_value_1234"
        ptr = PointerSchema(id="ptr1", vault_id="vault1", nonce=nonce)
        vault = VaultSchema(id="vault1", salt=salt, encrypted_pointers=[ptr])
        assert len(vault.encrypted_pointers) == 1
        assert vault.encrypted_pointers[0].id == "ptr1"

    def test_vault_to_dict(self):
        """Test vault to_dict method."""
        salt = b"salt_value_12345"
        nonce = b"nonce_value_1234"
        ptr = PointerSchema(id="ptr1", vault_id="vault1", nonce=nonce)
        vault = VaultSchema(id="vault1", salt=salt, encrypted_pointers=[ptr])
        d = vault.to_dict()
        assert d["id"] == "vault1"
        assert d["salt"] == salt
        assert len(d["encrypted_pointers"]) == 1
        assert d["encrypted_pointers"][0]["id"] == "ptr1"

    def test_vault_from_dict(self):
        """Test vault from_dict classmethod."""
        salt = b"salt_value_12345"
        nonce = b"nonce_value_1234"
        data = {
            "id": "vault1",
            "salt": salt,
            "encrypted_pointers": [{"id": "ptr1", "vault_id": "vault1", "nonce": nonce}],
            "kdf_params": {"time_cost": 2, "memory_cost": 65536, "parallelism": 1},
        }
        vault = VaultSchema.from_dict(data)
        assert vault.id == "vault1"
        assert vault.salt == salt
        assert len(vault.encrypted_pointers) == 1

    def test_vault_from_dict_with_none_pointers(self):
        """Test vault from_dict with None pointers."""
        salt = b"salt_value_12345"
        data = {
            "id": "vault1",
            "salt": salt,
            "encrypted_pointers": [None, None],
            "kdf_params": {"time_cost": 2, "memory_cost": 65536, "parallelism": 1},
        }
        vault = VaultSchema.from_dict(data)
        assert vault.id == "vault1"
        assert len(vault.encrypted_pointers) == 2
        assert vault.encrypted_pointers[0] is None
