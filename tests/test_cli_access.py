"""Tests for envault.cli_access CLI commands."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from envault.cli_access import access_group

MODULE = "envault.cli_access"


@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture(autouse=True)
def patch_vault_dir(tmp_path):
    with patch(f"{MODULE}.VAULT_DIR", tmp_path / "vaults"):
        yield tmp_path / "vaults"


class TestGrantCommand:
    def test_grant_read_success(self, runner):
        result = runner.invoke(access_group, ["grant", "myapp", "alice", "read"])
        assert result.exit_code == 0
        assert "Granted 'read'" in result.output

    def test_grant_write_success(self, runner):
        result = runner.invoke(access_group, ["grant", "myapp", "alice", "write"])
        assert result.exit_code == 0
        assert "write" in result.output

    def test_grant_invalid_permission_rejected(self, runner):
        result = runner.invoke(access_group, ["grant", "myapp", "alice", "admin"])
        assert result.exit_code != 0


class TestRevokeCommand:
    def test_revoke_success(self, runner, patch_vault_dir):
        runner.invoke(access_group, ["grant", "myapp", "alice", "read"])
        result = runner.invoke(access_group, ["revoke", "myapp", "alice", "read"])
        assert result.exit_code == 0
        assert "Revoked" in result.output


class TestCheckCommand:
    def test_check_allowed(self, runner):
        runner.invoke(access_group, ["grant", "myapp", "alice", "read"])
        result = runner.invoke(access_group, ["check", "myapp", "alice", "read"])
        assert result.exit_code == 0
        assert "ALLOWED" in result.output

    def test_check_denied(self, runner):
        result = runner.invoke(access_group, ["check", "myapp", "alice", "read"])
        assert result.exit_code == 0
        assert "DENIED" in result.output


class TestListCommand:
    def test_list_empty(self, runner):
        result = runner.invoke(access_group, ["list"])
        assert result.exit_code == 0
        assert "No access rules" in result.output

    def test_list_shows_entries(self, runner):
        runner.invoke(access_group, ["grant", "myapp", "alice", "read"])
        result = runner.invoke(access_group, ["list"])
        assert "myapp:alice" in result.output
        assert "read" in result.output

    def test_list_filtered_by_vault(self, runner):
        runner.invoke(access_group, ["grant", "app1", "alice", "read"])
        runner.invoke(access_group, ["grant", "app2", "bob", "write"])
        result = runner.invoke(access_group, ["list", "app1"])
        assert "app1:alice" in result.output
        assert "app2:bob" not in result.output
