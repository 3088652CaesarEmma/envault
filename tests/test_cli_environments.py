"""Tests for envault/cli_environments.py"""

import pytest
from click.testing import CliRunner
from unittest.mock import patch

from envault.cli_environments import environments_group


@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture(autouse=True)
def mock_passphrase():
    with patch("envault.cli_environments.get_passphrase", return_value="secret"):
        yield


def test_set_env_success(runner):
    with patch("envault.cli_environments.set_environment") as mock_set:
        result = runner.invoke(environments_group, ["set", "myvault", "DB_URL", "prod"])
        assert result.exit_code == 0
        assert "prod" in result.output
        mock_set.assert_called_once_with("myvault", "DB_URL", "prod", "secret")


def test_set_env_missing_key_exits_1(runner):
    with patch("envault.cli_environments.set_environment", side_effect=KeyError("DB_URL")):
        result = runner.invoke(environments_group, ["set", "myvault", "DB_URL", "dev"])
        assert result.exit_code == 1


def test_get_env_shows_value(runner):
    with patch("envault.cli_environments.get_environment", return_value="staging"):
        result = runner.invoke(environments_group, ["get", "myvault", "API_KEY"])
        assert result.exit_code == 0
        assert "staging" in result.output


def test_get_env_shows_none_when_unset(runner):
    with patch("envault.cli_environments.get_environment", return_value=None):
        result = runner.invoke(environments_group, ["get", "myvault", "API_KEY"])
        assert result.exit_code == 0
        assert "(none)" in result.output


def test_get_env_missing_key_exits_1(runner):
    with patch("envault.cli_environments.get_environment", side_effect=KeyError("X")):
        result = runner.invoke(environments_group, ["get", "myvault", "X"])
        assert result.exit_code == 1


def test_clear_env_success(runner):
    with patch("envault.cli_environments.clear_environment") as mock_clear:
        result = runner.invoke(environments_group, ["clear", "myvault", "DB_URL"])
        assert result.exit_code == 0
        assert "Cleared" in result.output
        mock_clear.assert_called_once()


def test_list_env_with_results(runner):
    with patch("envault.cli_environments.list_by_environment", return_value=["DB_URL", "REDIS_URL"]):
        result = runner.invoke(environments_group, ["list", "myvault", "prod"])
        assert result.exit_code == 0
        assert "DB_URL" in result.output
        assert "REDIS_URL" in result.output


def test_list_env_empty(runner):
    with patch("envault.cli_environments.list_by_environment", return_value=[]):
        result = runner.invoke(environments_group, ["list", "myvault", "test"])
        assert result.exit_code == 0
        assert "No keys" in result.output
