#!/usr/bin/env bash
set -euo pipefail

# Demo launcher for PassVault
# Creates a temporary vault with example entries and launches the GTK UI.
# Requires: conda env 'passvault' (or equivalent), system PyGObject and clipboard tools.

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
VAULT_PATH="/tmp/passvault_demo.json"
PW="demo-pass"

echo "Using repo root: $REPO_ROOT"

export PYTHONPATH="$REPO_ROOT"

# Helper: test if a python binary can import gi and Gtk 4
can_use_python() {
  local py=$1
  "$py" - <<'PY' 2>/dev/null || return 1
import sys
try:
    import gi
    gi.require_version('Gtk','4.0')
    from gi.repository import Gtk
    print('OK')
except Exception:
    sys.exit(1)
PY
  return $? 
}

# Find a suitable python: prefer current `python`, then /usr/bin/python3, then conda-run
PY_BIN=""
if command -v python >/dev/null 2>&1 && can_use_python "$(command -v python)"; then
  PY_BIN="$(command -v python)"
  echo "Using active python: $PY_BIN"
elif [ -x "/usr/bin/python3" ] && can_use_python "/usr/bin/python3"; then
  PY_BIN="/usr/bin/python3"
  echo "Using system python: $PY_BIN"
elif command -v conda >/dev/null 2>&1 && conda run -n passvault --no-capture-output python -c "import gi; gi.require_version('Gtk','4.0'); from gi.repository import Gtk; print('OK')" 2>/dev/null; then
  PY_BIN="conda run -n passvault python"
  echo "Using conda run -n passvault python"
else
  echo "No python with PyGObject/GTK4 available. Install 'python-gobject' (system) or add pygobject to your conda env." >&2
  exit 1
fi

echo "Creating demo vault at $VAULT_PATH"
if [ "$PY_BIN" = "conda run -n passvault python" ]; then
  $PY_BIN -m passvault_core.cli create "$VAULT_PATH" --password "$PW" || true
  $PY_BIN -m passvault_core.cli add "$VAULT_PATH" --password "$PW" --name "Email" --username "alice@example.com" --password-field "email-pass"
  $PY_BIN -m passvault_core.cli add "$VAULT_PATH" --password "$PW" --name "Bank" --username "alice" --password-field "bank-pass"
  echo "Launching GUI (unlock using password: $PW)"
  $PY_BIN -m passvault_gui.main
else
  "$PY_BIN" -m passvault_core.cli create "$VAULT_PATH" --password "$PW" || true
  "$PY_BIN" -m passvault_core.cli add "$VAULT_PATH" --password "$PW" --name "Email" --username "alice@example.com" --password-field "email-pass"
  "$PY_BIN" -m passvault_core.cli add "$VAULT_PATH" --password "$PW" --name "Bank" --username "alice" --password-field "bank-pass"
  echo "Launching GUI (unlock using password: $PW)"
  exec "$PY_BIN" -m passvault_gui.main
fi
