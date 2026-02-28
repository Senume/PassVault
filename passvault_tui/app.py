"""Main TUI application — PassVaultApp and entry point."""

import os
import shutil

from textual.app import ComposeResult, App
from textual.widgets import Header, Footer, Select, OptionList, Input, Static
from textual.widgets.option_list import Option

from passvault_core.clipboard import ClipboardManager
from passvault_core.storage import Vault
from utils import logger

from passvault_tui.widgets import (
    CredentialPanel,
    MasterPasswordPanel,
    AddVaultPanel,
    AddCredentialPanel,
    ExportVaultPanel,
    ImportVaultPanel,
    DeleteVaultPanel,
)


class PassVaultApp(App):
    """Main PassVault TUI application."""

    TITLE = "🔐 PassVault"
    SUB_TITLE = "A Simple TUI Password Manager"
    CSS_PATH = "style.css"

    vaults_list = Vault.list_vaults()
    current_vault = None
    pending_credential = None
    all_pointers: list = []

    BINDINGS = [
        ("slash", "select_vault", "Select a Vault (/)"),
        ("n", "new_vault", "New Vault (N)"),
        ("g", "add_credential", "Add Credential (G)"),
        ("f", "focus_search", "Search (F)"),
        ("e", "export_vault", "Export Vault (E)"),
        ("i", "import_vault", "Import Vault (I)"),
        ("ctrl+d", "delete_vault", "Delete Vault (Ctrl+D)"),
    ]

    # ── Layout ────────────────────────────────────────────────────

    def compose(self) -> ComposeResult:
        yield Header()
        yield Select(
            options=[(vault_id, vault_id) for vault_id in self.vaults_list],
            id="vault-selector",
        )
        yield Input(placeholder="🔍 Search credentials...", id="search-input")
        yield OptionList(id="pointers-list")
        yield Footer()

    def on_mount(self) -> None:
        self.query_one("#vault-selector", Select).display = False
        self.query_one("#search-input", Input).display = False
        self.query_one("#pointers-list", OptionList).display = False

    # ── Vault actions ─────────────────────────────────────────────

    def action_new_vault(self) -> None:
        try:
            self.query_one("#add-vault-modal", AddVaultPanel).remove()
        except Exception:
            pass
        self.mount(AddVaultPanel(id="add-vault-modal"))

    def action_export_vault(self) -> None:
        if self.current_vault is None:
            self.notify("Select a vault first", severity="warning")
            return
        vault_id = self.current_vault.vault_config.id
        vault_path = os.path.join(Vault.path, vault_id)
        try:
            self.query_one("#export-vault-modal", ExportVaultPanel).remove()
        except Exception:
            pass
        self.mount(ExportVaultPanel(vault_id=vault_id, vault_path=vault_path, id="export-vault-modal"))

    def action_import_vault(self) -> None:
        try:
            self.query_one("#import-vault-modal", ImportVaultPanel).remove()
        except Exception:
            pass
        self.mount(ImportVaultPanel(id="import-vault-modal"))

    def action_delete_vault(self) -> None:
        if self.current_vault is None:
            self.notify("Select a vault first", severity="warning")
            return
        vault_id = self.current_vault.vault_config.id
        try:
            self.query_one("#delete-vault-modal", DeleteVaultPanel).remove()
        except Exception:
            pass
        self.mount(DeleteVaultPanel(vault_id=vault_id, id="delete-vault-modal"))

    def action_select_vault(self) -> None:
        select = self.query_one("#vault-selector", Select)
        select.display = True
        self.set_focus(select)

    # ── Credential actions ────────────────────────────────────────

    def action_add_credential(self) -> None:
        logger.debug("action_add_credential called")
        if not self.current_vault:
            self.notify("Please select a vault first", severity="warning")
            return
        try:
            pointers_list = self.query_one("#pointers-list", OptionList)
            pointers_list.disabled = True
        except Exception:
            pass
        try:
            self.query_one("#add-credential-modal", AddCredentialPanel).remove()
        except Exception:
            pass
        self.mount(AddCredentialPanel(id="add-credential-modal"))

    def action_focus_search(self) -> None:
        search = self.query_one("#search-input", Input)
        if search.display:
            self.set_focus(search)

    # ── Event handlers ────────────────────────────────────────────

    def on_key(self, event) -> None:
        """Global key handler: Ctrl+V paste and Escape."""
        if event.key == "ctrl+v":
            focused = self.focused
            if isinstance(focused, Input):
                try:
                    text = ClipboardManager._read_from_clipboard()
                    if text:
                        focused.insert_text_at_cursor(text)
                        event.stop()
                except Exception as e:
                    logger.warning(f"Paste failed: {e}")
            return

        if event.key == "escape":
            try:
                selector = self.query_one("#vault-selector", Select)
                if selector.display:
                    selector.display = False
                    self._restore_main_focus()
                    event.stop()
                    return
            except Exception:
                pass
            try:
                search = self.query_one("#search-input", Input)
                if self.focused is search:
                    search.clear()
                    self.set_focus(self.query_one("#pointers-list", OptionList))
                    event.stop()
            except Exception:
                pass

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.control.id != "search-input":
            return
        query = event.value.strip().lower()
        pointers_list = self.query_one("#pointers-list", OptionList)
        pointers_list.clear_options()
        matches = (
            [p for p in self.all_pointers if query in p.lower()]
            if query else self.all_pointers
        )
        for pointer in matches:
            pointers_list.add_option(Option(pointer, id=pointer))

    def on_select_changed(self, event: Select.Changed) -> None:
        if event.control.id != "vault-selector":
            return
        selector = self.query_one("#vault-selector", Select)
        selector.display = False

        selected_id = str(event.value)
        if self.current_vault and self.current_vault.vault_config.id == selected_id:
            self._restore_main_focus()
            return

        self.sub_title = f"Selected Vault: {selected_id}"
        self.current_vault = Vault(id=selected_id)
        pointers = self.current_vault.list_pointers()
        self.all_pointers = pointers

        search = self.query_one("#search-input", Input)
        search.clear()
        search.display = True

        pointers_list = self.query_one("#pointers-list", OptionList)
        pointers_list.clear_options()
        for pointer in pointers:
            pointers_list.add_option(Option(pointer, id=pointer))
        pointers_list.display = True
        self.set_focus(pointers_list)

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        self.selected_pointer = event.option.id
        pointers_list = self.query_one("#pointers-list", OptionList)
        pointers_list.disabled = True
        try:
            self.query_one("#password-modal", MasterPasswordPanel).remove()
        except Exception:
            pass
        self.mount(MasterPasswordPanel(id="password-modal"))

    def on_master_password_panel_password_confirmed(self, message: MasterPasswordPanel.PasswordConfirmed) -> None:
        add_modal = None
        try:
            add_modal = self.query_one("#master-password-for-add-modal", MasterPasswordPanel)
        except Exception:
            pass

        if add_modal is not None:
            pointer_id = self.pending_credential['name']
            try:
                self.current_vault.updated_pointer(
                    master_password=message.password,
                    pointer_id=pointer_id,
                    username=self.pending_credential['username'],
                    password=self.pending_credential['password'],
                )
                self.current_vault.update_vault()
            except Exception as e:
                logger.error(f"Failed to add credential: {e}")
                try:
                    add_modal.query_one("#password-error", Static).update("Failed to add credential")
                except Exception:
                    self.notify(f"Error: {e}", severity="error")
                return

            self.notify(f"Credential '{self.pending_credential['name']}' added successfully")
            add_modal.remove()

            pointers = self.current_vault.list_pointers()
            self.all_pointers = pointers
            try:
                self.query_one("#search-input", Input).clear()
            except Exception:
                pass
            pointers_list = self.query_one("#pointers-list", OptionList)
            pointers_list.clear_options()
            for pointer in pointers:
                pointers_list.add_option(Option(pointer, id=pointer))
            pointers_list.disabled = False
            self.set_focus(pointers_list)
            return

        # Retrieve credential flow
        try:
            credential = self.current_vault.get_pointer(message.password, self.selected_pointer)
            logger.debug(f"Retrieved credential for pointer {self.selected_pointer}")
            self.query_one("#password-modal", MasterPasswordPanel).remove()
            self.mount(CredentialPanel(
                username=credential.username,
                password=credential.password,
                pointer_id=self.selected_pointer,
                id="credential-modal",
            ))
        except Exception as e:
            logger.error(f"Failed: {e}")
            self.notify("Wrong password", severity="error")
            try:
                self.query_one("#password-modal", MasterPasswordPanel).query_one(
                    "#password-error", Static
                ).update("Wrong password")
            except Exception:
                pass

    def on_master_password_panel_password_cancelled(self, message: MasterPasswordPanel.PasswordCancelled) -> None:
        for modal_id in ("#master-password-for-add-modal", "#password-modal"):
            try:
                self.query_one(modal_id, MasterPasswordPanel).remove()
                break
            except Exception:
                pass
        pointers_list = self.query_one("#pointers-list", OptionList)
        pointers_list.disabled = False
        self.set_focus(pointers_list)

    def on_credential_panel_credential_closed(self, message: CredentialPanel.CredentialClosed) -> None:
        logger.debug("Credential panel close message received")
        self.query_one("#credential-modal", CredentialPanel).remove()
        self.query_one("#pointers-list", OptionList).disabled = False
        self.set_focus(self.query_one("#pointers-list", OptionList))

    def on_add_vault_panel_vault_created(self, message: AddVaultPanel.VaultCreated) -> None:
        name = message.name
        if name in Vault.list_vaults():
            try:
                self.query_one("#add-vault-error", Static).update(f"Vault '{name}' already exists")
            except Exception:
                self.notify(f"Vault '{name}' already exists", severity="warning")
            return
        try:
            new_vault = Vault(id=name, load=False)
            new_vault.update_vault()
            logger.info(f"Created vault '{name}'")
            try:
                self.query_one("#add-vault-modal", AddVaultPanel).remove()
            except Exception:
                pass
            updated = Vault.list_vaults()
            self.query_one("#vault-selector", Select).set_options(
                (vault_id, vault_id) for vault_id in updated
            )
            self.notify(f"Vault '{name}' created")
        except Exception as e:
            logger.error(f"Failed to create vault: {e}")
            self.notify(f"Failed to create vault: {e}", severity="error")

    def on_add_credential_panel_credential_added(self, message: AddCredentialPanel.CredentialAdded) -> None:
        logger.debug(f"Credential to add: {message.username}")
        self.pending_credential = {
            'name': message.name,
            'username': message.username,
            'password': message.password,
        }
        try:
            self.query_one("#pointers-list", OptionList).disabled = True
        except Exception:
            pass
        try:
            self.query_one("#master-password-for-add-modal", MasterPasswordPanel).remove()
        except Exception:
            pass
        self.mount(MasterPasswordPanel(id="master-password-for-add-modal"))

    def on_export_vault_panel_export_done(self, message: ExportVaultPanel.ExportDone) -> None:
        try:
            self.query_one("#export-vault-modal", ExportVaultPanel).remove()
        except Exception:
            pass
        self.notify(f"Vault exported → {message.dest}")

    def on_import_vault_panel_import_done(self, message: ImportVaultPanel.ImportDone) -> None:
        try:
            self.query_one("#import-vault-modal", ImportVaultPanel).remove()
        except Exception:
            pass
        updated = Vault.list_vaults()
        self.query_one("#vault-selector", Select).set_options((v, v) for v in updated)
        self.notify(f"Vault '{message.vault_id}' imported ✓")
        logger.info(f"Vault '{message.vault_id}' imported and selector refreshed")

    def on_delete_vault_panel_delete_confirmed(self, message: DeleteVaultPanel.DeleteConfirmed) -> None:
        vault_id = message.vault_id
        vault_path = os.path.join(Vault.path, vault_id)
        try:
            shutil.rmtree(vault_path)
            logger.info(f"Vault '{vault_id}' deleted")
        except Exception as e:
            logger.error(f"Failed to delete vault: {e}")
            self.notify(f"Failed to delete vault: {e}", severity="error")
            return

        # Reset app state
        self.current_vault = None
        self.all_pointers = []
        self.sub_title = "A Simple TUI Password Manager"
        try:
            self.query_one("#delete-vault-modal", DeleteVaultPanel).remove()
        except Exception:
            pass
        self.query_one("#search-input", Input).display = False
        self.query_one("#pointers-list", OptionList).display = False

        updated = Vault.list_vaults()
        self.query_one("#vault-selector", Select).set_options((v, v) for v in updated)
        self.notify(f"Vault '{vault_id}' deleted")

    # ── Helpers ───────────────────────────────────────────────────

    def _restore_main_focus(self) -> None:
        try:
            pointers_list = self.query_one("#pointers-list", OptionList)
            if pointers_list.display:
                self.set_focus(pointers_list)
        except Exception:
            pass


def run():
    """Run the TUI application."""
    app = PassVaultApp()
    app.run()


if __name__ == "__main__":
    run()
