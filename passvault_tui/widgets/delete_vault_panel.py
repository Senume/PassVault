"""Delete Vault panel — confirm deletion by typing the vault name."""

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.message import Message
from textual.widgets import Label, Input, Static

from utils import logger


class DeleteVaultPanel(Vertical):
    """Panel to confirm vault deletion by retyping the vault name."""

    can_focus = True

    BINDINGS = [("escape", "cancel", "Cancel")]

    def __init__(self, vault_id: str, **kwargs):
        self.vault_id = vault_id
        super().__init__(**kwargs)

    def compose(self) -> ComposeResult:
        with Vertical(id="delete-vault-inner"):
            yield Label("⚠  Delete Vault", id="delete-vault-label")
            yield Label(
                f"Type [bold red]{self.vault_id}[/bold red] to confirm permanent deletion:",
                id="delete-vault-warning",
            )
            yield Input(id="delete-confirm-input", placeholder=self.vault_id)
            yield Static("", id="delete-vault-error")
            yield Static(
                "\\[[bold cyan]Enter[/]] Delete  \\[[bold cyan]Esc[/]] Cancel",
                id="delete-vault-hint",
            )

    def on_mount(self) -> None:
        self.query_one("#delete-confirm-input", Input).focus()
        logger.debug(f"DeleteVaultPanel mounted for vault '{self.vault_id}'")

    def on_input_submitted(self, event: Input.Submitted) -> None:
        typed = self.query_one("#delete-confirm-input", Input).value.strip()
        if typed != self.vault_id:
            self.query_one("#delete-vault-error", Static).update(
                "Vault name does not match — deletion cancelled"
            )
            return
        self.post_message(self.DeleteConfirmed(vault_id=self.vault_id))

    def action_cancel(self) -> None:
        logger.debug("DeleteVaultPanel cancelled")
        self.remove()

    class DeleteConfirmed(Message):
        """Message when the user confirmed vault deletion."""
        def __init__(self, vault_id: str) -> None:
            self.vault_id = vault_id
            super().__init__()
