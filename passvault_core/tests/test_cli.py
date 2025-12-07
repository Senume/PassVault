import sys
import os
import sys
import os

import pytest

pytest.importorskip("cryptography")
pytest.importorskip("argon2.low_level")

from passvault_core import cli


def run_cli(argv):
    old = sys.argv
    try:
        sys.argv = argv
        cli.main()
    finally:
        sys.argv = old


def test_cli_add_list_delete(tmp_path, capsys):
    path = str(tmp_path / "vault.json")
    pw = "cli-test-pass"

    # add an entry (this should create the vault)
    run_cli(["prog", "add", path, "--password", pw, "--name", "example", "--username", "u", "--password-field", "p"])
    # list entries
    run_cli(["prog", "list", path, "--password", pw])
    captured = capsys.readouterr()
    assert "1. example" in captured.out

    # delete entry
    run_cli(["prog", "delete", path, "--password", pw, "--name", "example"])
    # listing now should show no items
    run_cli(["prog", "list", path, "--password", pw])
    captured = capsys.readouterr()
    assert "(no items)" in captured.out