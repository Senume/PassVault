"""Tests for passvault_core.storage module."""
import os
import json
import tempfile
import shutil
import pytest
from passvault_core.storage import Vault
from passvault_core.schema import CredentialSchema, VaultSchema, PointerSchema


class TestVault:
    """Test Vault storage class."""

    @pytest.fixture
    def temp_vault_dir(self):
        """Create a temporary directory for vault tests."""
        temp_dir = tempfile.mkdtemp()
        original_path = Vault.path
        Vault.path = temp_dir
        yield temp_dir
        Vault.path = original_path
        shutil.rmtree(temp_dir, ignore_errors=True)

    def test_create_new_vault(self, temp_vault_dir):
        """Test creating a new vault."""
        vault = Vault("test_vault1", load=False)
        assert vault.vault_config.id == "test_vault1"
        assert isinstance(vault.vault_config.salt, bytes)
        assert len(vault.vault_config.salt) == 32
        assert vault.vault_config.encrypted_pointers == []

    def test_create_vault_custom_kdf_params(self, temp_vault_dir):
        """Test creating vault with custom KDF parameters."""
        vault = Vault("test_vault1", TIME=3, MEMORY=131072, PARALLELISM=2, load=False)
        assert vault.vault_config.kdf_params.time_cost == 3
        assert vault.vault_config.kdf_params.memory_cost == 131072
        assert vault.vault_config.kdf_params.parallelism == 2

    def test_vault_update(self, temp_vault_dir):
        """Test saving vault configuration."""
        vault = Vault("test_vault1", load=False)
        vault.update_vault()
        
        # Verify file was created
        vault_file = os.path.join(temp_vault_dir, "test_vault1", "vault_config.json")
        assert os.path.isfile(vault_file)
        
        # Verify file contains valid JSON
        with open(vault_file, "r") as f:
            data = json.load(f)
        assert data["id"] == "test_vault1"

    def test_vault_load(self, temp_vault_dir):
        """Test loading an existing vault."""
        # Create and save a vault
        vault1 = Vault("test_vault1", load=False)
        vault1.update_vault()
        
        # Load it back (load=True by default)
        vault2 = Vault("test_vault1", load=True)
        assert vault2.vault_config.id == "test_vault1"
        assert vault2.vault_config.salt == vault1.vault_config.salt

    def test_load_nonexistent_vault(self, temp_vault_dir):
        """Test loading a nonexistent vault creates a new one."""
        vault = Vault("nonexistent", load=True)
        assert vault.vault_config.id == "nonexistent"
        assert isinstance(vault.vault_config.salt, bytes)

    def test_add_pointer(self, temp_vault_dir):
        """Test adding a pointer to vault."""
        vault = Vault("test_vault1", load=False)
        master_password = "test_password"
        
        vault.updated_pointer(master_password, "ptr1", "user1", "pass1")
        
        assert len(vault.vault_config.encrypted_pointers) == 1
        assert vault.vault_config.encrypted_pointers[0].id == "ptr1"
        
        # Verify pointer file was created
        pointer_file = os.path.join(temp_vault_dir, "test_vault1", "ptr1.ptr")
        assert os.path.isfile(pointer_file)

    def test_add_duplicate_pointer(self, temp_vault_dir):
        """Test adding a pointer with duplicate ID raises error."""
        vault = Vault("test_vault1", load=False)
        master_password = "test_password"
        
        vault.updated_pointer(master_password, "ptr1", "user1", "pass1")
        
        with pytest.raises(ValueError):
            vault.updated_pointer(master_password, "ptr1", "user2", "pass2")

    def test_get_pointer(self, temp_vault_dir):
        """Test retrieving and decrypting pointer."""
        vault = Vault("test_vault1", load=False)
        master_password = "test_password"
        
        vault.updated_pointer(master_password, "ptr1", "user1", "pass1")
        vault.update_vault()
        
        credentials = vault.get_pointer(master_password, "ptr1")
        assert credentials.username == "user1"
        assert credentials.password == "pass1"

    def test_get_nonexistent_pointer(self, temp_vault_dir):
        """Test getting nonexistent pointer raises error."""
        vault = Vault("test_vault1", load=False)
        master_password = "test_password"
        
        with pytest.raises(ValueError):
            vault.get_pointer(master_password, "nonexistent")

    def test_get_pointer_wrong_password(self, temp_vault_dir):
        """Test getting pointer with wrong password fails."""
        vault = Vault("test_vault1", load=False)
        master_password = "test_password"
        wrong_password = "wrong_password"
        
        vault.updated_pointer(master_password, "ptr1", "user1", "pass1")
        vault.update_vault()
        
        # Should fail or return garbage (depends on crypto)
        with pytest.raises(Exception):
            credentials = vault.get_pointer(wrong_password, "ptr1")

    def test_list_pointers(self, temp_vault_dir):
        """Test listing pointers in vault."""
        vault = Vault("test_vault1", load=False)
        master_password = "test_password"
        
        vault.updated_pointer(master_password, "ptr1", "user1", "pass1")
        vault.updated_pointer(master_password, "ptr2", "user2", "pass2")
        
        pointers = vault.list_pointers()
        assert len(pointers) == 2
        assert "ptr1" in pointers
        assert "ptr2" in pointers

    def test_list_vaults(self, temp_vault_dir):
        """Test listing all vaults."""
        vault1 = Vault("vault1", load=False)
        vault1.update_vault()
        vault2 = Vault("vault2", load=False)
        vault2.update_vault()
        
        vaults = Vault.list_vaults()
        assert "vault1" in vaults
        assert "vault2" in vaults

    def test_vault_roundtrip(self, temp_vault_dir):
        """Test full roundtrip: create, save, load, verify."""
        # Create and populate vault
        vault1 = Vault("test_vault1", load=False)
        master_password = "my_secure_password"
        
        vault1.updated_pointer(master_password, "ptr1", "alice", "secret123")
        vault1.updated_pointer(master_password, "ptr2", "bob", "password456")
        vault1.update_vault()
        
        # Load vault
        vault2 = Vault("test_vault1", load=True)
        
        # Verify pointers
        assert len(vault2.vault_config.encrypted_pointers) == 2
        
        # Retrieve credentials
        cred1 = vault2.get_pointer(master_password, "ptr1")
        cred2 = vault2.get_pointer(master_password, "ptr2")
        
        assert cred1.username == "alice"
        assert cred1.password == "secret123"
        assert cred2.username == "bob"
        assert cred2.password == "password456"

    def test_atomic_write_bytes(self, temp_vault_dir):
        """Test atomic write function."""
        path = os.path.join(temp_vault_dir, "test", "file.bin")
        data = b"test data"
        
        Vault.atomic_write_bytes(path, data)
        
        assert os.path.isfile(path)
        with open(path, "rb") as f:
            written = f.read()
        assert written == data
