"""Credential detail panel — shown after unlocking a credential."""

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.message import Message
from textual.widgets import Label, Static, Rule

from passvault_core.clipboard import get_clipboard_manager
from utils import logger


class CredentialPanel(Vertical):
    """Panel to display credential details - uses Vertical for focusability."""

    can_focus = True

    BINDINGS = [
        ("escape", "close_panel", "Close"),
        ("c", "copy_credentials", "Copy Username"),
        ("p", "copy_password", "Copy Password"),
    ]

    def __init__(self, username: str = "", password: str = "", pointer_id: str = "", **kwargs):
        super().__init__(**kwargs)
        self.username = username
        self.password = password
        self.pointer_id = pointer_id

    def on_mount(self) -> None:
        self.focus()
        logger.debug("Credential panel mounted and focused")

    def compose(self) -> ComposeResult:
        yield Label("🔓 Credential Unlocked", id="credential-label")
        yield Label(self.pointer_id, id="pointer-label")
        yield Rule(id="credential-rule")
        yield Label("Username", classes="credential-field-label")
        yield Label(self.username, classes="credential-field-value")
        yield Label("Password", classes="credential-field-label")
        yield Label("●" * len(self.password), classes="credential-field-value", id="password-display")
        yield Rule(id="credential-rule-bottom")
        yield Label(
            "\\[[bold cyan]c[/]] Copy Username  "
            "\\[[bold cyan]p[/]] Copy Password  "
            "\\[[bold cyan]ESC[/]] Close",
            id="credential-help",
        )

    def action_close_panel(self) -> None:
        logger.debug("action_close_panel called")
        self.post_message(self.CredentialClosed())

    def action_copy_credentials(self) -> None:
        logger.debug("action_copy_credentials called")
        try:
            get_clipboard_manager().copy(self.username)
            self.app.notify("Username copied to clipboard")
        except Exception as e:
            logger.error(f"Failed to copy username: {e}")
            self.app.notify(f"Failed to copy: {e}", severity="error")

    def action_copy_password(self) -> None:
        logger.debug("action_copy_password called")
        try:
            get_clipboard_manager().copy(self.password)
            self.app.notify("Password copied to clipboard")
        except Exception as e:
            logger.error(f"Failed to copy password: {e}")
            self.app.notify(f"Failed to copy: {e}", severity="error")

    class CredentialClosed(Message):
        """Message when credential panel is closed."""
        pass
