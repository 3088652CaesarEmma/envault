"""Tests for envault/backup.py"""

import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from envault.backup import create_backup, restore_backup, list_backups, delete_backup


PASSPHRASE = "correct-horse-battery-staple"


@pytest.fixture()
def patched(tmp_path):
    """Patch vault dir and backup dir to use tmp_path."""
    backup_dir = tmp_path / "backups"
    backup_dir.mkdir()
    vault_dir = tmp_path / "vaults"
    vault_dir.mkdir()

    secrets_a = {"KEY_A": "value_a"}
    secrets_b = {"KEY_B": "value_b"}

    with (
        patch("envault.backup._get_backup_dir", return_value=backup_dir),
        patch("envault.backup.load_vault", side_effect=lambda name, _pp: {"alpha": secrets_a, "beta": secrets_b}[name]),
        patch("envault.backup.save_vault") as mock_save,
        patch("envault.backup._get_vault_path", side_effect=lambda name: vault_dir / f"{name}.json"),
        patch("envault.backup.record_event"),
    ):
        yield {"backup_dir": backup_dir, "vault_dir": vault_dir, "mock_save": mock_save,
               "secrets_a": secrets_a, "secrets_b": secrets_b}


class TestCreateBackup:
    def test_creates_backup_file(self, patched):
        result = create_backup(["alpha"], PASSPHRASE, label="test1")
        assert (patched["backup_dir"] / "backup_test1.evbak").exists()

    def test_returns_expected_keys(self, patched):
        result = create_backup(["alpha"], PASSPHRASE, label="test2")
        assert "label" in result
        assert "path" in result
        assert "vaults" in result

    def test_label_used_in_filename(self, patched):
        result = create_backup(["alpha"], PASSPHRASE, label="mylabel")
        assert "mylabel" in result["path"]

    def test_payload_is_not_plaintext(self, patched):
        create_backup(["alpha"], PASSPHRASE, label="enc_test")
        raw = json.loads((patched["backup_dir"] / "backup_enc_test.evbak").read_text())
        assert "KEY_A" not in raw["payload"]

    def test_auto_label_when_none_given(self, patched):
        result = create_backup(["alpha"], PASSPHRASE)
        assert result["label"] is not None
        assert len(result["label"]) > 0


class TestRestoreBackup:
    def test_restores_vault(self, patched):
        create_backup(["alpha"], PASSPHRASE, label="r1")
        result = restore_backup("r1", PASSPHRASE, overwrite=True)
        assert "alpha" in result["restored"]

    def test_skips_existing_without_overwrite(self, patched):
        vault_file = patched["vault_dir"] / "alpha.json"
        vault_file.write_text("{}")
        create_backup(["alpha"], PASSPHRASE, label="r2")
        result = restore_backup("r2", PASSPHRASE, overwrite=False)
        assert "alpha" in result["skipped"]
        assert "alpha" not in result["restored"]

    def test_raises_on_missing_backup(self, patched):
        with pytest.raises(FileNotFoundError):
            restore_backup("nonexistent", PASSPHRASE)


class TestListBackups:
    def test_returns_empty_when_no_backups(self, patched):
        assert list_backups() == []

    def test_returns_backup_entries(self, patched):
        create_backup(["alpha"], PASSPHRASE, label="lb1")
        create_backup(["beta"], PASSPHRASE, label="lb2")
        results = list_backups()
        labels = [b["label"] for b in results]
        assert "lb1" in labels
        assert "lb2" in labels

    def test_entry_has_expected_keys(self, patched):
        create_backup(["alpha"], PASSPHRASE, label="lb3")
        entry = list_backups()[0]
        assert "label" in entry
        assert "created_at" in entry
        assert "vaults" in entry


class TestDeleteBackup:
    def test_deletes_file(self, patched):
        create_backup(["alpha"], PASSPHRASE, label="del1")
        delete_backup("del1")
        assert not (patched["backup_dir"] / "backup_del1.evbak").exists()

    def test_raises_on_missing(self, patched):
        with pytest.raises(FileNotFoundError):
            delete_backup("ghost")
