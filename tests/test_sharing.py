"""Tests for envault.sharing and envault.cli_sharing."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from envault.sharing import export_share, import_share
from envault.cli_sharing import share_group


SECRETS = {"DB_URL": "postgres://localhost/test", "SECRET_KEY": "abc123"}
PASSPHRASE = "master-pass-correct-horse"
SHARE_PASS = "share-battery-staple"


@pytest.fixture()
def patched(tmp_path):
    """Patch vault I/O and audit so tests stay hermetic."""
    with (
        patch("envault.sharing.load_vault", return_value=dict(SECRETS)) as mock_load,
        patch("envault.sharing.save_vault") as mock_save,
        patch("envault.sharing.record_event") as mock_audit,
    ):
        yield {"load": mock_load, "save": mock_save, "audit": mock_audit}


class TestExportShare:
    def test_returns_bundle_with_expected_keys(self, patched):
        bundle = export_share("myapp", PASSPHRASE, SHARE_PASS)
        assert {"version", "vault", "salt", "ciphertext"} <= bundle.keys()

    def test_vault_name_stored_in_bundle(self, patched):
        bundle = export_share("myapp", PASSPHRASE, SHARE_PASS)
        assert bundle["vault"] == "myapp"

    def test_ciphertext_is_not_plaintext(self, patched):
        bundle = export_share("myapp", PASSPHRASE, SHARE_PASS)
        assert "DB_URL" not in bundle["ciphertext"]

    def test_records_audit_event(self, patched):
        export_share("myapp", PASSPHRASE, SHARE_PASS)
        patched["audit"].assert_called_once()
        assert patched["audit"].call_args[0][0] == "share_export"


class TestImportShare:
    def _make_bundle(self):
        with (
            patch("envault.sharing.load_vault", return_value=dict(SECRETS)),
            patch("envault.sharing.save_vault"),
            patch("envault.sharing.record_event"),
        ):
            return export_share("myapp", PASSPHRASE, SHARE_PASS)

    def test_round_trip_restores_secrets(self, patched):
        bundle = self._make_bundle()
        patched["load"].side_effect = FileNotFoundError
        result = import_share(bundle, SHARE_PASS, "newapp", PASSPHRASE)
        assert result == SECRETS

    def test_save_vault_called_with_target(self, patched):
        bundle = self._make_bundle()
        patched["load"].side_effect = FileNotFoundError
        import_share(bundle, SHARE_PASS, "newapp", PASSPHRASE)
        patched["save"].assert_called_once()
        args = patched["save"].call_args[0]
        assert args[0] == "newapp"

    def test_merge_preserves_existing_keys(self, patched):
        bundle = self._make_bundle()
        patched["load"].side_effect = None
        patched["load"].return_value = {"EXISTING": "value", "DB_URL": "old"}
        result = import_share(bundle, SHARE_PASS, "newapp", PASSPHRASE, merge=True)
        assert result["EXISTING"] == "value"
        assert result["DB_URL"] == SECRETS["DB_URL"]

    def test_wrong_share_passphrase_raises(self, patched):
        bundle = self._make_bundle()
        with pytest.raises(Exception):
            import_share(bundle, "wrong-passphrase", "newapp", PASSPHRASE)

    def test_bad_version_raises(self, patched):
        bundle = self._make_bundle()
        bundle["version"] = 99
        with pytest.raises(ValueError, match="Unsupported"):
            import_share(bundle, SHARE_PASS, "newapp", PASSPHRASE)


class TestCLIShareExport:
    def test_export_prints_json_to_stdout(self, patched):
        runner = CliRunner()
        with (
            patch("envault.cli_sharing.get_passphrase", return_value=PASSPHRASE),
            patch("envault.cli_sharing.prompt_new_passphrase", return_value=SHARE_PASS),
            patch("envault.cli_sharing.export_share", return_value={"version": 1, "vault": "myapp", "salt": "s", "ciphertext": "c"}) as mock_exp,
        ):
            result = runner.invoke(share_group, ["export", "myapp"])
        assert result.exit_code == 0
        assert "version" in result.output

    def test_export_error_exits_nonzero(self):
        runner = CliRunner()
        with (
            patch("envault.cli_sharing.get_passphrase", return_value=PASSPHRASE),
            patch("envault.cli_sharing.prompt_new_passphrase", return_value=SHARE_PASS),
            patch("envault.cli_sharing.export_share", side_effect=RuntimeError("boom")),
        ):
            result = runner.invoke(share_group, ["export", "myapp"])
        assert result.exit_code != 0
