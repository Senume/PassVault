import json
from pydantic import BaseModel
from typing import List, Optional

class CredentialSchema(BaseModel):
    username: str
    password: str

    def to_dict(self) -> dict:
        return {
            "username": self.username,
            "password": self.password,
        }
    
    def to_str(self) -> str:
        return json.dumps(self.to_dict())
    
    @classmethod
    def from_str(cls, data: str):
        """Create a CredentialSchema from a JSON string."""
        dict_data = json.loads(data)
        return cls(**dict_data)

class KDFParamsSchema(BaseModel):
    time_cost: int = 2
    memory_cost: int = 65536
    parallelism: int = 1

    def to_dict(self) -> dict:
        return {
            "time_cost": self.time_cost,
            "memory_cost": self.memory_cost,
            "parallelism": self.parallelism,
        }

class PointerSchema(BaseModel):
    id: str
    vault_id: str
    nonce: bytes

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "vault_id": self.vault_id,
            "nonce": self.nonce,
        }

    @classmethod
    def from_dict(cls, data: dict):
        """Create a PointerSchema from a plain dict.

        This helper prefers the Pydantic v2 API (`model_validate`) when
        available, falls back to v1 (`parse_obj`) and finally to direct
        construction. It will raise the appropriate Pydantic
        ValidationError on invalid input.
        """
        # Pydantic v2
        if hasattr(cls, "model_validate"):
            return cls.model_validate(data)
        # Pydantic v1
        if hasattr(cls, "parse_obj"):
            return cls.parse_obj(data)
        # Fallback
        return cls(**data)

class VaultSchema(BaseModel):
    id: str
    salt: bytes
    encrypted_pointers: List[Optional[PointerSchema]] = []
    kdf_params: KDFParamsSchema = KDFParamsSchema()

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "salt": self.salt,
            "encrypted_pointers": [p.to_dict() if p else None for p in self.encrypted_pointers],
            "kdf_params": self.kdf_params.to_dict(),
        }
    
    @classmethod
    def from_dict(self, data: dict):
        """Create a VaultSchema from a plain dict.

        This helper prefers the Pydantic v2 API (`model_validate`) when
        available, falls back to v1 (`parse_obj`) and finally to direct
        construction. It will raise the appropriate Pydantic
        ValidationError on invalid input.
        """
        # Pydantic v2
        if hasattr(self, "model_validate"):
            return self.model_validate(data)
        # Pydantic v1
        if hasattr(self, "parse_obj"):
            return self.parse_obj(data)
        # Fallback
        return self(**data)