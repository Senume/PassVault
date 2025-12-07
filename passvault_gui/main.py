"""Small GTK4 application entry that demonstrates unlocking a vault.

This is intentionally minimal: it allows picking a vault file and entering
the master password. On success it displays the top-level keys of the
stored JSON. It's only a development stub for early iteration.
"""
import sys
import typing

try:
    import gi
    gi.require_version("Gtk", "4.0")
    from gi.repository import Gtk, Gio
except Exception:
    gi = None  # type: ignore

from passvault_core.storage import open_vault
from passvault_core.errors import DecryptionError
from .clipboard import copy_and_clear, ClipboardUnavailable


if gi is not None:
    class PassVaultApp(Gtk.Application):
        def __init__(self):
            app_id = "org.passvault.app"
            super().__init__(application_id=app_id)
            self.window: typing.Optional[Gtk.ApplicationWindow] = None

        def do_activate(self):
            if self.window is None:
                self.window = Gtk.ApplicationWindow(application=self)
                self.window.set_title("PassVault - Unlock")
                self.window.set_default_size(540, 200)

                root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8, margin=12)

                # File chooser row
                row_file = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
                self.path_entry = Gtk.Entry(placeholder_text="Path to vault file")
                btn_browse = Gtk.Button(label="Browse")
                btn_browse.connect("clicked", self.on_browse)
                row_file.append(self.path_entry)
                row_file.append(btn_browse)

                # Password row
                row_pw = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
                self.pw_entry = Gtk.Entry(visibility=False, placeholder_text="Master password")
                btn_unlock = Gtk.Button(label="Unlock")
                btn_unlock.connect("clicked", self.on_unlock)
                row_pw.append(self.pw_entry)
                row_pw.append(btn_unlock)

                self.status = Gtk.Label(label="")
                self.status.set_hexpand(True)
                self.status.set_valign(Gtk.Align.START)

                # Results area
                self.results = Gtk.Label(label="")
                self.results.set_xalign(0)
                self.results.set_wrap(True)

                root.append(row_file)
                root.append(row_pw)
                root.append(self.status)
                root.append(self.results)

                self.window.set_child(root)

            self.window.present()

        def on_browse(self, button):
            chooser = Gtk.FileChooserNative.new("Open vault", self.window, Gtk.FileChooserAction.OPEN, "_Open", "_Cancel")
            chooser.connect("response", self._on_file_response)
            chooser.show()

        def _on_file_response(self, chooser, response):
            if response == Gtk.ResponseType.ACCEPT:
                file = chooser.get_file()
                if file:
                    path = file.get_path()
                    if path:
                        self.path_entry.set_text(path)
            chooser.destroy()

        def on_unlock(self, button):
            path = self.path_entry.get_text().strip()
            pw = self.pw_entry.get_text()
            if not path:
                self.status.set_text("Please select a vault file path.")
                return
            if not pw:
                self.status.set_text("Please enter the master password.")
                return
            try:
                data = open_vault(path, pw)
            except DecryptionError:
                self.status.set_text("Failed to decrypt vault: wrong password or corrupted file.")
                self.results.set_text("")
                return
            except FileNotFoundError:
                self.status.set_text("Vault file not found.")
                self.results.set_text("")
                return
            except Exception as e:
                self.status.set_text(f"Error opening vault: {e}")
                self.results.set_text("")
                return

            # Display a short summary of the loaded JSON or render items with copy buttons
            try:
                if isinstance(data, dict) and data.get("items"):
                    # Build a simple list of entries with Copy buttons
                    entries = data.get("items", [])
                    listbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
                    for it in entries:
                        name = it.get("name", "(no name)") if isinstance(it, dict) else str(it)
                        user = it.get("username", "") if isinstance(it, dict) else ""
                        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
                        lbl = Gtk.Label(label=f"{name} {('<' + user + '>') if user else ''}")
                        lbl.set_xalign(0)
                        btn_copy = Gtk.Button(label="Copy")
                        # capture password value
                        pw_value = it.get("password", "") if isinstance(it, dict) else ""

                        def make_handler(pw):
                            def _on_copy(btn):
                                try:
                                    copy_and_clear(pw)
                                    self.status.set_text("Copied to clipboard (will clear shortly)")
                                except ClipboardUnavailable:
                                    self.status.set_text("Clipboard not available on this system")

                            return _on_copy

                        btn_copy.connect("clicked", make_handler(pw_value))
                        row.append(lbl)
                        row.append(btn_copy)
                        listbox.append(row)

                    # Replace results area with listbox
                    self.window.set_child(listbox)
                    self.status.set_text("Unlocked successfully")
                else:
                    if isinstance(data, dict):
                        keys = ", ".join(sorted(data.keys())) or "(empty)"
                        self.results.set_text(f"Unlocked — top-level keys: {keys}")
                    else:
                        self.results.set_text("Unlocked — data loaded (non-dict)")
                    self.status.set_text("Unlocked successfully")
            except Exception:
                self.results.set_text("Unlocked — (could not render contents)")
                self.status.set_text("Unlocked successfully")
else:
    # gi is not available; we define no GUI classes. main() below will exit early.
    pass


def main():
    if gi is None:
        print("PyGObject (GTK4) is not available. Install system package 'python3-gi' and gir bindings to run the GUI.")
        sys.exit(1)
    app = PassVaultApp()
    app.run(sys.argv)


if __name__ == "__main__":
    main()
