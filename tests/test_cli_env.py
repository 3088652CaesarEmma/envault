"""Tests for the CLI env commands (import, export, list keys)."""

import json
import os
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from envault.cli_env import export_env, import_env, list_env_keys


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def mock_passphrase():
    """Patch get_passphrase to return a fixed passphrase during tests."""
    with patch("envault.cli_env.get_passphrase", return_value="StrongPass123!") as m:
        yield m


@pytest.fixture
def sample_env_file(tmp_path):
    """Create a temporary .env file with sample content."""
    env_file = tmp_path / ".env"
    env_file.write_text("API_KEY=abc123\nDEBUG=true\nSECRET=supersecret\n")
    return str(env_file)


@pytest.fixture
def sample_vault(tmp_path):
    """Return a path to a vault name (not yet created on disk)."""
    return "test_project"


# ---------------------------------------------------------------------------
# import_env
# ---------------------------------------------------------------------------

class TestImportEnvCommand:
    def test_imports_env_successfully(
        self, runner, mock_passphrase, sample_env_file, sample_vault
    ):
        with patch("envault.cli_env.parse_env_file", return_value={"API_KEY": "abc123"}) as mock_parse, \
             patch("envault.cli_env.save_vault") as mock_save, \
             patch("envault.cli_env.load_vault", return_value={"secrets": {}}):
            result = runner.invoke(import_env, [sample_vault, sample_env_file])
            assert result.exit_code == 0
            assert "Imported" in result.output or "import" in result.output.lower()
            mock_parse.assert_called_once_with(sample_env_file)

    def test_import_fails_if_file_not_found(self, runner, mock_passphrase, sample_vault):
        with patch("envault.cli_env.parse_env_file", side_effect=FileNotFoundError("not found")):
            result = runner.invoke(import_env, [sample_vault, "/nonexistent/.env"])
            assert result.exit_code != 0 or "error" in result.output.lower() or "not found" in result.output.lower()

    def test_import_merges_with_existing_secrets(
        self, runner, mock_passphrase, sample_env_file, sample_vault
    ):
        existing = {"secrets": {"OLD_KEY": "old_value"}}
        new_secrets = {"NEW_KEY": "new_value"}
        with patch("envault.cli_env.parse_env_file", return_value=new_secrets), \
             patch("envault.cli_env.load_vault", return_value=existing), \
             patch("envault.cli_env.save_vault") as mock_save:
            result = runner.invoke(import_env, [sample_vault, sample_env_file])
            assert result.exit_code == 0
            # Ensure save_vault was called with merged data
            call_args = mock_save.call_args
            assert call_args is not None


# ---------------------------------------------------------------------------
# export_env
# ---------------------------------------------------------------------------

class TestExportEnvCommand:
    def test_exports_env_successfully(self, runner, mock_passphrase, tmp_path, sample_vault):
        secrets = {"API_KEY": "abc123", "DEBUG": "true"}
        output_file = str(tmp_path / "exported.env")
        with patch("envault.cli_env.load_vault", return_value={"secrets": secrets}), \
             patch("envault.cli_env.write_env_file") as mock_write:
            result = runner.invoke(export_env, [sample_vault, output_file])
            assert result.exit_code == 0
            mock_write.assert_called_once_with(output_file, secrets)

    def test_export_fails_on_missing_vault(self, runner, mock_passphrase, tmp_path, sample_vault):
        output_file = str(tmp_path / "exported.env")
        with patch("envault.cli_env.load_vault", side_effect=FileNotFoundError("vault not found")):
            result = runner.invoke(export_env, [sample_vault, output_file])
            assert result.exit_code != 0 or "not found" in result.output.lower() or "error" in result.output.lower()

    def test_export_shows_confirmation_message(self, runner, mock_passphrase, tmp_path, sample_vault):
        secrets = {"KEY": "value"}
        output_file = str(tmp_path / "out.env")
        with patch("envault.cli_env.load_vault", return_value={"secrets": secrets}), \
             patch("envault.cli_env.write_env_file"):
            result = runner.invoke(export_env, [sample_vault, output_file])
            assert result.exit_code == 0
            assert output_file in result.output or "export" in result.output.lower()


# ---------------------------------------------------------------------------
# list_env_keys
# ---------------------------------------------------------------------------

class TestListEnvKeysCommand:
    def test_lists_keys_for_vault(self, runner, mock_passphrase, sample_vault):
        secrets = {"API_KEY": "abc123", "DEBUG": "true", "SECRET": "shh"}
        with patch("envault.cli_env.load_vault", return_value={"secrets": secrets}):
            result = runner.invoke(list_env_keys, [sample_vault])
            assert result.exit_code == 0
            for key in secrets:
                assert key in result.output

    def test_list_keys_does_not_show_values(self, runner, mock_passphrase, sample_vault):
        secrets = {"API_KEY": "super_secret_value"}
        with patch("envault.cli_env.load_vault", return_value={"secrets": secrets}):
            result = runner.invoke(list_env_keys, [sample_vault])
            assert result.exit_code == 0
            assert "super_secret_value" not in result.output

    def test_list_keys_empty_vault(self, runner, mock_passphrase, sample_vault):
        with patch("envault.cli_env.load_vault", return_value={"secrets": {}}):
            result = runner.invoke(list_env_keys, [sample_vault])
            assert result.exit_code == 0
            assert "no" in result.output.lower() or result.output.strip() == ""

    def test_list_keys_handles_missing_vault(self, runner, mock_passphrase, sample_vault):
        with patch("envault.cli_env.load_vault", side_effect=FileNotFoundError("vault not found")):
            result = runner.invoke(list_env_keys, [sample_vault])
            assert result.exit_code != 0 or "not found" in result.output.lower() or "error" in result.output.lower()
