"""Master password entry panel — shared by view and add-credential flows."""

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.message import Message
from textual.widgets import Label, Input, Static

from utils import logger


class MasterPasswordPanel(Static):
    """Modal panel for entering master password."""

    BINDINGS = [
        ("escape", "cancel_password", "Cancel"),
    ]

    def compose(self) -> ComposeResult:
        with Vertical(id="password-panel"):
            yield Label("Enter Master Password", id="password-label")
            yield Input(id="master-password-input", password=True)
            yield Static("", id="password-error")

    def on_mount(self) -> None:
        self.app.set_focus(self.query_one("#master-password-input", Input))
        logger.debug("Master password panel mounted, input focused.")

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.control.id == "master-password-input":
            password = event.value
            logger.debug(f"Password entered: {len(password)} chars")
            if not password:
                self.query_one("#password-error", Static).update("Password cannot be empty")
                return
            self.post_message(self.PasswordConfirmed(password))

    def action_cancel_password(self) -> None:
        self.post_message(self.PasswordCancelled())

    class PasswordConfirmed(Message):
        """Message when password is confirmed."""
        def __init__(self, password: str) -> None:
            self.password = password
            super().__init__()

    class PasswordCancelled(Message):
        """Message when password entry is cancelled."""
        pass
