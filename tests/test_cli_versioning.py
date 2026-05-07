"""Tests for envault.cli_versioning."""

from unittest.mock import patch
import pytest
from click.testing import CliRunner
from envault.cli_versioning import version_group


@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture(autouse=True)
def mock_passphrase():
    with patch("envault.cli_versioning.get_passphrase", return_value="secret"):
        yield


class TestPushCmd:
    def test_push_success(self, runner):
        entry = {"value": "val", "timestamp": "2024-01-01T00:00:00+00:00"}
        with patch("envault.cli_versioning.push_version", return_value=entry):
            result = runner.invoke(version_group, ["push", "myvault", "KEY"])
        assert result.exit_code == 0
        assert "Pushed version" in result.output

    def test_push_missing_key_exits_1(self, runner):
        with patch("envault.cli_versioning.push_version", side_effect=KeyError("KEY")):
            result = runner.invoke(version_group, ["push", "myvault", "KEY"])
        assert result.exit_code == 1
        assert "Error" in result.output


class TestListCmd:
    def test_list_shows_versions(self, runner):
        versions = [{"value": "v1", "timestamp": "2024-01-01T00:00:00+00:00"}]
        with patch("envault.cli_versioning.list_versions", return_value=versions):
            result = runner.invoke(version_group, ["list", "myvault", "KEY"])
        assert result.exit_code == 0
        assert "[0]" in result.output

    def test_list_empty_history(self, runner):
        with patch("envault.cli_versioning.list_versions", return_value=[]):
            result = runner.invoke(version_group, ["list", "myvault", "KEY"])
        assert result.exit_code == 0
        assert "No version history" in result.output

    def test_list_missing_key_exits_1(self, runner):
        with patch("envault.cli_versioning.list_versions", side_effect=KeyError("KEY")):
            result = runner.invoke(version_group, ["list", "myvault", "KEY"])
        assert result.exit_code == 1


class TestRestoreCmd:
    def test_restore_success(self, runner):
        with patch("envault.cli_versioning.restore_version", return_value="old_val"):
            result = runner.invoke(version_group, ["restore", "myvault", "KEY", "0"])
        assert result.exit_code == 0
        assert "Restored" in result.output

    def test_restore_index_error_exits_1(self, runner):
        with patch("envault.cli_versioning.restore_version", side_effect=IndexError("oob")):
            result = runner.invoke(version_group, ["restore", "myvault", "KEY", "99"])
        assert result.exit_code == 1


class TestClearCmd:
    def test_clear_success(self, runner):
        with patch("envault.cli_versioning.clear_versions", return_value=3):
            result = runner.invoke(
                version_group, ["clear", "myvault", "KEY"], input="y\n"
            )
        assert result.exit_code == 0
        assert "3" in result.output

    def test_clear_aborted_on_no(self, runner):
        with patch("envault.cli_versioning.clear_versions") as mock_clear:
            result = runner.invoke(
                version_group, ["clear", "myvault", "KEY"], input="n\n"
            )
        mock_clear.assert_not_called()
