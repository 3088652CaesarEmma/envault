"""Tests for envault/snapshot.py"""

import json
import time
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from envault.snapshot import (
    create_snapshot,
    restore_snapshot,
    list_snapshots,
    delete_snapshot,
    _get_snapshot_path,
)

SAMPLE_SECRETS = {"API_KEY": "abc123", "DB_URL": "postgres://localhost/test"}


@pytest.fixture(autouse=True)
def patch_snapshot_dir(tmp_path, monkeypatch):
    import envault.snapshot as snap_mod
    monkeypatch.setattr(snap_mod, "_SNAPSHOT_DIR", tmp_path / "snapshots")


@pytest.fixture()
def patched_vault():
    with patch("envault.snapshot.load_vault", return_value=SAMPLE_SECRETS) as mock_load, \
         patch("envault.snapshot.save_vault") as mock_save, \
         patch("envault.snapshot.record_event"):
        yield mock_load, mock_save


class TestCreateSnapshot:
    def test_returns_auto_label_when_none_given(self, patched_vault):
        label = create_snapshot("myapp", "passphrase")
        assert label.isdigit()

    def test_uses_provided_label(self, patched_vault):
        label = create_snapshot("myapp", "passphrase", label="v1")
        assert label == "v1"

    def test_snapshot_file_is_created(self, patched_vault, tmp_path):
        import envault.snapshot as snap_mod
        label = create_snapshot("myapp", "passphrase", label="release")
        snapshot_file = snap_mod._SNAPSHOT_DIR / "myapp" / "release.json"
        assert snapshot_file.exists()

    def test_snapshot_file_contains_secrets(self, patched_vault, tmp_path):
        import envault.snapshot as snap_mod
        create_snapshot("myapp", "passphrase", label="v2")
        snapshot_file = snap_mod._SNAPSHOT_DIR / "myapp" / "v2.json"
        data = json.loads(snapshot_file.read_text())
        assert data["secrets"] == SAMPLE_SECRETS
        assert data["vault"] == "myapp"
        assert data["label"] == "v2"


class TestRestoreSnapshot:
    def test_restores_secrets_from_file(self, patched_vault, tmp_path):
        import envault.snapshot as snap_mod
        _, mock_save = patched_vault
        create_snapshot("myapp", "passphrase", label="snap1")
        restored = restore_snapshot("myapp", "snap1", "passphrase")
        assert restored == SAMPLE_SECRETS
        mock_save.assert_called_once_with("myapp", SAMPLE_SECRETS, "passphrase")

    def test_raises_if_snapshot_not_found(self, patched_vault):
        with pytest.raises(FileNotFoundError, match="missing"):
            restore_snapshot("myapp", "missing", "passphrase")


class TestListSnapshots:
    def test_returns_empty_list_when_no_snapshots(self):
        assert list_snapshots("noapp") == []

    def test_lists_created_snapshots(self, patched_vault):
        create_snapshot("myapp", "passphrase", label="a")
        create_snapshot("myapp", "passphrase", label="b")
        snapshots = list_snapshots("myapp")
        labels = [s["label"] for s in snapshots]
        assert "a" in labels and "b" in labels

    def test_snapshot_entry_has_expected_keys(self, patched_vault):
        create_snapshot("myapp", "passphrase", label="check")
        snapshots = list_snapshots("myapp")
        entry = next(s for s in snapshots if s["label"] == "check")
        assert "created_at" in entry
        assert "key_count" in entry
        assert entry["key_count"] == len(SAMPLE_SECRETS)


class TestDeleteSnapshot:
    def test_deletes_existing_snapshot(self, patched_vault):
        import envault.snapshot as snap_mod
        create_snapshot("myapp", "passphrase", label="todel")
        delete_snapshot("myapp", "todel")
        assert not (snap_mod._SNAPSHOT_DIR / "myapp" / "todel.json").exists()

    def test_raises_if_snapshot_missing(self, patched_vault):
        with pytest.raises(FileNotFoundError):
            delete_snapshot("myapp", "ghost")
