# PassVault – Copilot Instructions

## Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run all tests (must set PYTHONPATH from repo root)
PYTHONPATH=$PWD pytest -q

# Run a single test file
PYTHONPATH=$PWD pytest passvault_core/tests/test_crypto.py -q

# Run a single test by name
PYTHONPATH=$PWD pytest passvault_core/tests/test_crypto.py::TestEncryptDecrypt::test_roundtrip -q

# Launch the TUI
python main.py
```

## Architecture

PassVault is a local-first password manager with two top-level packages:

- **`passvault_core/`** – crypto, storage, schema, clipboard, and errors. No UI dependency.
- **`passvault_tui/`** – Textual TUI. Imports from `passvault_core` and `utils`.
- **`utils/`** – Shared logger (`utils.logger`). Both layers import `from utils import logger`.
- **`main.py`** – Entry point; calls `passvault_tui.app.run()`.

### Storage layout

Vaults live under `data/<vault_id>/` (overridden via the `PASSVAULT` env var):

```
data/
  <vault_id>/
    vault_config.json     # metadata: salt, KDF params, pointer list (id + nonce)
    <pointer_id>.ptr      # AES-GCM encrypted credential blob (binary)
```

`vault_config.json` never contains plaintext credentials. Each `.ptr` file contains the ciphertext for one credential (username + password JSON, base64-encoded, then AES-GCM encrypted).

### Crypto pipeline

1. **KDF**: Argon2id (`argon2-cffi`) derives a 32-byte key from the master password + per-vault salt.
2. **Encrypt**: AES-GCM (`cryptography`) with a random 12-byte nonce → `(nonce, ciphertext)`.
3. **Nonce** is stored in `vault_config.json` alongside the pointer id; ciphertext goes in the `.ptr` file.
4. Binary fields (`salt`, `nonce`) are base64-encoded in JSON.

### TUI (Textual) patterns

All UI panels are defined in `passvault_tui/app.py`. Communication between panels uses Textual's **message-passing** (`post_message` / `on_<widget>_<message>`):

- `AddCredentialPanel.CredentialAdded` → triggers master-password prompt
- `MasterPasswordPanel.PasswordConfirmed` / `PasswordCancelled` → drives credential retrieval or creation
- `CredentialPanel.CredentialClosed` → cleans up and re-enables the option list

The `OptionList` is disabled while any modal panel is active to prevent double interaction.

## Key Conventions

- **Atomic writes**: All file writes go through `Vault.atomic_write_bytes(path, data)` (write to temp file, then `os.replace`). Never write vault files directly.
- **Pydantic compat**: Schema classes support both Pydantic v1 and v2 via a `from_dict` helper that tries `model_validate` → `parse_obj` → direct construction.
- **Clipboard**: Uses `xclip` (Linux only). The global `ClipboardManager` singleton is accessed via `get_clipboard_manager()` from `passvault_core.clipboard`.
- **Error types**: `DecryptionError` and `ClipboardError` are defined in `passvault_core/errors.py`; `clipboard.py` also redeclares `ClipboardError` locally – use the one from the module you're working in.
- **Logging**: Import the shared logger with `from utils import logger`. Logs go to `passvault.log` at the repo root.
- **Test mocking**: Clipboard tests mock `ClipboardManager._write_to_clipboard` (the static method), not subprocess directly.
