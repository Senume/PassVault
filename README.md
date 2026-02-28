# 🔐 PassVault

A local-first TUI (Terminal User Interface) password manager for Linux.  
Credentials are encrypted with **Argon2id + AES-GCM** and never leave your machine.

---

## Features

| Key | Action |
|-----|--------|
| `/` | Open vault selector overlay |
| `n` | Create a new vault |
| `g` | Add a new credential to the current vault |
| `f` | Search credentials by name |
| `e` | Export current vault as an encrypted `.pvault` archive |
| `i` | Import a vault from a `.pvault` archive |
| `ctrl+d` | Delete the current vault (requires typing vault name) |
| `ctrl+g` | Auto-generate a strong password (inside Add Credential panel) |
| `ctrl+v` | Paste from clipboard into any input field |

---

## Requirements

### System dependency
PassVault uses `xclip` for clipboard operations:
```bash
sudo apt install xclip        # Debian / Ubuntu
sudo pacman -S xclip          # Arch
sudo dnf install xclip        # Fedora
```

### Python
- Python **3.10+**

---

## Installation

### From PyPI
```bash
pip install passvault
```

### From source
```bash
git clone https://github.com/Senume/PassVault.git
cd PassVault
pip install -e .
```

---

## Running

```bash
passvault
```

---

## Data & log paths

PassVault resolves paths in priority order:

| | System path (root) | User fallback | Env override |
|---|---|---|---|
| **Vaults** | `/etc/passvault/vaults` | `~/.local/share/passvault/vaults` | `$PASSVAULT` |
| **Logs** | `/var/log/passvault/passvault.log` | `~/.local/state/passvault/passvault.log` | `$PASSVAULT_LOG` |

Directories are created automatically on first run.

> To grant your user write access to the system paths:
> ```bash
> sudo mkdir -p /etc/passvault/vaults /var/log/passvault
> sudo chown -R $USER /etc/passvault /var/log/passvault
> ```

---

## Usage walkthrough

### 1 — Create a vault
Press `n`, enter a vault name and master password (confirmed twice). Press `Enter`.

### 2 — Add credentials
Press `g` (a vault must be selected first via `/`).  
Fill in **Name**, **Username**, **Password** — or press `Ctrl+G` to auto-generate a strong password.  
Press `Enter` to confirm, then enter the vault master password.

### 3 — View credentials
Select a credential from the list and press `Enter`.  
Enter the master password to unlock.  
Press `c` to copy the username or `p` to copy the password to clipboard.  
Press `Esc` to close.

### 4 — Search
Press `f` to focus the search bar. Type to filter credentials by name in real time. Press `Esc` to clear.

### 5 — Export / Import
- **Export** (`e`): saves the current vault as an encrypted `.pvault` zip to a path you specify (default: `~/PassVault_exports/`).
- **Import** (`i`): restores a vault from a `.pvault` file path.

The archive keeps credentials AES-GCM encrypted — no master password is needed for the transfer itself.

### 6 — Delete a vault
Press `Ctrl+D`, then type the vault name exactly to confirm permanent deletion.

---

## Security

- **KDF**: Argon2id (time cost 3, memory 64 MB, parallelism 1)
- **Encryption**: AES-256-GCM per credential — each `.ptr` file is independently encrypted
- **Master password**: never stored; derived key exists only in memory during a session
- **Clipboard**: copy operations use `xclip`; clear the clipboard manually after use

---

## Development

```bash
git clone https://github.com/Senume/PassVault.git
cd PassVault
pip install -e ".[dev]"

# Run tests
PYTHONPATH=$PWD pytest -q

# Run the app
PASSVAULT=data passvault
```

---

## License

MIT — see [LICENSE](LICENSE)
