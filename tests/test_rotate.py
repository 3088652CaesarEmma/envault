"""Tests for envault.rotate passphrase rotation."""

import pytest
from unittest.mock import patch, MagicMock
from envault.rotate import rotate_vault_passphrase, rotate_all_vaults


OLD_PASS = "OldCorrectHorseBattery1!"
NEW_PASS = "NewCorrectHorseBattery2@"
VAULT_NAME = "myapp"
SECRETS = {"DB_URL": "postgres://localhost/db", "SECRET_KEY": "abc123"}


@pytest.fixture()
def patched_vault(tmp_path):
    """Patch load_vault, save_vault, list_vaults and record_event."""
    with (
        patch("envault.rotate.load_vault") as mock_load,
        patch("envault.rotate.save_vault") as mock_save,
        patch("envault.rotate.list_vaults") as mock_list,
        patch("envault.rotate.record_event") as mock_audit,
    ):
        mock_load.return_value = {"secrets": SECRETS.copy()}
        mock_list.return_value = [VAULT_NAME, "otherapp"]
        yield {
            "load": mock_load,
            "save": mock_save,
            "list": mock_list,
            "audit": mock_audit,
        }


class TestRotateVaultPassphrase:
    def test_returns_summary_with_rotated_keys(self, patched_vault):
        result = rotate_vault_passphrase(VAULT_NAME, OLD_PASS, NEW_PASS)
        assert result["vault"] == VAULT_NAME
        assert set(result["rotated_keys"]) == set(SECRETS.keys())
        assert result["skipped_keys"] == []

    def test_calls_save_vault_with_new_passphrase(self, patched_vault):
        rotate_vault_passphrase(VAULT_NAME, OLD_PASS, NEW_PASS)
        patched_vault["save"].assert_called_once_with(
            VAULT_NAME, SECRETS, NEW_PASS, vault_dir=None
        )

    def test_records_audit_event(self, patched_vault):
        rotate_vault_passphrase(VAULT_NAME, OLD_PASS, NEW_PASS)
        patched_vault["audit"].assert_called_once()
        args = patched_vault["audit"].call_args[0]
        assert args[0] == "rotate_passphrase"
        assert args[1]["vault"] == VAULT_NAME

    def test_skips_none_values(self, patched_vault):
        patched_vault["load"].return_value = {
            "secrets": {"KEY": "value", "EMPTY": None}
        }
        result = rotate_vault_passphrase(VAULT_NAME, OLD_PASS, NEW_PASS)
        assert "EMPTY" in result["skipped_keys"]
        assert "KEY" in result["rotated_keys"]

    def test_raises_on_load_failure(self, patched_vault):
        patched_vault["load"].side_effect = ValueError("Bad passphrase")
        with pytest.raises(ValueError, match="Bad passphrase"):
            rotate_vault_passphrase(VAULT_NAME, OLD_PASS, NEW_PASS)


class TestRotateAllVaults:
    def test_rotates_all_vaults(self, patched_vault):
        results = rotate_all_vaults(OLD_PASS, NEW_PASS)
        assert len(results) == 2
        assert all("vault" in r for r in results)

    def test_records_error_on_failure(self, patched_vault):
        def fail_on_other(name, *args, **kwargs):
            if name == "otherapp":
                raise ValueError("Wrong passphrase")
            return {"secrets": SECRETS.copy()}

        patched_vault["load"].side_effect = fail_on_other
        results = rotate_all_vaults(OLD_PASS, NEW_PASS)
        errors = [r for r in results if "error" in r]
        assert len(errors) == 1
        assert errors[0]["vault"] == "otherapp"

    def test_successful_vaults_still_saved(self, patched_vault):
        patched_vault["load"].side_effect = [
            {"secrets": SECRETS.copy()},
            ValueError("fail"),
        ]
        rotate_all_vaults(OLD_PASS, NEW_PASS)
        assert patched_vault["save"].call_count == 1
