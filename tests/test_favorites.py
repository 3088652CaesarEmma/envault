"""Tests for envault.favorites."""

from __future__ import annotations

import pytest
from unittest.mock import patch, MagicMock

from envault.favorites import mark_favorite, unmark_favorite, is_favorite, list_favorites


def _make_vault(data: dict) -> dict:
    return dict(data)


@pytest.fixture()
def no_audit():
    with patch("envault.favorites.record_event"):
        yield


@pytest.fixture()
def patched(no_audit):
    """Patch load_vault and save_vault for isolation."""
    with patch("envault.favorites.load_vault") as mock_load, \
         patch("envault.favorites.save_vault") as mock_save:
        yield mock_load, mock_save


# ---------------------------------------------------------------------------
# is_favorite
# ---------------------------------------------------------------------------

class TestIsFavorite:
    def test_returns_false_for_plain_string(self):
        assert is_favorite("secret") is False

    def test_returns_false_when_flag_absent(self):
        assert is_favorite({"value": "secret"}) is False

    def test_returns_false_when_flag_is_false(self):
        assert is_favorite({"value": "secret", "favorite": False}) is False

    def test_returns_true_when_flag_is_true(self):
        assert is_favorite({"value": "secret", "favorite": True}) is True


# ---------------------------------------------------------------------------
# mark_favorite
# ---------------------------------------------------------------------------

class TestMarkFavorite:
    def test_marks_plain_string_entry(self, patched):
        mock_load, mock_save = patched
        mock_load.return_value = {"API_KEY": "abc123"}
        mark_favorite("myvault", "API_KEY", "pass")
        saved = mock_save.call_args[0][1]
        assert saved["API_KEY"]["favorite"] is True
        assert saved["API_KEY"]["value"] == "abc123"

    def test_marks_dict_entry(self, patched):
        mock_load, mock_save = patched
        mock_load.return_value = {"API_KEY": {"value": "abc123"}}
        mark_favorite("myvault", "API_KEY", "pass")
        saved = mock_save.call_args[0][1]
        assert saved["API_KEY"]["favorite"] is True

    def test_raises_on_missing_key(self, patched):
        mock_load, _ = patched
        mock_load.return_value = {}
        with pytest.raises(KeyError, match="MISSING"):
            mark_favorite("myvault", "MISSING", "pass")


# ---------------------------------------------------------------------------
# unmark_favorite
# ---------------------------------------------------------------------------

class TestUnmarkFavorite:
    def test_removes_favorite_flag(self, patched):
        mock_load, mock_save = patched
        mock_load.return_value = {"API_KEY": {"value": "abc123", "favorite": True}}
        unmark_favorite("myvault", "API_KEY", "pass")
        saved = mock_save.call_args[0][1]
        assert "favorite" not in saved["API_KEY"]

    def test_no_error_on_plain_string(self, patched):
        mock_load, mock_save = patched
        mock_load.return_value = {"API_KEY": "abc123"}
        unmark_favorite("myvault", "API_KEY", "pass")  # should not raise

    def test_raises_on_missing_key(self, patched):
        mock_load, _ = patched
        mock_load.return_value = {}
        with pytest.raises(KeyError):
            unmark_favorite("myvault", "MISSING", "pass")


# ---------------------------------------------------------------------------
# list_favorites
# ---------------------------------------------------------------------------

class TestListFavorites:
    def test_returns_only_favorite_keys(self, patched):
        mock_load, _ = patched
        mock_load.return_value = {
            "A": {"value": "1", "favorite": True},
            "B": "plain",
            "C": {"value": "3", "favorite": False},
            "D": {"value": "4", "favorite": True},
        }
        result = list_favorites("myvault", "pass")
        assert result == ["A", "D"]

    def test_returns_empty_when_none_marked(self, patched):
        mock_load, _ = patched
        mock_load.return_value = {"A": "val", "B": {"value": "v"}}
        assert list_favorites("myvault", "pass") == []
