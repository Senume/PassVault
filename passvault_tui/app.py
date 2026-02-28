"""Main TUI application using Textual."""

from textual.app import ComposeResult, App
from textual.containers import Vertical, Horizontal
from textual.widgets import Header, Footer, Label, Button, Select, OptionList, Static, Input, Rule
from textual.message import Message
from textual.widgets. option_list import Option

from passvault_core.clipboard import get_clipboard_manager
from passvault_core.storage import Vault
from utils import logger

class CredentialPanel(Vertical):
    """Panel to display credential details - uses Vertical for focusability."""
    
    # Ensure the container can receive focus
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
        """Update display with data on mount."""

        # Set focus on the panel so key bindings work
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
        """Close the credential panel."""
        logger.debug("action_close_panel called")
        self.post_message(self.CredentialClosed())

    def action_copy_credentials(self) -> None:
        """Copy username to clipboard."""
        logger.debug("action_copy_credentials called")
        try:
            clipboard_manager = get_clipboard_manager()
            clipboard_manager.copy(self.username)
            logger.info(f"Copied username to clipboard")
            self.app.notify("Username copied to clipboard")
        except Exception as e:
            logger.error(f"Failed to copy username: {e}")
            self.app.notify(f"Failed to copy: {e}", severity="error")

    def action_copy_password(self) -> None:
        """Copy password to clipboard."""
        logger.debug("action_copy_password called")
        try:
            clipboard_manager = get_clipboard_manager()
            clipboard_manager.copy(self.password)
            logger.info(f"Copied password to clipboard")
            self.app.notify("Password copied to clipboard")
        except Exception as e:
            logger.error(f"Failed to copy password:  {e}")
            self.app.notify(f"Failed to copy: {e}", severity="error")

    class CredentialClosed(Message):
        """Message when credential panel is closed."""
        pass

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
        """Focus on password input when panel mounts."""
        password_input = self.query_one("#master-password-input", Input)
        self.app.set_focus(password_input)
        logger.debug("Master password panel mounted, input focused.")

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle input submission (Enter key)."""
        if event.control.id == "master-password-input":
            logger.debug("Input submitted via Enter")
            password = event.value
            logger.debug(f"Password entered: {len(password)} chars")
            if not password:
                self.query_one("#password-error", Static).update("Password cannot be empty")
                return
            self.post_message(self.PasswordConfirmed(password))

    def action_cancel_password(self) -> None:
        """Cancel password entry."""
        self.post_message(self. PasswordCancelled())

    class PasswordConfirmed(Message):
        """Message when password is confirmed."""
        def __init__(self, password: str) -> None:
            self.password = password
            super().__init__()

    class PasswordCancelled(Message):
        """Message when password entry is cancelled."""
        pass

class AddVaultPanel(Vertical):
    """Panel for creating a new vault with master password confirmation."""

    can_focus = True

    BINDINGS = [
        ("escape", "cancel", "Cancel"),
    ]

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


class AddCredentialPanel(Vertical):
    """Panel for adding new credentials."""
    
    can_focus = True
    
    BINDINGS = [
        ("escape", "cancel_add", "Cancel"),
        ("enter", "confirm_add", "Add"),
    ]
    
    def compose(self) -> ComposeResult:
        with Vertical(id="add-credential-panel"):
            yield Label("Add New Credential", id="add-credential-label")
            yield Label("Name:", id="name-label")
            yield Input(id="new-name-input", placeholder="e.g. github, work-email")
            yield Label("Username:", id="username-label")
            yield Input(id="new-username-input", placeholder="Enter username")
            yield Label("Password:", id="password-label")
            yield Input(id="new-password-input", placeholder="Enter password", password=True)
            yield Static("", id="add-credential-error")

    def on_mount(self) -> None:
        """Focus on name input when panel mounts."""
        self.app.set_focus(self.query_one("#new-name-input", Input))
        logger.debug("Add credential panel mounted, name input focused.")

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle input submission (Enter key)."""
        if event.control.id == "new-name-input":
            self.query_one("#new-username-input", Input).focus()
        elif event.control.id == "new-username-input":
            self.query_one("#new-password-input", Input).focus()
        elif event.control.id == "new-password-input":
            logger.debug("Password input submitted via Enter")
            self.action_confirm_add()

    def action_cancel_add(self) -> None:
        """Cancel adding credential."""
        logger.debug("action_cancel_add called")
        # Re-enable the OptionList before removing
        try:
            pointers_list = self.app.query_one("#pointers-list", OptionList)
            pointers_list.disabled = False
            self.app.set_focus(pointers_list)
        except:
            pass
        self.remove()

    def action_confirm_add(self) -> None:
        """Confirm adding new credential."""
        logger.debug("action_confirm_add called")
        name = self.query_one("#new-name-input", Input).value.strip()
        username = self.query_one("#new-username-input", Input).value
        password = self.query_one("#new-password-input", Input).value

        error_label = self.query_one("#add-credential-error", Static)
        if not name:
            error_label.update("Name cannot be empty")
            self.query_one("#new-name-input", Input).focus()
            return
        if not username or not password:
            error_label.update("Username and password cannot be empty")
            logger.warning("Empty username or password")
            return

        try:
            self.post_message(self.CredentialAdded(name=name, username=username, password=password))
            logger.info(f"New credential added: {name}")
            try:
                self.app.query_one("#pointers-list", OptionList).disabled = False
            except Exception:
                pass
            self.remove()
        except Exception as e:
            logger.error(f"Failed to add credential: {e}")
            error_label.update(f"Error: {str(e)}")

    class CredentialAdded(Message):
        """Message when credential is added."""
        def __init__(self, name: str, username: str, password: str) -> None:
            self.name = name
            self.username = username
            self.password = password
            super().__init__()

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
    ]

    def compose(self) -> ComposeResult:
        """Compose the main layout."""
        yield Header()
        yield Select(
            options=[(vault_id, vault_id) for vault_id in self.vaults_list],
            id="vault-selector"
        )
        yield Input(placeholder="🔍 Search credentials...", id="search-input")
        yield OptionList(id="pointers-list")
        yield Footer()

    def on_mount(self) -> None:
        """Hide widgets on startup."""
        self.query_one("#vault-selector", Select).display = False
        self.query_one("#search-input", Input).display = False
        self.query_one("#pointers-list", OptionList).display = False
    

    def action_new_vault(self) -> None:
        """Show the add vault panel."""
        try:
            self.query_one("#add-vault-modal", AddVaultPanel).remove()
        except Exception:
            pass
        self.mount(AddVaultPanel(id="add-vault-modal"))

    def action_focus_search(self) -> None:
        """Focus the search input if a vault is loaded."""
        search = self.query_one("#search-input", Input)
        if search.display:
            self.set_focus(search)

    def on_key(self, event) -> None:
        """Handle Escape for the vault selector and search input."""
        if event.key == "escape":
            # Hide vault selector if it is visible
            try:
                selector = self.query_one("#vault-selector", Select)
                if selector.display:
                    selector.display = False
                    self._restore_main_focus()
                    event.stop()
                    return
            except Exception:
                pass
            # Clear search and return to list
            try:
                search = self.query_one("#search-input", Input)
                if self.focused is search:
                    search.clear()
                    self.set_focus(self.query_one("#pointers-list", OptionList))
                    event.stop()
            except Exception:
                pass

    def _restore_main_focus(self) -> None:
        """Return focus to the credentials list when a vault is loaded."""
        try:
            pointers_list = self.query_one("#pointers-list", OptionList)
            if pointers_list.display:
                self.set_focus(pointers_list)
        except Exception:
            pass

    def on_input_changed(self, event: Input.Changed) -> None:
        """Filter the credentials list as the user types in the search box."""
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

    def on_add_vault_panel_vault_created(self, message: AddVaultPanel.VaultCreated) -> None:
        """Create and persist the new vault, then refresh the vault selector."""
        name = message.name
        if name in Vault.list_vaults():
            try:
                self.query_one("#add-vault-error", Static).update(f"Vault '{name}' already exists")
            except Exception:
                self.app.notify(f"Vault '{name}' already exists", severity="warning")
            return

        try:
            new_vault = Vault(id=name, load=False)
            new_vault.update_vault()
            logger.info(f"Created vault '{name}'")

            # Dismiss the panel and refresh the selector
            try:
                self.query_one("#add-vault-modal", AddVaultPanel).remove()
            except Exception:
                pass

            updated = Vault.list_vaults()
            self.query_one("#vault-selector", Select).set_options(
                (vault_id, vault_id) for vault_id in updated
            )
            self.app.notify(f"Vault '{name}' created")
        except Exception as e:
            logger.error(f"Failed to create vault: {e}")
            self.app.notify(f"Failed to create vault: {e}", severity="error")

    def action_select_vault(self) -> None:
        """Show the vault selector as an overlay."""
        select = self.query_one("#vault-selector", Select)
        select.display = True
        self.set_focus(select)

    def on_select_changed(self, event: Select.Changed) -> None:
        """Handle vault selection — only reload if the vault actually changed."""
        if event.control.id != "vault-selector":
            return

        selector = self.query_one("#vault-selector", Select)
        selector.display = False

        selected_id = str(event.value)

        # Same vault — keep the credentials list as-is
        if self.current_vault and self.current_vault.vault_config.id == selected_id:
            self._restore_main_focus()
            return

        # New vault selected — reload credentials
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

    def action_add_credential(self) -> None:
        """Show the add credential panel."""
        logger.debug("action_add_credential called")
        if not self.current_vault:
            self.app.notify("Please select a vault first", severity="warning")
            return
        
        # Disable the OptionList
        try:
            pointers_list = self.query_one("#pointers-list", OptionList)
            pointers_list.disabled = True
        except:
            pass
        
        # Remove existing add credential panel if present
        try:
            self.query_one("#add-credential-modal", AddCredentialPanel).remove()
        except:
            pass
        
        # Mount new panel
        self.mount(AddCredentialPanel(id="add-credential-modal"))

    def on_master_password_panel_password_confirmed(self, message:  MasterPasswordPanel.PasswordConfirmed) -> None:
        """Handle password confirmation."""
        # Determine which flow sent this message
        add_modal = None
        try:
            add_modal = self.query_one("#master-password-for-add-modal", MasterPasswordPanel)
        except Exception:
            pass

        if add_modal is not None:
            # --- Add credential flow ---
            pointer_id = self.pending_credential['name']
            try:
                self.current_vault.updated_pointer(
                    master_password=message.password,
                    pointer_id=pointer_id,
                    username=self.pending_credential['username'],
                    password=self.pending_credential['password']
                )
                self.current_vault.update_vault()
            except Exception as e:
                logger.error(f"Failed to add credential: {e}")
                try:
                    add_modal.query_one("#password-error", Static).update("Failed to add credential")
                except Exception:
                    self.app.notify(f"Error: {e}", severity="error")
                return

            self.app.notify(f"Credential '{self.pending_credential['name']}' added successfully")
            add_modal.remove()

            pointers = self.current_vault.list_pointers()
            self.all_pointers = pointers
            # Clear search so the new credential is visible
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

        # --- Retrieve credential flow ---
        try:
            credential = self.current_vault.get_pointer(message.password, self.selected_pointer)
            logger.debug(f"Retrieved credential for pointer {self.selected_pointer}")
            self.query_one("#password-modal", MasterPasswordPanel).remove()
            self.mount(CredentialPanel(
                username=credential.username,
                password=credential.password,
                pointer_id=self.selected_pointer,
                id="credential-modal"
            ))
        except Exception as e:
            logger.error(f"Failed: {e}")
            self.app.notify("Wrong password", severity="error")
            try:
                self.query_one("#password-modal", MasterPasswordPanel).query_one("#password-error", Static).update("Wrong password")
            except Exception:
                pass

    def on_master_password_panel_password_cancelled(self, message: MasterPasswordPanel.PasswordCancelled) -> None:
        """Handle password cancellation."""
        for modal_id in ("#master-password-for-add-modal", "#password-modal"):
            try:
                self.query_one(modal_id, MasterPasswordPanel).remove()
                break
            except Exception:
                pass
        pointers_list = self.query_one("#pointers-list", OptionList)
        pointers_list.disabled = False
        self.set_focus(pointers_list)

    def on_credential_panel_credential_closed(self, message: CredentialPanel. CredentialClosed) -> None:
        """Handle credential closure."""
        logger.debug("Credential panel close message received")
        self.query_one("#credential-modal", CredentialPanel).remove()
        # Re-enable the OptionList
        self.query_one("#pointers-list", OptionList).disabled = False
        self.set_focus(self.query_one("#pointers-list", OptionList))

    def on_option_list_option_selected(self, event: OptionList. OptionSelected) -> None:
        """Handle pointer selection and show master password panel."""
        self.selected_pointer = event.option.id
        
        # Disable the OptionList
        pointers_list = self.query_one("#pointers-list", OptionList)
        pointers_list.disabled = True
        
        # Remove existing modal if present
        try: 
            self.query_one("#password-modal", MasterPasswordPanel).remove()
        except:
            pass
        
        # Mount new modal
        self.mount(MasterPasswordPanel(id="password-modal"))

    def on_add_credential_panel_credential_added(self, message: AddCredentialPanel.CredentialAdded) -> None:
        """Handle new credential addition - show master password panel first."""
        logger.debug(f"Credential to add: {message.username}")

        self.pending_credential = {
            'name': message.name,
            'username': message.username,
            'password': message.password
        }

        # Keep the OptionList disabled while the master password prompt is shown
        try:
            self.query_one("#pointers-list", OptionList).disabled = True
        except Exception:
            pass

        try:
            self.query_one("#master-password-for-add-modal", MasterPasswordPanel).remove()
        except Exception:
            pass

        self.mount(MasterPasswordPanel(id="master-password-for-add-modal"))

def run():
    """Run the TUI application."""
    app = PassVaultApp()
    app.run()


if __name__ == "__main__":
    run()