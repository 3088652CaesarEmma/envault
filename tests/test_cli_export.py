"""Tests for envault/cli_export.py"""

import json
import pytest
from click.testing import CliRunner
from unittest.mock import patch, MagicMock

from envault.cli_export import export_group

SAMPLE_VAULT = {"secrets": {"DB_HOST": "localhost", "API_KEY": "secret"}}


@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture(autouse=True)
def mock_passphrase():
    with patch("envault.cli_export.get_passphrase", return_value="strongpass"):
        yield


@pytest.fixture(autouse=True)
def mock_audit():
    with patch("envault.cli_export.record_event"):
        yield


class TestRenderVaultCommand:
    def test_default_format_is_dotenv(self, runner):
        with patch("envault.cli_export.load_vault", return_value=SAMPLE_VAULT):
            result = runner.invoke(export_group, ["render", "myvault"])
        assert result.exit_code == 0
        assert "DB_HOST=localhost" in result.output

    def test_json_format_output(self, runner):
        with patch("envault.cli_export.load_vault", return_value=SAMPLE_VAULT):
            result = runner.invoke(export_group, ["render", "myvault", "--format", "json"])
        assert result.exit_code == 0
        parsed = json.loads(result.output)
        assert parsed["DB_HOST"] == "localhost"

    def test_shell_format_output(self, runner):
        with patch("envault.cli_export.load_vault", return_value=SAMPLE_VAULT):
            result = runner.invoke(export_group, ["render", "myvault", "--format", "shell"])
        assert result.exit_code == 0
        assert "export DB_HOST=" in result.output

    def test_write_to_file(self, runner, tmp_path):
        out_file = tmp_path / "out.env"
        with patch("envault.cli_export.load_vault", return_value=SAMPLE_VAULT):
            result = runner.invoke(
                export_group,
                ["render", "myvault", "--output", str(out_file)],
            )
        assert result.exit_code == 0
        assert out_file.exists()
        content = out_file.read_text()
        assert "DB_HOST=localhost" in content

    def test_vault_not_found_exits_with_error(self, runner):
        with patch("envault.cli_export.load_vault", side_effect=FileNotFoundError):
            result = runner.invoke(export_group, ["render", "missing"])
        assert result.exit_code != 0
        assert "not found" in result.output

    def test_load_vault_generic_error(self, runner):
        with patch("envault.cli_export.load_vault", side_effect=Exception("bad decrypt")):
            result = runner.invoke(export_group, ["render", "myvault"])
        assert result.exit_code != 0
        assert "Error loading vault" in result.output

    def test_invalid_format_rejected_by_click(self, runner):
        with patch("envault.cli_export.load_vault", return_value=SAMPLE_VAULT):
            result = runner.invoke(export_group, ["render", "myvault", "--format", "xml"])
        assert result.exit_code != 0
