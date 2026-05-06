"""Tests for envault.readonly."""

from __future__ import annotations

import pytest
from unittest.mock import patch, MagicMock

from envault.readonly import (
    mark_readonly,
    unmark_readonly,
    is_readonly,
    assert_not_readonly,
    list_readonly_keys,
    ReadOnlyViolationError,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_vault(data: dict):
    """Return patched load/save context with the given vault data."""
    return patch("envault.readonly.load_vault", return_value=data), \
           patch("envault.readonly.save_vault"), \
           patch("envault.readonly.record_event")


# ---------------------------------------------------------------------------
# is_readonly
# ---------------------------------------------------------------------------

class TestIsReadonly:
    def test_returns_false_for_plain_string(self):
        assert is_readonly("some_value") is False

    def test_returns_false_when_flag_absent(self):
        assert is_readonly({"value": "v"}) is False

    def test_returns_false_when_flag_is_false(self):
        assert is_readonly({"value": "v", "readonly": False}) is False

    def test_returns_true_when_flag_set(self):
        assert is_readonly({"value": "v", "readonly": True}) is True


# ---------------------------------------------------------------------------
# mark_readonly
# ---------------------------------------------------------------------------

class TestMarkReadonly:
    def test_marks_plain_string_key(self):
        vault_data = {"API_KEY": "secret"}
        load_p, save_p, audit_p = _make_vault(vault_data)
        with load_p, save_p as mock_save, audit_p:
            result = mark_readonly("myvault", "API_KEY", "pass")
        assert result["readonly"] is True
        assert result["value"] == "secret"
        mock_save.assert_called_once()

    def test_marks_dict_key(self):
        vault_data = {"DB_URL": {"value": "postgres://", "tag": "db"}}
        load_p, save_p, audit_p = _make_vault(vault_data)
        with load_p, save_p, audit_p:
            result = mark_readonly("myvault", "DB_URL", "pass")
        assert result["readonly"] is True
        assert result["tag"] == "db"

    def test_raises_on_missing_key(self):
        load_p, save_p, audit_p = _make_vault({})
        with load_p, save_p, audit_p:
            with pytest.raises(KeyError, match="MISSING"):
                mark_readonly("myvault", "MISSING", "pass")


# ---------------------------------------------------------------------------
# unmark_readonly
# ---------------------------------------------------------------------------

class TestUnmarkReadonly:
    def test_removes_readonly_flag(self):
        vault_data = {"KEY": {"value": "x", "readonly": True}}
        load_p, save_p, audit_p = _make_vault(vault_data)
        with load_p, save_p, audit_p:
            result = unmark_readonly("myvault", "KEY", "pass")
        assert "readonly" not in result

    def test_plain_string_returns_unchanged(self):
        vault_data = {"KEY": "plain"}
        load_p, save_p, audit_p = _make_vault(vault_data)
        with load_p, save_p, audit_p:
            result = unmark_readonly("myvault", "KEY", "pass")
        assert result == "plain"


# ---------------------------------------------------------------------------
# assert_not_readonly
# ---------------------------------------------------------------------------

class TestAssertNotReadonly:
    def test_passes_for_plain_string(self):
        assert_not_readonly("v", "K", "value")  # no exception

    def test_passes_when_not_readonly(self):
        assert_not_readonly("v", "K", {"value": "x", "readonly": False})

    def test_raises_when_readonly(self):
        with pytest.raises(ReadOnlyViolationError, match="read-only"):
            assert_not_readonly("v", "K", {"value": "x", "readonly": True})


# ---------------------------------------------------------------------------
# list_readonly_keys
# ---------------------------------------------------------------------------

class TestListReadonlyKeys:
    def test_returns_only_readonly_keys(self):
        vault_data = {
            "A": {"value": "1", "readonly": True},
            "B": "plain",
            "C": {"value": "3", "readonly": False},
            "D": {"value": "4", "readonly": True},
        }
        load_p, _, audit_p = _make_vault(vault_data)
        with load_p, patch("envault.readonly.save_vault"), audit_p:
            keys = list_readonly_keys("myvault", "pass")
        assert set(keys) == {"A", "D"}

    def test_returns_empty_when_none_readonly(self):
        vault_data = {"X": "val", "Y": {"value": "v"}}
        load_p, _, audit_p = _make_vault(vault_data)
        with load_p, patch("envault.readonly.save_vault"), audit_p:
            keys = list_readonly_keys("myvault", "pass")
        assert keys == []
