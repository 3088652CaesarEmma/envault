"""Tests for envault.annotations."""

from __future__ import annotations

import pytest
from unittest.mock import patch, MagicMock

from envault import annotations as ann_mod


PASSPHRASE = "test-passphrase"
VAULT = "myvault"


def _make_vault(data: dict):
    """Return a mock vault dict for patching load_vault."""
    return dict(data)


@pytest.fixture(autouse=True)
def no_audit():
    with patch("envault.annotations.record_event"):
        yield


class TestSetAnnotation:
    def test_sets_annotation_on_plain_value(self):
        vault = _make_vault({"DB_URL": "postgres://localhost"})
        with patch("envault.annotations.load_vault", return_value=vault), \
             patch("envault.annotations.save_vault") as mock_save:
            result = ann_mod.set_annotation(VAULT, "DB_URL", "Primary DB", PASSPHRASE)
        assert result["value"] == "postgres://localhost"
        assert result["annotation"] == "Primary DB"
        mock_save.assert_called_once()

    def test_sets_annotation_on_dict_value(self):
        vault = _make_vault({"API_KEY": {"value": "abc123", "tags": ["prod"]}})
        with patch("envault.annotations.load_vault", return_value=vault), \
             patch("envault.annotations.save_vault"):
            result = ann_mod.set_annotation(VAULT, "API_KEY", "Production key", PASSPHRASE)
        assert result["annotation"] == "Production key"
        assert result["tags"] == ["prod"]

    def test_raises_on_missing_key(self):
        vault = _make_vault({})
        with patch("envault.annotations.load_vault", return_value=vault):
            with pytest.raises(KeyError, match="DB_URL"):
                ann_mod.set_annotation(VAULT, "DB_URL", "note", PASSPHRASE)


class TestGetAnnotation:
    def test_returns_annotation_when_set(self):
        vault = _make_vault({"KEY": {"value": "val", "annotation": "my note"}})
        with patch("envault.annotations.load_vault", return_value=vault):
            result = ann_mod.get_annotation(VAULT, "KEY", PASSPHRASE)
        assert result == "my note"

    def test_returns_none_for_plain_string(self):
        vault = _make_vault({"KEY": "plain"})
        with patch("envault.annotations.load_vault", return_value=vault):
            result = ann_mod.get_annotation(VAULT, "KEY", PASSPHRASE)
        assert result is None

    def test_returns_none_when_annotation_absent(self):
        vault = _make_vault({"KEY": {"value": "v"}})
        with patch("envault.annotations.load_vault", return_value=vault):
            result = ann_mod.get_annotation(VAULT, "KEY", PASSPHRASE)
        assert result is None

    def test_raises_on_missing_key(self):
        vault = _make_vault({})
        with patch("envault.annotations.load_vault", return_value=vault):
            with pytest.raises(KeyError):
                ann_mod.get_annotation(VAULT, "MISSING", PASSPHRASE)


class TestClearAnnotation:
    def test_removes_annotation(self):
        vault = _make_vault({"KEY": {"value": "v", "annotation": "old note"}})
        with patch("envault.annotations.load_vault", return_value=vault), \
             patch("envault.annotations.save_vault") as mock_save:
            ann_mod.clear_annotation(VAULT, "KEY", PASSPHRASE)
        assert "annotation" not in vault["KEY"]
        mock_save.assert_called_once()

    def test_noop_when_no_annotation(self):
        vault = _make_vault({"KEY": {"value": "v"}})
        with patch("envault.annotations.load_vault", return_value=vault), \
             patch("envault.annotations.save_vault") as mock_save:
            ann_mod.clear_annotation(VAULT, "KEY", PASSPHRASE)
        mock_save.assert_not_called()


class TestListAnnotatedKeys:
    def test_returns_annotated_entries(self):
        vault = _make_vault({
            "A": {"value": "1", "annotation": "note A"},
            "B": "plain",
            "C": {"value": "3", "annotation": "note C"},
        })
        with patch("envault.annotations.load_vault", return_value=vault):
            results = ann_mod.list_annotated_keys(VAULT, PASSPHRASE)
        keys = [r["key"] for r in results]
        assert "A" in keys
        assert "C" in keys
        assert "B" not in keys

    def test_returns_empty_when_none_annotated(self):
        vault = _make_vault({"X": "val", "Y": {"value": "v"}})
        with patch("envault.annotations.load_vault", return_value=vault):
            results = ann_mod.list_annotated_keys(VAULT, PASSPHRASE)
        assert results == []
