"""Tests for envault.cli_passphrase CLI commands."""

import pytest
from unittest.mock import patch
from click.testing import CliRunner

import envault.passphrase as passphrase_module
from envault.cli_passphrase import passphrase_group
from envault.passphrase import clear_session_passphrase


@pytest.fixture(autouse=True)
def reset_session():
    clear_session_passphrase()
    yield
    clear_session_passphrase()


@pytest.fixture
def runner():
    return CliRunner()


class TestSetPassphraseCommand:
    def test_sets_passphrase_successfully(self, runner):
        with patch("getpass.getpass", side_effect=["GoodPass1!", "GoodPass1!"]):
            result = runner.invoke(passphrase_group, ["set"])
        assert result.exit_code == 0
        assert "set for current session" in result.output
        assert passphrase_module._session_passphrase == "GoodPass1!"

    def test_warns_on_weak_passphrase(self, runner):
        with patch("getpass.getpass", side_effect=["weakpass", "weakpass"]):
            result = runner.invoke(passphrase_group, ["set"])
        assert "Warning" in result.output

    def test_no_warn_flag_suppresses_warnings(self, runner):
        with patch("getpass.getpass", side_effect=["weakpass", "weakpass"]):
            result = runner.invoke(passphrase_group, ["set", "--no-warn-weak"])
        assert "Warning" not in result.output
        assert result.exit_code == 0


class TestClearPassphraseCommand:
    def test_clears_session_passphrase(self, runner):
        passphrase_module._session_passphrase = "some-secret"
        result = runner.invoke(passphrase_group, ["clear"])
        assert result.exit_code == 0
        assert "cleared" in result.output
        assert passphrase_module._session_passphrase is None


class TestCheckPassphraseCommand:
    def test_strong_passphrase_exits_zero(self, runner):
        result = runner.invoke(passphrase_group, ["check", "Str0ng!Passphrase"])
        assert result.exit_code == 0
        assert "strong" in result.output

    def test_weak_passphrase_exits_nonzero(self, runner):
        result = runner.invoke(passphrase_group, ["check", "weak"])
        assert result.exit_code != 0
        assert "Warning" in result.output
