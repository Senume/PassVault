import os,json, base64, tempfile
from passvault_core.crypto import derive_key, encrypt, decrypt
from passvault_core.storage import encode_string_to_base64_bytes, decode_base64_bytes_to_string

from passvault_core.schema import VaultSchema, KDFParamsSchema, PointerSchema, CredentialSchema


class Vault:

    path = 'data'

    def __init__(self, id: str, TIME: int = None, MEMORY: int = None, PARALLELISM: int = None, load: bool = True):
        vault_config: VaultSchema = VaultSchema(id=id, salt=os.urandom(32))

        if TIME is not None and MEMORY is not None and PARALLELISM is not None:
            vault_config.kdf_params = KDFParamsSchema(time_cost=TIME, memory_cost=MEMORY, parallelism=PARALLELISM)
        self.vault_config = vault_config

        # auto-load existing vault config if requested and file exists
        if load:
            cfg_path = os.path.join(Vault.path, id, "vault_config.json")
            if os.path.exists(cfg_path):
                self.load(id)

    def load(self, id):
        path = os.path.join(Vault.path, id, "vault_config.json")
        with open(path, "r", encoding="utf-8") as f:
            vault_data = json.load(f)

        def _decode_bytes(obj):
            if isinstance(obj, dict):
                out = {}
                for k, v in obj.items():
                    if k in ("salt", "nonce") and isinstance(v, str):
                        out[k] = base64.b64decode(v.encode("ascii"))
                    else:
                        out[k] = _decode_bytes(v)
                return out
            if isinstance(obj, list):
                return [_decode_bytes(x) for x in obj]
            return obj

        vault_data = _decode_bytes(vault_data)
        self.vault_config = VaultSchema.from_dict(vault_data)


    def update_vault(self):
        path = os.path.join(Vault.path, self.vault_config.id, "vault_config.json")

        def _encode_bytes(obj):
            if isinstance(obj, bytes):
                return base64.b64encode(obj).decode("ascii")
            if isinstance(obj, dict):
                return {k: _encode_bytes(v) for k, v in obj.items()}
            if isinstance(obj, list):
                return [_encode_bytes(x) for x in obj]
            return obj

        plain = self.vault_config.to_dict()
        serializable = _encode_bytes(plain)
        json_bytes = json.dumps(serializable, indent=2).encode("utf-8")
        Vault.atomic_write_bytes(path, json_bytes)


    def updated_pointer(self, master_password: str, pointer_id: str, username: str, password: str):
        
        if any([p.id for p in self.vault_config.encrypted_pointers if p.id == pointer_id]):
            raise ValueError(f"Pointer with id {pointer_id} already exists in vault {self.vault_config.id}")
        credentials = CredentialSchema(password=password, username=username)
        master_hash_key = derive_key(password=master_password, salt=self.vault_config.salt, **self.vault_config.kdf_params.to_dict())
        nonce, encrypted_data = encrypt(key=master_hash_key, plaintext=encode_string_to_base64_bytes(credentials.to_str()))

        Vault.atomic_write_bytes(os.path.join(Vault.path, self.vault_config.id, f"{pointer_id}.ptr"), encrypted_data)
        pointer = PointerSchema(id=pointer_id, vault_id=self.vault_config.id, nonce=nonce)
        self.vault_config.encrypted_pointers.append(pointer)
    
    def get_pointer(self, master_password: str, pointer_id: str) -> CredentialSchema:
        pointer = next((p for p in self.vault_config.encrypted_pointers if p.id == pointer_id), None)
        if pointer is None:
            raise ValueError(f"Pointer with id {pointer_id} does not exist in vault {self.vault_config.id}")
        with open(os.path.join(Vault.path, self.vault_config.id, f"{pointer_id}.ptr"), "rb") as f:
            encrypted_data = f.read()
        master_hash_key = derive_key(password=master_password, salt=self.vault_config.salt, **self.vault_config.kdf_params.to_dict())
        decrypted_data = decrypt(key=master_hash_key, nonce=pointer.nonce, ciphertext=encrypted_data)
        credentials_str = decode_base64_bytes_to_string(decrypted_data)
        credentials = CredentialSchema.from_str(data=credentials_str)
        return credentials
    

    def list_pointers(self) -> list[str]:
        return [p.id for p in self.vault_config.encrypted_pointers]
    
    @staticmethod
    def list_vaults() -> list[str]:
        return os.listdir(Vault.path)
    
    @classmethod
    def atomic_write_bytes(cls, path: str, data: bytes):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with tempfile.NamedTemporaryFile(dir=os.path.dirname(path), delete=False) as tf:
            tf.write(data)
            tmp = tf.name
        os.replace(tmp, path)