"""Add Vault panel — create a new vault with master password confirmation."""

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.message import Message
from textual.widgets import Label, Input, Static

from utils import logger


class AddVaultPanel(Vertical):
    """Panel for creating a new vault with master password confirmation."""

    can_focus = True

    BINDINGS = [("escape", "cancel", "Cancel")]

    def compose(self) -> ComposeResult:
        with Vertical(id="add-vault-inner"):
            yield Label("Create New Vault", id="add-vault-label")
            yield Label("Vault Name:", id="vault-name-label")
            yield Input(id="new-vault-name-input", placeholder="Enter vault name")
            yield Label("Master Password:", id="vault-master-password-label")
            yield Input(id="new-vault-password-input", placeholder="Enter master password", password=True)
            yield Label("Confirm Password:", id="vault-confirm-label")
            yield Input(id="new-vault-confirm-input", placeholder="Confirm master password", password=True)
            yield Static("", id="add-vault-error")

    def on_mount(self) -> None:
        self.query_one("#new-vault-name-input", Input).focus()
        logger.debug("AddVaultPanel mounted")

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.control.id == "new-vault-name-input":
            self.query_one("#new-vault-password-input", Input).focus()
        elif event.control.id == "new-vault-password-input":
            self.query_one("#new-vault-confirm-input", Input).focus()
        elif event.control.id == "new-vault-confirm-input":
            self._submit()

    def _submit(self) -> None:
        name = self.query_one("#new-vault-name-input", Input).value.strip()
        password = self.query_one("#new-vault-password-input", Input).value
        confirm = self.query_one("#new-vault-confirm-input", Input).value
        error = self.query_one("#add-vault-error", Static)

        if not name:
            error.update("Vault name cannot be empty")
            return
        if not password:
            error.update("Password cannot be empty")
            return
        if password != confirm:
            error.update("Passwords do not match")
            self.query_one("#new-vault-confirm-input", Input).clear()
            return

        self.post_message(self.VaultCreated(name=name, master_password=password))

    def action_cancel(self) -> None:
        logger.debug("AddVaultPanel cancelled")
        self.remove()

    class VaultCreated(Message):
        """Message when a new vault should be created."""
        def __init__(self, name: str, master_password: str) -> None:
            self.name = name
            self.master_password = master_password
            super().__init__()
