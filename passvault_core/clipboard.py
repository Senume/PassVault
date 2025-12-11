"""
Clipboard management module.

Provides functionality to copy data to and from system clipboard
with manual clearing control.
"""

import subprocess
import threading
import logging
from typing import Optional
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class ClipboardError(Exception):
    """Raised when clipboard operations fail."""
    pass


class ClipboardManager:
    """
    Manages clipboard operations with thread-safe access.
    
    Provides thread-safe copy, clear, and read operations for
    system clipboard access. All clearing is manual.
    """

    def __init__(self):
        """
        Initialize the clipboard manager.
        
        Raises:
            ValueError: If initialization fails.
        """
        self._lock = threading.RLock()
        self._clipboard_content: Optional[str] = None
        self._is_managed = False

    def copy(self, text: str) -> None:
        """
        Copy text to clipboard.
        
        Args:
            text: The text to copy to clipboard.
        
        Raises:
            ClipboardError: If clipboard operation fails.
            ValueError: If text is None or empty.
        """
        if not text or not isinstance(text, str):
            raise ValueError("Text must be a non-empty string")
        
        with self._lock:
            try:
                # Copy to system clipboard
                self._write_to_clipboard(text)
                self._clipboard_content = text
                self._is_managed = True
                
                logger.info(f"Copied {len(text)} characters to clipboard")
                
            except Exception as e:
                self._is_managed = False
                logger.error(f"Failed to copy to clipboard: {e}")
                raise ClipboardError(f"Failed to copy to clipboard: {e}") from e

    def clear(self) -> None:
        """
        Manually clear the clipboard.
        
        Raises:
            ClipboardError: If clipboard clear operation fails.
        """
        with self._lock:
            try:
                # Clear clipboard
                self._write_to_clipboard("")
                self._clipboard_content = None
                self._is_managed = False
                
                logger.info("Clipboard cleared")
                
            except Exception as e:
                logger.error(f"Failed to clear clipboard: {e}")
                raise ClipboardError(f"Failed to clear clipboard: {e}") from e

    def is_managed(self) -> bool:
        """
        Check if clipboard is currently managed (content copied by this manager).
        
        Returns:
            True if clipboard content is managed, False otherwise.
        """
        with self._lock:
            return self._is_managed

    @contextmanager
    def temporary_copy(self, text: str):
        """
        Context manager for temporary clipboard operations.
        
        Ensures clipboard is cleared when exiting the context.
        
        Args:
            text: Text to copy to clipboard.
        
        Example:
            with clipboard_manager.temporary_copy("password123"):
                # clipboard contains "password123"
                pass
            # clipboard is now cleared
        """
        try:
            self.copy(text)
            yield
        finally:
            self.clear()

    @staticmethod
    def _write_to_clipboard(text: str) -> None:
        """
        Write text to system clipboard using xclip.
        
        Args:
            text: The text to write.
        
        Raises:
            ClipboardError: If clipboard write fails.
        """
        try:
            process = subprocess.Popen(
                ["xclip", "-selection", "clipboard"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            # Use input parameter and timeout to avoid hanging
            stdout, stderr = process.communicate(
                input=text.encode("utf-8"),
                timeout=1
            )
            
            if process.returncode != 0:
                raise ClipboardError(f"xclip failed: {stderr.decode('utf-8', errors='ignore')}")
                
        except subprocess.TimeoutExpired:
            process.kill()
        except FileNotFoundError:
            raise ClipboardError(
                "xclip not found. Install it with: sudo apt-get install xclip"
            )
        except Exception as e:
            raise ClipboardError(f"Clipboard write failed: {e}") from e

    @staticmethod
    def _read_from_clipboard() -> str:
        """
        Read text from system clipboard using xclip.
        
        Returns:
            The clipboard content as a string.
        
        Raises:
            ClipboardError: If clipboard read fails.
        """
        try:
            process = subprocess.Popen(
                ["xclip", "-selection", "clipboard", "-o"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            stdout, stderr = process.communicate(timeout=5)
            
            if process.returncode != 0:
                raise ClipboardError(f"xclip failed: {stderr.decode('utf-8', errors='ignore')}")
            
            return stdout.decode("utf-8")
                
        except subprocess.TimeoutExpired:
            process.kill()
            raise ClipboardError("xclip operation timed out (5 seconds)")
        except FileNotFoundError:
            raise ClipboardError(
                "xclip not found. Install it with: sudo apt-get install xclip"
            )
        except Exception as e:
            raise ClipboardError(f"Clipboard read failed: {e}") from e


# Global clipboard manager instance
_clipboard_manager: Optional[ClipboardManager] = None


def get_clipboard_manager() -> ClipboardManager:
    """
    Get or create the global clipboard manager instance.
    
    Returns:
        The global ClipboardManager instance.
    """
    global _clipboard_manager
    if _clipboard_manager is None:
        _clipboard_manager = ClipboardManager()
    return _clipboard_manager
