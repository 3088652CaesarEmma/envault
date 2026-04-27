import pytest
from click.testing import CliRunner
from unittest.mock import patch, MagicMock
from envault.cli_vault import vault_group


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def mock_passphrase():
    with patch("envault.cli_vault.get_passphrase", return_value="StrongPass123!") as m:
        yield m


class TestCreateVaultCommand:
    def test_creates_vault_successfully(self, runner, mock_passphrase):
        with patch("envault.cli_vault.save_vault") as mock_save:
            result = runner.invoke(vault_group, ["create", "myproject"])
            assert result.exit_code == 0
            assert "created successfully" in result.output
            mock_save.assert_called_once_with("myproject", {}, "StrongPass123!")

    def test_create_vault_handles_error(self, runner):
        with patch(
            "envault.cli_vault.get_passphrase", side_effect=ValueError("No passphrase")
        ):
            result = runner.invoke(vault_group, ["create", "myproject"])
            assert result.exit_code == 1
            assert "Error" in result.output


class TestListVaultsCommand:
    def test_lists_vaults(self, runner):
        with patch(
            "envault.cli_vault.list_vaults", return_value=["proj1", "proj2"]
        ):
            result = runner.invoke(vault_group, ["list"])
            assert result.exit_code == 0
            assert "proj1" in result.output
            assert "proj2" in result.output

    def test_shows_message_when_no_vaults(self, runner):
        with patch("envault.cli_vault.list_vaults", return_value=[]):
            result = runner.invoke(vault_group, ["list"])
            assert result.exit_code == 0
            assert "No vaults found" in result.output


class TestDeleteVaultCommand:
    def test_deletes_vault_with_confirmation(self, runner, tmp_path):
        fake_vault = tmp_path / "myproject.vault"
        fake_vault.touch()
        with patch("envault.cli_vault._get_vault_path", return_value=fake_vault):
            result = runner.invoke(vault_group, ["delete", "myproject", "--yes"])
            assert result.exit_code == 0
            assert "deleted" in result.output
            assert not fake_vault.exists()

    def test_delete_aborts_without_confirmation(self, runner, tmp_path):
        fake_vault = tmp_path / "myproject.vault"
        fake_vault.touch()
        with patch("envault.cli_vault._get_vault_path", return_value=fake_vault):
            result = runner.invoke(vault_group, ["delete", "myproject"], input="n\n")
            assert result.exit_code == 0
            assert "Aborted" in result.output
            assert fake_vault.exists()

    def test_delete_nonexistent_vault(self, runner, tmp_path):
        nonexistent = tmp_path / "ghost.vault"
        with patch("envault.cli_vault._get_vault_path", return_value=nonexistent):
            result = runner.invoke(vault_group, ["delete", "ghost", "--yes"])
            assert result.exit_code == 1


class TestVaultInfoCommand:
    def test_shows_vault_info(self, runner, mock_passphrase):
        with patch(
            "envault.cli_vault.load_vault",
            return_value={"KEY1": "val1", "KEY2": "val2"},
        ):
            result = runner.invoke(vault_group, ["info", "myproject"])
            assert result.exit_code == 0
            assert "myproject" in result.output
            assert "2" in result.output

    def test_info_vault_not_found(self, runner, mock_passphrase):
        with patch(
            "envault.cli_vault.load_vault", side_effect=FileNotFoundError
        ):
            result = runner.invoke(vault_group, ["info", "missing"])
            assert result.exit_code == 1
            assert "not found" in result.output
