"""Logger configuration for PassVault."""

import os
import logging
from pathlib import Path

_SYSTEM_LOG = Path("/var/log/passvault/passvault.log")
_USER_LOG = Path.home() / ".local" / "state" / "passvault" / "passvault.log"


def _resolve_log_path() -> Path:
    """Return the log file path: env var → /var/log (if writable) → ~/.local/state fallback."""
    env = os.getenv("PASSVAULT_LOG")
    if env:
        return Path(env)
    try:
        _SYSTEM_LOG.parent.mkdir(parents=True, exist_ok=True)
        return _SYSTEM_LOG
    except PermissionError:
        return _USER_LOG


def setup_logger(name: str, log_file: str | None = None) -> logging.Logger:
    """
    Setup a logger with file logging.

    Log location (in priority order):
      1. ``log_file`` argument
      2. ``PASSVAULT_LOG`` environment variable
      3. /var/log/passvault/passvault.log  (requires write permission)
      4. ~/.local/state/passvault/passvault.log  (user fallback)

    Args:
        name: Logger name
        log_file: Explicit path override.

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    resolved = Path(log_file) if log_file else _resolve_log_path()
    resolved.parent.mkdir(parents=True, exist_ok=True)

    file_handler = logging.FileHandler(resolved)
    file_handler.setLevel(logging.DEBUG)

    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(formatter)

    if not logger.handlers:
        logger.addHandler(file_handler)

    return logger
