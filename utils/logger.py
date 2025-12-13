"""Logger configuration for PassVault."""

import logging
from pathlib import Path


def setup_logger(name: str, log_file: str | None = None) -> logging.Logger:
    """
    Setup a logger with file logging.
    
    Args:
        name: Logger name (usually __name__)
        log_file: Path to log file. If None, uses default location.
    
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    
    # Default log file location
    if log_file is None:
        log_dir = Path(__file__).parent.parent
        log_file = log_dir / "passvault.log"
    else:
        log_file = Path(log_file)
    
    # Create log directory if it doesn't exist
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    # File handler
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)
    
    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(formatter)
    
    # Add handler to logger (avoid duplicates)
    if not logger.handlers:
        logger.addHandler(file_handler)
    
    return logger
