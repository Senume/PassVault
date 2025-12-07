class VaultError(Exception):
    """Base vault error."""


class DecryptionError(VaultError):
    """Raised when vault decryption or authentication fails."""
    pass
