"""Tests for envault/diff.py and envault/cli_diff.py."""

import json
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from envault.cli_diff import diff_group
from envault.diff import DiffEntry, diff_vault_vs_env, format_diff


# --- Unit tests for diff logic ---

class TestDiffVaultVsEnv:
    def test_detects_added_key(self):
        entries = diff_vault_vs_env({}, {"NEW_KEY": "value"})
        assert any(e.key == "NEW_KEY" and e.status == "added" for e in entries)

    def test_detects_removed_key(self):
        entries = diff_vault_vs_env({"OLD_KEY": "value"}, {})
        assert any(e.key == "OLD_KEY" and e.status == "removed" for e in entries)

    def test_detects_modified_key(self):
        entries = diff_vault_vs_env({"KEY": "old"}, {"KEY": "new"})
        assert any(e.key == "KEY" and e.status == "modified" for e in entries)

    def test_detects_unchanged_key(self):
        entries = diff_vault_vs_env({"KEY": "same"}, {"KEY": "same"})
        assert any(e.key == "KEY" and e.status == "unchanged" for e in entries)

    def test_returns_sorted_keys(self):
        vault = {"ZEBRA": "z", "APPLE": "a"}
        env = {"MANGO": "m"}
        entries = diff_vault_vs_env(vault, env)
        keys = [e.key for e in entries]
        assert keys == sorted(keys)

    def test_empty_both_returns_empty(self):
        assert diff_vault_vs_env({}, {}) == []


class TestFormatDiff:
    def test_added_uses_plus_symbol(self):
        entries = [DiffEntry(key="KEY", status="added", env_value="val")]
        output = format_diff(entries)
        assert output.startswith("+ KEY")

    def test_removed_uses_minus_symbol(self):
        entries = [DiffEntry(key="KEY", status="removed", vault_value="val")]
        output = format_diff(entries)
        assert output.startswith("- KEY")

    def test_modified_shows_values_when_flag_set(self):
        entries = [DiffEntry(key="KEY", status="modified", vault_value="old", env_value="new")]
        output = format_diff(entries, show_values=True)
        assert "old" in output and "new" in output

    def test_modified_hides_values_by_default(self):
        entries = [DiffEntry(key="KEY", status="modified", vault_value="old", env_value="new")]
        output = format_diff(entries, show_values=False)
        assert "old" not in output


# --- CLI integration tests ---

@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def mock_passphrase():
    with patch("envault.cli_diff.get_passphrase", return_value="masterpass"):
        yield


class TestShowDiffCommand:
    def test_shows_diff_output(self, runner, mock_passphrase, tmp_path):
        env_file = tmp_path / ".env"
        env_file.write_text("NEW_KEY=value\nSHARED=same\n")

        vault_data = {"secrets": {"SHARED": "same", "OLD_KEY": "gone"}}
        with patch("envault.cli_diff.load_vault", return_value=vault_data), \
             patch("envault.cli_diff.record_event"):
            result = runner.invoke(diff_group, ["show", "myvault", str(env_file)])

        assert result.exit_code == 0
        assert "NEW_KEY" in result.output
        assert "OLD_KEY" in result.output
        assert "Summary" in result.output

    def test_filter_by_only_added(self, runner, mock_passphrase, tmp_path):
        env_file = tmp_path / ".env"
        env_file.write_text("EXTRA=val\n")

        vault_data = {"secrets": {}}
        with patch("envault.cli_diff.load_vault", return_value=vault_data), \
             patch("envault.cli_diff.record_event"):
            result = runner.invoke(diff_group, ["show", "myvault", str(env_file), "--only", "added"])

        assert result.exit_code == 0
        assert "EXTRA" in result.output

    def test_handles_vault_load_error(self, runner, mock_passphrase, tmp_path):
        env_file = tmp_path / ".env"
        env_file.write_text("KEY=val\n")

        with patch("envault.cli_diff.load_vault", side_effect=Exception("not found")):
            result = runner.invoke(diff_group, ["show", "missing", str(env_file)])

        assert result.exit_code == 1
        assert "Error loading vault" in result.output
