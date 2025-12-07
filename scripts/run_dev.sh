#!/usr/bin/env bash
set -euo pipefail

python -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -r requirements.txt
python -m passvault_gui.main
