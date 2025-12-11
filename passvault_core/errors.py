"""Custom exceptions for passvault_core."""


class DecryptionError(Exception):
    """Raised when decryption fails or authentication check fails."""
    pass


class ClipboardError(Exception):
    """Raised when clipboard operations fail."""
    pass
