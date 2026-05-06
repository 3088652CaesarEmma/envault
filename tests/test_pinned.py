"""Tests for envault.pinned — pin/unpin vault keys."""

from __future__ import annotations

import pytest
from unittest.mock import patch, MagicMock

from envault.pinned import (
    pin_key,
    unpin_key,
    is_pinned,
    list_pinned_keys,
    assert_not_pinned,
)


def _make_vault(data: dict):
    """Return (load_vault mock, save_vault mock) with preset vault data."""
    load_mock = MagicMock(return_value=data)
    save_mock = MagicMock()
    return load_mock, save_mock


@pytest.fixture()
def no_audit():
    with patch("envault.pinned.record_event"):
        yield


# ---------------------------------------------------------------------------
# is_pinned
# ---------------------------------------------------------------------------

class TestIsPinned:
    def test_returns_false_for_plain_string(self):
        assert is_pinned("secret") is False

    def test_returns_false_when_flag_absent(self):
        assert is_pinned({"value": "secret"}) is False

    def test_returns_true_when_flag_set(self):
        assert is_pinned({"value": "secret", "pinned": True}) is True

    def test_returns_false_when_flag_is_false(self):
        assert is_pinned({"value": "secret", "pinned": False}) is False


# ---------------------------------------------------------------------------
# pin_key
# ---------------------------------------------------------------------------

class TestPinKey:
    def test_pins_plain_string_value(self, no_audit):
        vault_data = {"API_KEY": "abc123"}
        load_mock, save_mock = _make_vault(vault_data)
        with patch("envault.pinned.load_vault", load_mock), \
             patch("envault.pinned.save_vault", save_mock):
            pin_key("myvault", "API_KEY", "pass")

        saved = save_mock.call_args[0][1]
        assert saved["API_KEY"] == {"value": "abc123", "pinned": True}

    def test_pins_existing_dict_entry(self, no_audit):
        vault_data = {"DB_URL": {"value": "postgres://", "tags": ["db"]}}
        load_mock, save_mock = _make_vault(vault_data)
        with patch("envault.pinned.load_vault", load_mock), \
             patch("envault.pinned.save_vault", save_mock):
            pin_key("myvault", "DB_URL", "pass")

        saved = save_mock.call_args[0][1]
        assert saved["DB_URL"]["pinned"] is True
        assert saved["DB_URL"]["tags"] == ["db"]

    def test_raises_on_missing_key(self, no_audit):
        load_mock, save_mock = _make_vault({})
        with patch("envault.pinned.load_vault", load_mock), \
             patch("envault.pinned.save_vault", save_mock):
            with pytest.raises(KeyError, match="MISSING"):
                pin_key("myvault", "MISSING", "pass")


# ---------------------------------------------------------------------------
# unpin_key
# ---------------------------------------------------------------------------

class TestUnpinKey:
    def test_removes_pinned_flag(self, no_audit):
        vault_data = {"TOKEN": {"value": "xyz", "pinned": True}}
        load_mock, save_mock = _make_vault(vault_data)
        with patch("envault.pinned.load_vault", load_mock), \
             patch("envault.pinned.save_vault", save_mock):
            unpin_key("myvault", "TOKEN", "pass")

        saved = save_mock.call_args[0][1]
        assert "pinned" not in saved["TOKEN"]

    def test_silently_succeeds_on_plain_string(self, no_audit):
        vault_data = {"TOKEN": "plain"}
        load_mock, save_mock = _make_vault(vault_data)
        with patch("envault.pinned.load_vault", load_mock), \
             patch("envault.pinned.save_vault", save_mock):
            unpin_key("myvault", "TOKEN", "pass")  # should not raise

    def test_raises_on_missing_key(self, no_audit):
        load_mock, save_mock = _make_vault({})
        with patch("envault.pinned.load_vault", load_mock), \
             patch("envault.pinned.save_vault", save_mock):
            with pytest.raises(KeyError):
                unpin_key("myvault", "GHOST", "pass")


# ---------------------------------------------------------------------------
# list_pinned_keys
# ---------------------------------------------------------------------------

class TestListPinnedKeys:
    def test_returns_only_pinned_keys(self, no_audit):
        vault_data = {
            "A": {"value": "1", "pinned": True},
            "B": "plain",
            "C": {"value": "3", "pinned": False},
            "D": {"value": "4", "pinned": True},
        }
        load_mock, _ = _make_vault(vault_data)
        with patch("envault.pinned.load_vault", load_mock):
            result = list_pinned_keys("myvault", "pass")
        assert sorted(result) == ["A", "D"]

    def test_returns_empty_when_none_pinned(self, no_audit):
        vault_data = {"X": "value", "Y": {"value": "v"}}
        load_mock, _ = _make_vault(vault_data)
        with patch("envault.pinned.load_vault", load_mock):
            result = list_pinned_keys("myvault", "pass")
        assert result == []


# ---------------------------------------------------------------------------
# assert_not_pinned
# ---------------------------------------------------------------------------

class TestAssertNotPinned:
    def test_raises_when_key_is_pinned(self):
        vault = {"SECRET": {"value": "s", "pinned": True}}
        with pytest.raises(ValueError, match="pinned"):
            assert_not_pinned(vault, "SECRET", "delete")

    def test_passes_when_key_is_not_pinned(self):
        vault = {"SECRET": {"value": "s"}}
        assert_not_pinned(vault, "SECRET", "delete")  # no exception

    def test_passes_when_key_absent(self):
        vault = {}
        assert_not_pinned(vault, "MISSING", "delete")  # no exception
