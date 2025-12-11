"""
Unit tests for the clipboard module.

Tests cover:
- Basic copy and clear operations
- Error handling
- Thread safety
- Context manager functionality
"""

import pytest
import threading
from unittest.mock import patch, MagicMock

from passvault_core.clipboard import (
    ClipboardManager,
    ClipboardError,
    get_clipboard_manager,
)


# Note: Timeout-related tests have been removed as the module now uses
# manual clearing only with subprocess timeout protection.




class TestClipboardCopyAndClear:
    """Tests for copy and clear operations."""

    @pytest.fixture
    def manager(self):
        """Provide a ClipboardManager instance."""
        return ClipboardManager()

    @patch("passvault_core.clipboard.ClipboardManager._write_to_clipboard")
    def test_copy_success(self, mock_write, manager):
        """Test successful copy operation."""
        mock_write.return_value = None
        manager.copy("test_password")
        
        mock_write.assert_called_once_with("test_password")
        assert manager.is_managed() is True

    @patch("passvault_core.clipboard.ClipboardManager._write_to_clipboard")
    def test_copy_empty_string(self, mock_write, manager):
        """Test that empty string copy raises ValueError."""
        with pytest.raises(ValueError, match="non-empty string"):
            manager.copy("")
        
        mock_write.assert_not_called()

    @patch("passvault_core.clipboard.ClipboardManager._write_to_clipboard")
    def test_copy_none_raises_error(self, mock_write, manager):
        """Test that None copy raises ValueError."""
        with pytest.raises(ValueError, match="non-empty string"):
            manager.copy(None)
        
        mock_write.assert_not_called()

    @patch("passvault_core.clipboard.ClipboardManager._write_to_clipboard")
    def test_copy_write_fails(self, mock_write, manager):
        """Test that write failure raises ClipboardError."""
        mock_write.side_effect = Exception("Write failed")
        
        with pytest.raises(ClipboardError):
            manager.copy("password")
        
        assert manager.is_managed() is False

    @patch("passvault_core.clipboard.ClipboardManager._write_to_clipboard")
    def test_clear_success(self, mock_write, manager):
        """Test successful clear operation."""
        mock_write.return_value = None
        manager.copy("password")
        assert manager.is_managed() is True
        
        manager.clear()
        
        # Should be called twice: once for copy, once for clear
        assert mock_write.call_count == 2
        mock_write.assert_called_with("")
        assert manager.is_managed() is False

    @patch("passvault_core.clipboard.ClipboardManager._write_to_clipboard")
    def test_clear_write_fails(self, mock_write, manager):
        """Test that clear failure raises ClipboardError."""
        mock_write.side_effect = Exception("Clear failed")
        
        with pytest.raises(ClipboardError):
            manager.clear()


class TestContextManager:
    """Tests for context manager functionality."""

    @pytest.fixture
    def manager(self):
        """Provide a ClipboardManager instance."""
        return ClipboardManager()

    @patch("passvault_core.clipboard.ClipboardManager._write_to_clipboard")
    def test_temporary_copy_context(self, mock_write, manager):
        """Test temporary_copy context manager."""
        mock_write.return_value = None
        
        with manager.temporary_copy("secret"):
            assert manager.is_managed() is True
            mock_write.assert_called_with("secret")
        
        # After context, clipboard should be cleared
        assert manager.is_managed() is False

    @patch("passvault_core.clipboard.ClipboardManager._write_to_clipboard")
    def test_temporary_copy_clears_on_exception(self, mock_write, manager):
        """Test that temporary_copy clears clipboard even on exception."""
        mock_write.return_value = None
        
        try:
            with manager.temporary_copy("secret"):
                raise ValueError("Test error")
        except ValueError:
            pass
        
        # Clipboard should still be cleared
        assert manager.is_managed() is False


class TestGlobalManager:
    """Tests for global clipboard manager."""

    @patch("passvault_core.clipboard.ClipboardManager._write_to_clipboard")
    def test_get_clipboard_manager_singleton(self, mock_write):
        """Test that get_clipboard_manager returns singleton."""
        mock_write.return_value = None
        
        manager1 = get_clipboard_manager()
        manager2 = get_clipboard_manager()
        
        assert manager1 is manager2


class TestThreadSafety:
    """Tests for thread safety."""

    @pytest.fixture
    def manager(self):
        """Provide a ClipboardManager instance."""
        return ClipboardManager()

    @patch("passvault_core.clipboard.ClipboardManager._write_to_clipboard")
    def test_concurrent_copy_operations(self, mock_write, manager):
        """Test that concurrent operations are thread-safe."""
        mock_write.return_value = None
        errors = []
        
        def copy_operation(text):
            try:
                manager.copy(text)
            except Exception as e:
                errors.append(e)
        
        threads = [
            threading.Thread(target=copy_operation, args=(f"password{i}",))
            for i in range(5)
        ]
        
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        assert len(errors) == 0


class TestErrorHandling:
    """Tests for error handling."""

    @pytest.fixture
    def manager(self):
        """Provide a ClipboardManager instance."""
        return ClipboardManager()

    @patch("passvault_core.clipboard.subprocess.Popen")
    def test_xclip_not_found(self, mock_popen, manager):
        """Test handling of missing xclip."""
        mock_popen.side_effect = FileNotFoundError("xclip not found")
        
        with pytest.raises(ClipboardError, match="xclip not found"):
            manager.copy("password")

    @patch("passvault_core.clipboard.subprocess.Popen")
    def test_xclip_command_fails(self, mock_popen, manager):
        """Test handling of xclip command failure."""
        mock_process = MagicMock()
        mock_process.returncode = 1
        mock_process.communicate.return_value = (b"", b"Error message")
        mock_popen.return_value = mock_process
        
        with pytest.raises(ClipboardError, match="xclip failed"):
            manager.copy("password")








