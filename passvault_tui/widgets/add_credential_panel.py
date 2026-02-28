"""Add Credential panel — name / username / password form with auto-generate."""

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.message import Message
from textual.widgets import Label, Input, Static, OptionList
from textual import work

import httpx

from utils import logger


class AddCredentialPanel(Vertical):
    """Panel for adding new credentials."""

    can_focus = True

    BINDINGS = [
        ("escape", "cancel_add", "Cancel"),
        ("enter", "confirm_add", "Add"),
        ("ctrl+g", "generate_password", "Generate Password (Ctrl+G)"),
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
            yield Static("\[[bold cyan]Ctrl+G[/]] Auto-generate password", id="generate-hint")
            yield Static("", id="add-credential-error")

    def on_mount(self) -> None:
        self.app.set_focus(self.query_one("#new-name-input", Input))
        logger.debug("Add credential panel mounted, name input focused.")

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.control.id == "new-name-input":
            self.query_one("#new-username-input", Input).focus()
        elif event.control.id == "new-username-input":
            self.query_one("#new-password-input", Input).focus()
        elif event.control.id == "new-password-input":
            logger.debug("Password input submitted via Enter")
            self.action_confirm_add()

    @work(exclusive=True)
    async def action_generate_password(self) -> None:
        """Fetch a random password from a public API and fill the password field."""
        self.app.notify("Generating password…", timeout=2)
        url = "https://api.genratr.com/?length=20&uppercase&lowercase&numbers&special"
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(url)
                resp.raise_for_status()
                data = resp.json()
            generated = data.get("password", "")
            if not generated:
                raise ValueError("Empty response from API")
            password_input = self.query_one("#new-password-input", Input)
            password_input.value = generated
            password_input.focus()
            self.app.notify("Password generated! ✓")
            logger.info("Password auto-generated via API")
        except Exception as e:
            logger.error(f"Password generation failed: {e}")
            self.app.notify(f"Generation failed: {e}", severity="error")

    def action_cancel_add(self) -> None:
        logger.debug("action_cancel_add called")
        try:
            pointers_list = self.app.query_one("#pointers-list", OptionList)
            pointers_list.disabled = False
            self.app.set_focus(pointers_list)
        except Exception:
            pass
        self.remove()

    def action_confirm_add(self) -> None:
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
