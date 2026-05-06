"""Tests for envault/cli_backup.py"""

import pytest
from click.testing import CliRunner
from unittest.mock import patch

from envault.cli_backup import backup_group


@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture(autouse=True)
def mock_passphrase():
    with patch("envault.cli_backup.get_passphrase", return_value="s3cr3t-passphrase"):
        yield


class TestCreateCmd:
    def test_creates_successfully(self, runner):
        with patch("envault.cli_backup.create_backup", return_value={"label": "lbl", "path": "/tmp/x.evbak", "vaults": ["myvault"]}) as m:
            result = runner.invoke(backup_group, ["create", "myvault"])
        assert result.exit_code == 0
        assert "lbl" in result.output

    def test_uses_label_option(self, runner):
        with patch("envault.cli_backup.create_backup", return_value={"label": "custom", "path": "/tmp/c.evbak", "vaults": ["v"]}) as m:
            runner.invoke(backup_group, ["create", "v", "--label", "custom"])
        m.assert_called_once_with(["v"], "s3cr3t-passphrase", label="custom")

    def test_handles_error(self, runner):
        with patch("envault.cli_backup.create_backup", side_effect=Exception("boom")):
            result = runner.invoke(backup_group, ["create", "v"])
        assert result.exit_code == 1
        assert "boom" in result.output


class TestRestoreCmd:
    def test_restores_successfully(self, runner):
        with patch("envault.cli_backup.restore_backup", return_value={"restored": ["v1"], "skipped": []}):
            result = runner.invoke(backup_group, ["restore", "lbl1"])
        assert result.exit_code == 0
        assert "v1" in result.output

    def test_shows_skipped_vaults(self, runner):
        with patch("envault.cli_backup.restore_backup", return_value={"restored": [], "skipped": ["v1"]}):
            result = runner.invoke(backup_group, ["restore", "lbl2"])
        assert "Skipped" in result.output

    def test_handles_not_found(self, runner):
        with patch("envault.cli_backup.restore_backup", side_effect=FileNotFoundError("no backup")):
            result = runner.invoke(backup_group, ["restore", "ghost"])
        assert result.exit_code == 1


class TestListCmd:
    def test_shows_backups(self, runner):
        with patch("envault.cli_backup.list_backups", return_value=[
            {"label": "bk1", "created_at": "2024-01-01T00:00:00Z", "vaults": ["v1"]}
        ]):
            result = runner.invoke(backup_group, ["list"])
        assert "bk1" in result.output

    def test_shows_empty_message(self, runner):
        with patch("envault.cli_backup.list_backups", return_value=[]):
            result = runner.invoke(backup_group, ["list"])
        assert "No backups" in result.output


class TestDeleteCmd:
    def test_deletes_with_confirmation(self, runner):
        with patch("envault.cli_backup.delete_backup") as m:
            result = runner.invoke(backup_group, ["delete", "bk1"], input="y\n")
        assert result.exit_code == 0
        m.assert_called_once_with("bk1")

    def test_handles_not_found(self, runner):
        with patch("envault.cli_backup.delete_backup", side_effect=FileNotFoundError("missing")):
            result = runner.invoke(backup_group, ["delete", "ghost"], input="y\n")
        assert result.exit_code == 1
