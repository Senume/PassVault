"""Main TUI application using Textual."""

from textual.app import ComposeResult, App
from textual.containers import Vertical, Horizontal
from textual.widgets import Header, Footer, Label, Button, Select, OptionList, Static, Input
from textual.message import Message
from textual.widgets.option_list import Option

from passvault_core.storage import Vault
from utils import logger

class CredentialPanel(Static):
    """Panel to display credential details."""
    
    BINDINGS = [
        ("escape", "close_panel", "Close"),
    ]


    def __init__(self, username: str = "", password: str = "", **kwargs):
        super().__init__(**kwargs)
        self.username = username
        self.password = password
    
    def on_mount(self) -> None:
        """Update display with data on mount."""
        self.query_one("#credential-username", Static).update(f"Username: {self.username}")
        self.query_one("#credential-password", Static).update(f"Password: {self.password}")

    
    def compose(self) -> ComposeResult:
        with Vertical(id="credential-panel"):
            yield Label("Credential Details", id="credential-label")
            yield Static("", id="credential-username")
            yield Static("", id="credential-password")

    def action_close_panel(self) -> None:
        """Close the credential panel."""
        self.post_message(self.CredentialClosed())

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
            self.post_message(self.PasswordConfirmed(password))

    def action_cancel_password(self) -> None:
        """Cancel password entry."""
        self.post_message(self.PasswordCancelled())

    class PasswordConfirmed(Message):
        """Message when password is confirmed."""
        def __init__(self, password: str) -> None:
            self.password = password
            super().__init__()

    class PasswordCancelled(Message):
        """Message when password entry is cancelled."""
        pass

class PassVaultApp(App):
    """Main PassVault TUI application."""

    TITLE = "🔐 PassVault"
    SUB_TITLE = "A Simple TUI Password Manager"
    CSS_PATH = "style.css"
    
    vaults_list = Vault.list_vaults()
    current_vault = None

    BINDINGS = [
        ("slash", "select_vault", "Select a Vault (/)"),
    ]

    def compose(self) -> ComposeResult:
        """Compose the main layout."""
        yield Header()
        yield Select(
            options=[(vault_id, vault_id) for vault_id in self.vaults_list],
            id="vault-selector"
        )
        yield OptionList(id="pointers-list")
        yield Footer()
    
    def on_mount(self) -> None:
        """Hide the Select widget on startup."""
        self.query_one("#vault-selector", Select).display = False
        self.query_one("#pointers-list", OptionList).display = False
    

    def action_select_vault(self) -> None:
        """Show the Select widget and focus it."""
        select = self.query_one("#vault-selector", Select)
        select.display = True
        self.set_focus(select)

    def on_select_changed(self, event: Select.Changed) -> None:
        """Handle vault selection."""
        # If this is the vault selector
        if event.control.id == "vault-selector":
            self.query_one("#vault-selector", Select).display = False
            self.sub_title = f"Selected Vault: {event.value}"
            
            # Initialize vault and load pointers
            self.current_vault = Vault(id=event.value)
            pointers = self.current_vault.list_pointers()
            
            # Update pointers list with OptionList
            pointers_list = self.query_one("#pointers-list", OptionList)
            pointers_list.clear_options()
            
            for pointer in pointers:
                pointers_list.add_option(Option(pointer, id=pointer))
            
            pointers_list.display = True
            self.set_focus(pointers_list)

    def on_master_password_panel_password_confirmed(self, message: MasterPasswordPanel.PasswordConfirmed) -> None:
        """Handle password confirmation."""
        try:
            credential = self.current_vault.get_pointer(message.password, self.selected_pointer)
            logger.debug(f"Master credential for pointer {message.password}")
            self.sub_title = f"Username: {credential.username}"
            self.sub_title = f": {credential.password}"
            self.query_one("#password-modal", MasterPasswordPanel).remove()
            
            # Display credential details panel
            # Mount panel with data directly
            self.mount(CredentialPanel(
                username=credential.username,
                password=credential.password,
                id="credential-modal"
            ))

        except Exception as e:
            error_label = self.query_one("#password-error", Static)
            error_label.update("Wrong password")

    def on_master_password_panel_password_cancelled(self, message: MasterPasswordPanel.PasswordCancelled) -> None:
        """Handle password cancellation."""
        self.query_one("#password-modal", MasterPasswordPanel).remove()
        # Re-enable the OptionList
        self.query_one("#pointers-list", OptionList).disabled = False
        self.set_focus(self.query_one("#pointers-list", OptionList))

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
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

def run():
    """Run the TUI application."""
    app = PassVaultApp()
    app.run()


if __name__ == "__main__":
    run()