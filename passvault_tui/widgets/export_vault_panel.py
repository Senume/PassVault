"""Export Vault panel — save vault as an encrypted .pvault zip archive."""

import os
import zipfile

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.message import Message
from textual.widgets import Label, Input, Static

from utils import logger


class ExportVaultPanel(Vertical):
    """Panel to export the current vault as an encrypted zip archive."""

    can_focus = True

    BINDINGS = [("escape", "cancel", "Cancel")]

    def __init__(self, vault_id: str, vault_path: str, **kwargs):
        self.vault_id = vault_id
        self.vault_path = vault_path
        super().__init__(**kwargs)

    def compose(self) -> ComposeResult:
        default_dest = os.path.join(
            os.path.expanduser("~"), "PassVault_exports", f"{self.vault_id}.pvault"
        )
        with Vertical(id="export-vault-inner"):
            yield Label("Export Vault", id="export-vault-label")
            yield Label(f"Vault: [bold]{self.vault_id}[/bold]", id="export-vault-name")
            yield Label("Export path:", id="export-path-label")
            yield Input(id="export-path-input", value=default_dest)
            yield Static("", id="export-vault-error")
            yield Static(
                "\\[[bold cyan]Enter[/]] Export  \\[[bold cyan]Esc[/]] Cancel",
                id="export-vault-hint",
            )

    def on_mount(self) -> None:
        self.query_one("#export-path-input", Input).focus()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        self._do_export()

    def _do_export(self) -> None:
        dest = self.query_one("#export-path-input", Input).value.strip()
        error = self.query_one("#export-vault-error", Static)
        if not dest:
            error.update("Export path cannot be empty")
            return
        try:
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            with zipfile.ZipFile(dest, "w", zipfile.ZIP_DEFLATED) as zf:
                for fname in os.listdir(self.vault_path):
                    zf.write(
                        os.path.join(self.vault_path, fname),
                        arcname=os.path.join(self.vault_id, fname),
                    )
            logger.info(f"Vault '{self.vault_id}' exported to {dest}")
            self.post_message(self.ExportDone(dest=dest))
        except Exception as e:
            logger.error(f"Export failed: {e}")
            error.update(f"Export failed: {e}")

    def action_cancel(self) -> None:
        self.remove()

    class ExportDone(Message):
        def __init__(self, dest: str) -> None:
            self.dest = dest
            super().__init__()
