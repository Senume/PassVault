#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
export PYTHONPATH="$REPO_ROOT"

echo "Using repo root: $REPO_ROOT"

# Ensure textual is installed
if ! python -c "import textual" >/dev/null 2>&1; then
  echo "Missing 'textual'. Please install requirements: pip install -r requirements.txt or 'conda install -c conda-forge textual rich'" >&2
  exit 1
fi

# Auto-create a demo vault if none is provided via args
VAULT_PATH=${1:-/tmp/passvault_demo.json}
PW=${2:-demo-pass}

if [ ! -f "$VAULT_PATH" ]; then
  echo "Creating demo vault at $VAULT_PATH"
  python -m passvault_core.cli create "$VAULT_PATH" --password "$PW" || true
  python -m passvault_core.cli add "$VAULT_PATH" --password "$PW" --name "Email" --username "alice@example.com" --password-field "email-pass"
  python -m passvault_core.cli add "$VAULT_PATH" --password "$PW" --name "Bank" --username "alice" --password-field "bank-pass"
fi

echo "Launch TUI. Use vault: $VAULT_PATH, password: $PW"
export PASSVAULT_PATH="$VAULT_PATH"
export PASSVAULT_PASSWORD="$PW"
python -m passvault_tui.main

#/tmp/passvault_demo.json demo-pass