"""Import Vault panel — restore a vault from a .pvault zip archive."""

import os
import zipfile

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.message import Message
from textual.widgets import Label, Input, Static

from passvault_core.storage import Vault
from utils import logger


class ImportVaultPanel(Vertical):
    """Panel to import a vault from a .pvault zip archive."""

    can_focus = True

    BINDINGS = [("escape", "cancel", "Cancel")]

    def compose(self) -> ComposeResult:
        with Vertical(id="import-vault-inner"):
            yield Label("Import Vault", id="import-vault-label")
            yield Label("Path to .pvault file:", id="import-path-label")
            yield Input(
                id="import-path-input",
                placeholder="e.g. ~/PassVault_exports/myvault.pvault",
            )
            yield Static("", id="import-vault-error")
            yield Static(
                "\\[[bold cyan]Enter[/]] Import  \\[[bold cyan]Esc[/]] Cancel",
                id="import-vault-hint",
            )

    def on_mount(self) -> None:
        self.query_one("#import-path-input", Input).focus()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        self._do_import()

    def _do_import(self) -> None:
        src = os.path.expanduser(self.query_one("#import-path-input", Input).value.strip())
        error = self.query_one("#import-vault-error", Static)
        if not src:
            error.update("File path cannot be empty")
            return
        if not os.path.isfile(src):
            error.update(f"File not found: {src}")
            return
        try:
            with zipfile.ZipFile(src, "r") as zf:
                names = zf.namelist()
                vault_id = names[0].split("/")[0]
                dest_dir = os.path.join(Vault.path, vault_id)
                if os.path.exists(dest_dir):
                    error.update(f"Vault '{vault_id}' already exists")
                    return
                zf.extractall(Vault.path)
            logger.info(f"Vault '{vault_id}' imported from {src}")
            self.post_message(self.ImportDone(vault_id=vault_id))
        except Exception as e:
            logger.error(f"Import failed: {e}")
            error.update(f"Import failed: {e}")

    def action_cancel(self) -> None:
        self.remove()

    class ImportDone(Message):
        def __init__(self, vault_id: str) -> None:
            self.vault_id = vault_id
            super().__init__()
