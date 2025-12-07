"""Clipboard helpers for PassVault (core).

Provides a small abstraction to copy secrets to the system clipboard and
clear them after a timeout. It attempts to use the desktop toolchain in
this order: wl-copy (Wayland), xclip/xsel (X11). If none are available it
raises RuntimeError.

This module keeps dependencies minimal by shelling out to existing tools
commonly present on Linux systems. Clearing is implemented with a
background Timer so callers can continue execution.
"""
from __future__ import annotations

import shutil
import subprocess
import threading

DEFAULT_CLEAR_SECONDS = 15


class ClipboardUnavailable(RuntimeError):
    pass


def _has_command(cmd: str) -> bool:
    return shutil.which(cmd) is not None


def _set_clipboard_via_cmd(text: str) -> None:
    """Try to set the clipboard using available command-line tools."""
    # Prefer Wayland
    if _has_command("wl-copy"):
        p = subprocess.Popen(["wl-copy"], stdin=subprocess.PIPE)
        p.communicate(input=text.encode("utf-8"))
        return
    # Try xclip
    if _has_command("xclip"):
        p = subprocess.Popen(["xclip", "-selection", "clipboard"], stdin=subprocess.PIPE)
        p.communicate(input=text.encode("utf-8"))
        return
    # Try xsel
    if _has_command("xsel"):
        p = subprocess.Popen(["xsel", "--clipboard", "--input"], stdin=subprocess.PIPE)
        p.communicate(input=text.encode("utf-8"))
        return
    raise ClipboardUnavailable("No clipboard utility found (wl-copy, xclip or xsel)")


def _clear_clipboard_via_cmd() -> None:
    try:
        _set_clipboard_via_cmd("")
    except ClipboardUnavailable:
        # If no command is available we simply ignore; nothing to clear.
        pass


def copy_and_clear(text: str, timeout: int = DEFAULT_CLEAR_SECONDS) -> threading.Timer:
    """Copy `text` to the system clipboard and arrange to clear it after `timeout` seconds.

    Returns the Timer object so the caller may cancel it if needed.
    Raises ClipboardUnavailable if no backend is available.
    """
    # Try to write the clipboard now.
    _set_clipboard_via_cmd(text)

    timer = threading.Timer(timeout, _clear_clipboard_via_cmd)
    timer.daemon = True
    timer.start()
    return timer


__all__ = ["copy_and_clear", "ClipboardUnavailable"]
