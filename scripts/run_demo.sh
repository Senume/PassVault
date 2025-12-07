#!/usr/bin/env bash
set -euo pipefail

# Demo launcher for PassVault
# Creates a temporary vault with example entries and launches the GTK UI.
# Requires: conda env 'passvault' (or equivalent), system PyGObject and clipboard tools.

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
VAULT_PATH="/tmp/passvault_demo.json"
PW="demo-pass"

echo "Using repo root: $REPO_ROOT"

if [ -z "${CONDA_PREFIX:-}" ]; then
  echo "Warning: Conda env not active. You should activate your 'passvault' env first:"
  echo "  conda activate passvault"
fi

export PYTHONPATH="$REPO_ROOT"

echo "Creating demo vault at $VAULT_PATH"
python -m passvault_core.cli create "$VAULT_PATH" --password "$PW" || true

echo "Adding sample entries"
python -m passvault_core.cli add "$VAULT_PATH" --password "$PW" --name "Email" --username "alice@example.com" --password-field "email-pass"
python -m passvault_core.cli add "$VAULT_PATH" --password "$PW" --name "Bank" --username "alice" --password-field "bank-pass"

echo "Launching GUI (unlock using password: $PW)"
python -m passvault_gui.main
