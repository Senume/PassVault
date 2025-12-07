import sys
from typing import List, Dict

from textual.app import App, ComposeResult
from textual.widgets import Input, Button, Static, DataTable
from textual.containers import Vertical, Horizontal

from passvault_core import storage
from passvault_core import clipboard


class UnlockView(Vertical):
    def __init__(self):
        super().__init__()
        self.path_input = Input(placeholder="Vault path (e.g., /tmp/passvault_demo.json)")
        self.password_input = Input(password=True, placeholder="Vault password")
        self.status = Static("")
        self.unlock_btn = Button(label="Unlock", id="unlock")

    def compose(self) -> ComposeResult:
        yield self.path_input
        yield self.password_input
        yield self.unlock_btn
        yield self.status


class VaultApp(App):
    CSS = """
    Screen { align: center middle; }
    #unlock { margin-top: 1; }
    """

    def __init__(self):
        super().__init__()
        self.unlock = UnlockView()
        self.table = DataTable()
        self.entries: List[Dict] = []
        self._auto_path = None
        self._auto_password = None
        self._current_path = None
        self._current_password = None
        self.add_form = None

    def compose(self) -> ComposeResult:
        yield self.unlock

    def on_mount(self) -> None:
        # Auto-fill from environment variables if provided
        if self._auto_path:
            self.unlock.path_input.value = self._auto_path
        if self._auto_password:
            self.unlock.password_input.value = self._auto_password
        if self._auto_path and self._auto_password:
            # Trigger unlock automatically on the app thread
            self.post_message(Button.Pressed(self.unlock.unlock_btn))

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "unlock":
            path = self.unlock.path_input.value.strip()
            password = self.unlock.password_input.value
            try:
                data = storage.open_vault(path, password)
                # entries may be a list or dict depending on storage; normalize to list of dicts
                entries = data.get("entries", [])
                if isinstance(entries, dict):
                    # assume {name: {username:..., password:...}}
                    self.entries = [
                        {"name": k, **(v if isinstance(v, dict) else {})} for k, v in entries.items()
                    ]
                else:
                    self.entries = entries
            except Exception as e:
                self.unlock.status.update(f"[red]Failed to open vault: {e}")
                return

            # Build entries table
            self.table.clear()
            self.table.show_header = True
            self.table.add_columns("Name", "Username", "Password", "Actions")
            for idx, entry in enumerate(self.entries or []):
                name = entry.get("name", "")
                username = entry.get("username", "")
                pw = entry.get("password", "")
                actions = f"[copy user:{idx}] [copy pass:{idx}]"
                self.table.add_row(name, username, pw, actions)

            if not self.entries:
                self.unlock.status.update("[yellow]Vault opened but no entries found. Use CLI to add entries.")

            # Replace unlock view with table and action help in the same screen
            help_text = Static("Shortcuts: 'u' to copy username, 'p' to copy password. Select a row first.")
            container = Vertical(self.table, help_text)
            # Remove the unlock form and mount the entries view
            try:
                self.unlock.remove()
            except Exception:
                pass
            await self.mount(container)
            # Ensure a row is selected if available
            if self.table.row_count:
                self.table.cursor_type = "row"
                self.table.cursor_row = 0
                self.table.refresh()
            # Remember current vault
            self._current_path = path
            self._current_password = password

    async def on_data_table_cell_selected(self, event: DataTable.CellSelected) -> None:
        # Parse action commands in the selected cell
        row = event.coordinate.row
        column = event.coordinate.column
        if column != 3:  # Actions column
            return
        cell = self.table.get_cell_at(row, column)
        text = str(cell)
        # Expect something like "[copy user:0] [copy pass:0]"
        # We'll copy username on first Enter, password on second Enter based on caret position is complex.
        # Instead, parse by row and show a small prompt in status.
        entry = self.entries[row]
        try:
            # Default to copying password when selecting actions; provide both options via shortcuts
            await self.copy_to_clipboard(entry.get("password", ""))
            await self.toast("Copied password; it will clear automatically.")
        except Exception as e:
            await self.toast(f"Copy failed: {e}", severity="error")

    async def on_key(self, event) -> None:
        # Shortcuts: u to copy username, p to copy password when a row is selected
        if not self.table.rows:
            return
        if event.key == "u":
            row = self.table.cursor_row or 0
            try:
                await self.copy_to_clipboard(self.entries[row].get("username", ""))
                await self.toast("Copied username.")
            except Exception as e:
                await self.toast(f"Copy failed: {e}", severity="error")
        elif event.key == "p":
            row = self.table.cursor_row or 0
            try:
                await self.copy_to_clipboard(self.entries[row].get("password", ""))
                await self.toast("Copied password; it will clear automatically.")
            except Exception as e:
                await self.toast(f"Copy failed: {e}", severity="error")
        elif event.key == "a":
            # Open Add Entry form
            await self.open_add_form()

    async def copy_to_clipboard(self, text: str) -> None:
        clipboard.copy_and_clear(text, timeout=15)

    async def open_add_form(self) -> None:
        # Build a simple inline add form
        name_input = Input(placeholder="Name")
        user_input = Input(placeholder="Username")
        pass_input = Input(password=True, placeholder="Password")
        submit_btn = Button(label="Add", id="add")
        cancel_btn = Button(label="Cancel", id="cancel")

        form_status = Static("")
        self.add_form = Vertical(
            Static("Add new entry"),
            name_input,
            user_input,
            pass_input,
            Horizontal(submit_btn, cancel_btn),
            form_status,
        )
        await self.mount(self.add_form)

        # Inner handler to process button presses specific to the form
        async def handle(event_btn: Button.Pressed) -> None:
            nonlocal name_input, user_input, pass_input, form_status
            if event_btn.button.id == "cancel":
                try:
                    self.add_form.remove()
                except Exception:
                    pass
                self.add_form = None
                return
            if event_btn.button.id == "add":
                name = name_input.value.strip()
                username = user_input.value.strip()
                password = pass_input.value
                if not name:
                    form_status.update("[red]Name is required")
                    return
                # Append and persist
                self.entries.append({"name": name, "username": username, "password": password})
                try:
                    # Reconstruct vault data and save
                    data = {"entries": self.entries}
                    storage.save_vault(self._current_path, data, self._current_password)
                except Exception as e:
                    form_status.update(f"[red]Save failed: {e}")
                    return
                # Update table
                self.table.add_row(name, username, password, f"[copy user:{len(self.entries)-1}] [copy pass:{len(self.entries)-1}]")
                await self.toast("Entry added.")
                try:
                    self.add_form.remove()
                except Exception:
                    pass
                self.add_form = None

        # Temporarily hook into on_button_pressed to catch add/cancel while form is mounted
        original_handler = getattr(self, "on_button_pressed")

        async def proxy_handler(event: Button.Pressed) -> None:
            if self.add_form and event.button.id in {"add", "cancel"}:
                await handle(event)
            else:
                await original_handler(event)

        # Monkey-patch for the duration of the form
        self.on_button_pressed = proxy_handler  # type: ignore


def main():
    app = VaultApp()
    app.run()


if __name__ == "__main__":
    main()