class TestClipboardCopyAndClear:
    """Tests for copy and clear operations."""

    @pytest.fixture
    def manager(self):
        """Provide a ClipboardManager instance."""
        return ClipboardManager()

    @patch("passvault_core.clipboard.ClipboardManager._write_to_clipboard")
    def test_copy_success(self, mock_write, manager):
        """Test successful copy operation."""
        mock_write.return_value = None
        manager.copy("test_password")
        
        mock_write.assert_called_once_with("test_password")
        assert manager.is_managed() is True

    @patch("passvault_core.clipboard.ClipboardManager._write_to_clipboard")
    def test_copy_empty_string(self, mock_write, manager):
        """Test that empty string copy raises ValueError."""
        with pytest.raises(ValueError, match="non-empty string"):
            manager.copy("")
        
        mock_write.assert_not_called()

    @patch("passvault_core.clipboard.ClipboardManager._write_to_clipboard")
    def test_copy_none_raises_error(self, mock_write, manager):
        """Test that None copy raises ValueError."""
        with pytest.raises(ValueError, match="non-empty string"):
            manager.copy(None)
        
        mock_write.assert_not_called()

    @patch("passvault_core.clipboard.ClipboardManager._write_to_clipboard")
    def test_copy_write_fails(self, mock_write, manager):
        """Test that write failure raises ClipboardError."""
        mock_write.side_effect = Exception("Write failed")
        
        with pytest.raises(ClipboardError):
            manager.copy("password")
        
        assert manager.is_managed() is False

    @patch("passvault_core.clipboard.ClipboardManager._write_to_clipboard")
    def test_clear_success(self, mock_write, manager):
        """Test successful clear operation."""
        mock_write.return_value = None
        manager.copy("password")
        assert manager.is_managed() is True
        
        manager.clear()
        
        # Should be called twice: once for copy, once for clear
        assert mock_write.call_count == 2
        mock_write.assert_called_with("")
        assert manager.is_managed() is False

    @patch("passvault_core.clipboard.ClipboardManager._write_to_clipboard")
    def test_clear_write_fails(self, mock_write, manager):
        """Test that clear failure raises ClipboardError."""
        mock_write.side_effect = Exception("Clear failed")
        
        with pytest.raises(ClipboardError):
            manager.clear()


class TestContextManager:
    """Tests for context manager functionality."""

    @pytest.fixture
    def manager(self):
        """Provide a ClipboardManager instance."""
        return ClipboardManager()

    @patch("passvault_core.clipboard.ClipboardManager._write_to_clipboard")
    def test_temporary_copy_context(self, mock_write, manager):
        """Test temporary_copy context manager."""
        mock_write.return_value = None
        
        with manager.temporary_copy("secret"):
            assert manager.is_managed() is True
            mock_write.assert_called_with("secret")
        
        # After context, clipboard should be cleared
        assert manager.is_managed() is False

    @patch("passvault_core.clipboard.ClipboardManager._write_to_clipboard")
    def test_temporary_copy_clears_on_exception(self, mock_write, manager):
        """Test that temporary_copy clears clipboard even on exception."""
        mock_write.return_value = None
        
        try:
            with manager.temporary_copy("secret"):
                raise ValueError("Test error")
        except ValueError:
            pass
        
        # Clipboard should still be cleared
        assert manager.is_managed() is False


class TestGlobalManager:
    """Tests for global clipboard manager."""

    @patch("passvault_core.clipboard.ClipboardManager._write_to_clipboard")
    def test_get_clipboard_manager_singleton(self, mock_write):
        """Test that get_clipboard_manager returns singleton."""
        mock_write.return_value = None
        
        manager1 = get_clipboard_manager()
        manager2 = get_clipboard_manager()
        
        assert manager1 is manager2


class TestThreadSafety:
    """Tests for thread safety."""

    @pytest.fixture
    def manager(self):
        """Provide a ClipboardManager instance."""
        return ClipboardManager()

    @patch("passvault_core.clipboard.ClipboardManager._write_to_clipboard")
    def test_concurrent_copy_operations(self, mock_write, manager):
        """Test that concurrent operations are thread-safe."""
        mock_write.return_value = None
        errors = []
        
        def copy_operation(text):
            try:
                manager.copy(text)
            except Exception as e:
                errors.append(e)
        
        threads = [
            threading.Thread(target=copy_operation, args=(f"password{i}",))
            for i in range(5)
        ]
        
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        assert len(errors) == 0


class TestErrorHandling:
    """Tests for error handling."""

    @pytest.fixture
    def manager(self):
        """Provide a ClipboardManager instance."""
        return ClipboardManager()

    @patch("passvault_core.clipboard.subprocess.Popen")
    def test_xclip_not_found(self, mock_popen, manager):
        """Test handling of missing xclip."""
        mock_popen.side_effect = FileNotFoundError("xclip not found")
        
        with pytest.raises(ClipboardError, match="xclip not found"):
            manager.copy("password")

    @patch("passvault_core.clipboard.subprocess.Popen")
    def test_xclip_command_fails(self, mock_popen, manager):
        """Test handling of xclip command failure."""
        mock_process = MagicMock()
        mock_process.returncode = 1
        mock_process.communicate.return_value = (b"", b"Error message")
        mock_popen.return_value = mock_process
        
        with pytest.raises(ClipboardError, match="xclip failed"):
            manager.copy("password")
