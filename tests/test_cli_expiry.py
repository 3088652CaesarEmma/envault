"""Tests for envault.cli_expiry CLI commands."""

import pytest
from click.testing import CliRunner
from unittest.mock import patch, MagicMock

from envault.cli_expiry import expiry_group


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture(autouse=True)
def mock_passphrase(monkeypatch):
    monkeypatch.setattr("envault.cli_expiry.get_passphrase", lambda: "s3cret")


class TestSetExpiryCommand:
    def test_sets_expiry_successfully(self, runner):
        result_data = {"key": "API_KEY", "expires_at": 9999999999, "ttl_seconds": 3600}
        with patch("envault.cli_expiry.set_expiry", return_value=result_data):
            result = runner.invoke(expiry_group, ["set", "myvault", "API_KEY", "3600"])
        assert result.exit_code == 0
        assert "API_KEY" in result.output
        assert "3600" in result.output

    def test_handles_missing_key_error(self, runner):
        with patch("envault.cli_expiry.set_expiry", side_effect=KeyError("API_KEY")):
            result = runner.invoke(expiry_group, ["set", "myvault", "API_KEY", "60"])
        assert result.exit_code == 1
        assert "Error" in result.output


class TestClearExpiryCommand:
    def test_clears_expiry_successfully(self, runner):
        with patch("envault.cli_expiry.clear_expiry"):
            result = runner.invoke(expiry_group, ["clear", "myvault", "API_KEY"])
        assert result.exit_code == 0
        assert "cleared" in result.output

    def test_handles_missing_key_error(self, runner):
        with patch("envault.cli_expiry.clear_expiry", side_effect=KeyError("API_KEY")):
            result = runner.invoke(expiry_group, ["clear", "myvault", "API_KEY"])
        assert result.exit_code == 1


class TestListExpiredCommand:
    def test_lists_expired_keys(self, runner):
        with patch("envault.cli_expiry.list_expired_keys", return_value=["OLD_TOKEN", "STALE_KEY"]):
            result = runner.invoke(expiry_group, ["list-expired", "myvault"])
        assert result.exit_code == 0
        assert "OLD_TOKEN" in result.output
        assert "STALE_KEY" in result.output

    def test_shows_message_when_none_expired(self, runner):
        with patch("envault.cli_expiry.list_expired_keys", return_value=[]):
            result = runner.invoke(expiry_group, ["list-expired", "myvault"])
        assert result.exit_code == 0
        assert "No expired" in result.output


class TestPurgeExpiredCommand:
    def test_purges_expired_keys(self, runner):
        with patch("envault.cli_expiry.purge_expired_keys", return_value=["OLD"]):
            result = runner.invoke(expiry_group, ["purge", "myvault"], input="y\n")
        assert result.exit_code == 0
        assert "1" in result.output
        assert "OLD" in result.output

    def test_shows_nothing_to_purge(self, runner):
        with patch("envault.cli_expiry.purge_expired_keys", return_value=[]):
            result = runner.invoke(expiry_group, ["purge", "myvault"], input="y\n")
        assert result.exit_code == 0
        assert "Nothing" in result.output
