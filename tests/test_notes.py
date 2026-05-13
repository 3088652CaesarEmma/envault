"""Tests for envault.notes."""

from __future__ import annotations

import pytest
from unittest.mock import patch, MagicMock

from envault import notes as notes_mod


def _make_vault(data: dict):
    """Return (load_mock, save_mock) patched onto envault.notes."""
    load = MagicMock(return_value=data)
    save = MagicMock()
    return load, save


@pytest.fixture(autouse=True)
no_audit = patch("envault.notes.record_event")


@pytest.fixture(autouse=True)
def _no_audit(no_audit):
    no_audit.start()
    yield
    no_audit.stop()


class TestSetNote:
    def test_sets_note_on_plain_string(self):
        vault = {"API_KEY": "abc123"}
        load, save = _make_vault(vault)
        with patch("envault.notes.load_vault", load), patch("envault.notes.save_vault", save):
            notes_mod.set_note("myvault", "API_KEY", "rotate monthly", "pass")
        saved = save.call_args[0][1]
        assert saved["API_KEY"]["note"] == "rotate monthly"
        assert saved["API_KEY"]["value"] == "abc123"

    def test_sets_note_on_dict_value(self):
        vault = {"DB_URL": {"value": "postgres://", "tags": ["db"]}}
        load, save = _make_vault(vault)
        with patch("envault.notes.load_vault", load), patch("envault.notes.save_vault", save):
            notes_mod.set_note("myvault", "DB_URL", "primary db", "pass")
        saved = save.call_args[0][1]
        assert saved["DB_URL"]["note"] == "primary db"
        assert saved["DB_URL"]["tags"] == ["db"]

    def test_raises_on_missing_key(self):
        load, save = _make_vault({})
        with patch("envault.notes.load_vault", load), patch("envault.notes.save_vault", save):
            with pytest.raises(KeyError, match="MISSING"):
                notes_mod.set_note("myvault", "MISSING", "hi", "pass")


class TestGetNote:
    def test_returns_note_when_present(self):
        vault = {"KEY": {"value": "val", "note": "important"}}
        load, _ = _make_vault(vault)
        with patch("envault.notes.load_vault", load):
            result = notes_mod.get_note("myvault", "KEY", "pass")
        assert result == "important"

    def test_returns_none_for_plain_string(self):
        vault = {"KEY": "plain"}
        load, _ = _make_vault(vault)
        with patch("envault.notes.load_vault", load):
            result = notes_mod.get_note("myvault", "KEY", "pass")
        assert result is None

    def test_raises_on_missing_key(self):
        load, _ = _make_vault({})
        with patch("envault.notes.load_vault", load):
            with pytest.raises(KeyError):
                notes_mod.get_note("myvault", "NOPE", "pass")


class TestClearNote:
    def test_removes_existing_note(self):
        vault = {"KEY": {"value": "v", "note": "old note"}}
        load, save = _make_vault(vault)
        with patch("envault.notes.load_vault", load), patch("envault.notes.save_vault", save):
            notes_mod.clear_note("myvault", "KEY", "pass")
        saved = save.call_args[0][1]
        assert "note" not in saved["KEY"]

    def test_noop_when_no_note(self):
        vault = {"KEY": "plain"}
        load, save = _make_vault(vault)
        with patch("envault.notes.load_vault", load), patch("envault.notes.save_vault", save):
            notes_mod.clear_note("myvault", "KEY", "pass")
        save.assert_not_called()


class TestListNotedKeys:
    def test_returns_keys_with_notes(self):
        vault = {
            "A": {"value": "1", "note": "note A"},
            "B": "no note",
            "C": {"value": "3", "note": "note C"},
        }
        load, _ = _make_vault(vault)
        with patch("envault.notes.load_vault", load):
            result = notes_mod.list_noted_keys("myvault", "pass")
        keys = [r["key"] for r in result]
        assert "A" in keys
        assert "C" in keys
        assert "B" not in keys

    def test_returns_empty_list_when_none(self):
        load, _ = _make_vault({"X": "plain"})
        with patch("envault.notes.load_vault", load):
            result = notes_mod.list_noted_keys("myvault", "pass")
        assert result == []
