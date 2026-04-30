"""Tests for the rotate CLI commands."""

import pytest
from click.testing import CliRunner
from unittest.mock import patch
from envault.cli_rotate import rotate_group

OLD_PASS = "OldCorrectHorseBattery1!"
NEW_PASS = "NewCorrectHorseBattery2@"


@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture(autouse=True)
def mock_prompt_new(monkeypatch):
    monkeypatch.setattr(
        "envault.cli_rotate.prompt_new_passphrase", lambda: NEW_PASS
    )


@pytest.fixture(autouse=True)
def mock_strength(monkeypatch):
    monkeypatch.setattr(
        "envault.cli_rotate.validate_passphrase_strength", lambda p: []
    )


class TestRotateOneCommand:
    def test_rotates_successfully(self, runner):
        summary = {"vault": "myapp", "rotated_keys": ["DB_URL", "SECRET_KEY"], "skipped_keys": []}
        with patch("envault.cli_rotate.rotate_vault_passphrase", return_value=summary):
            result = runner.invoke(
                rotate_group,
                ["vault", "myapp", "--old-passphrase", OLD_PASS, "--new-passphrase", NEW_PASS],
            )
        assert result.exit_code == 0
        assert "2 key(s)" in result.output

    def test_shows_error_on_failure(self, runner):
        with patch(
            "envault.cli_rotate.rotate_vault_passphrase",
            side_effect=ValueError("Bad passphrase"),
        ):
            result = runner.invoke(
                rotate_group,
                ["vault", "myapp", "--old-passphrase", OLD_PASS, "--new-passphrase", NEW_PASS],
            )
        assert result.exit_code != 0
        assert "Bad passphrase" in result.output

    def test_warns_on_weak_passphrase(self, runner, monkeypatch):
        monkeypatch.setattr(
            "envault.cli_rotate.validate_passphrase_strength",
            lambda p: ["Too short"],
        )
        summary = {"vault": "myapp", "rotated_keys": ["K"], "skipped_keys": []}
        with patch("envault.cli_rotate.rotate_vault_passphrase", return_value=summary):
            result = runner.invoke(
                rotate_group,
                ["vault", "myapp", "--old-passphrase", OLD_PASS, "--new-passphrase", NEW_PASS],
            )
        assert "Too short" in result.output


class TestRotateAllCommand:
    def test_rotates_all_successfully(self, runner):
        results = [
            {"vault": "app1", "rotated_keys": ["A"], "skipped_keys": []},
            {"vault": "app2", "rotated_keys": ["B", "C"], "skipped_keys": []},
        ]
        with patch("envault.cli_rotate.rotate_all_vaults", return_value=results):
            result = runner.invoke(
                rotate_group,
                ["all", "--old-passphrase", OLD_PASS, "--new-passphrase", NEW_PASS],
            )
        assert result.exit_code == 0
        assert "app1" in result.output
        assert "app2" in result.output

    def test_exits_nonzero_on_partial_failure(self, runner):
        results = [
            {"vault": "app1", "rotated_keys": ["A"], "skipped_keys": []},
            {"vault": "app2", "error": "Bad passphrase"},
        ]
        with patch("envault.cli_rotate.rotate_all_vaults", return_value=results):
            result = runner.invoke(
                rotate_group,
                ["all", "--old-passphrase", OLD_PASS, "--new-passphrase", NEW_PASS],
            )
        assert result.exit_code != 0
        assert "Bad passphrase" in result.output
