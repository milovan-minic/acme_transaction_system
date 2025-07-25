"""
CLI tests for manage_cli.py (user and currency management).
Uses subprocess to invoke the CLI and a temp SQLite DB for isolation.
"""

import subprocess
import sys
import os
import tempfile
import shutil
import pytest
from db import get_engine
from models import Base

CLI_PATH = os.path.join(os.path.dirname(__file__), "../manage_cli.py")
CLI_PATH = os.path.abspath(CLI_PATH)

@pytest.fixture(scope="function")
def cli_env(monkeypatch):
    # Use a temp DB file for each test
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "cli_test.db")
        monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")
        # Create schema in the new test DB
        engine = get_engine()
        Base.metadata.create_all(engine)
        yield
        # DB file is deleted with the tempdir

def run_cli(args, env=None):
    cmd = [sys.executable, CLI_PATH] + args
    result = subprocess.run(cmd, capture_output=True, text=True, env=env)
    return result

def test_cli_add_and_list_user(cli_env):
    # Add user
    result = run_cli(["add-user", "--id", "cliuser", "--name", "CLI User"])
    assert "Added user cliuser" in result.stdout
    # List users
    result = run_cli(["list-users"])
    assert "cliuser: CLI User" in result.stdout

def test_cli_add_user_duplicate(cli_env):
    run_cli(["add-user", "--id", "cliuser", "--name", "CLI User"])
    result = run_cli(["add-user", "--id", "cliuser", "--name", "CLI User"])
    assert "already exists" in result.stdout

def test_cli_add_and_list_currency(cli_env):
    # Add currency
    result = run_cli(["add-currency", "--code", "CHF", "--name", "Swiss Franc"])
    assert "Added currency CHF" in result.stdout
    # List currencies
    result = run_cli(["list-currencies"])
    assert "CHF: Swiss Franc" in result.stdout

def test_cli_add_currency_duplicate(cli_env):
    run_cli(["add-currency", "--code", "CHF", "--name", "Swiss Franc"])
    result = run_cli(["add-currency", "--code", "CHF", "--name", "Swiss Franc"])
    assert "already exists" in result.stdout 