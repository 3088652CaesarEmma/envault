"""Tests for envault.visibility module."""

from __future__ import annotations

import pytest
from unittest.mock import patch, MagicMock

from envault.visibility import (
    mark_masked,
    unmark_masked,
    is_masked,
    list_masked_keys,
    apply_visibility,
    _MASKED_PLACEHOLDER,
)


def _make_vault(secrets: dict) -> dict:
    return {"secrets": secrets, "meta": {}}


@pytest.fixture()
def no_audit():
    with patch("envault.visibility.record_event"):
        yield


@pytest.fixture()
def patched(no_audit):
    _store: dict = {}

    def fake_load(name, pw):
        return _store.get(name, _make_vault({}))

    def fake_save(name, data, pw):
        _store[name] = data

    with patch("envault.visibility.load_vault", side_effect=fake_load), \
         patch("envault.visibility.save_vault", side_effect=fake_save):
        yield _store


# --- is_masked ---

class TestIsMasked:
    def test_returns_false_for_plain_string(self):
        assert is_masked("secret") is False

    def test_returns_false_when_flag_absent(self):
        assert is_masked({"value": "secret"}) is False

    def test_returns_false_when_flag_is_false(self):
        assert is_masked({"value": "secret", "masked": False}) is False

    def test_returns_true_when_flag_set(self):
        assert is_masked({"value": "secret", "masked": True}) is True


# --- mark_masked / unmark_masked ---

class TestMarkMasked:
    def test_marks_plain_string(self, patched):
        patched["v"] = _make_vault({"KEY": "hello"})
        result = mark_masked("v", "KEY", "pw")
        assert result["masked"] is True
        assert result["value"] == "hello"

    def test_marks_existing_dict_entry(self, patched):
        patched["v"] = _make_vault({"KEY": {"value": "hello"}})
        result = mark_masked("v", "KEY", "pw")
        assert result["masked"] is True

    def test_raises_on_missing_key(self, patched):
        patched["v"] = _make_vault({})
        with pytest.raises(KeyError, match="KEY"):
            mark_masked("v", "KEY", "pw")

    def test_unmark_removes_flag(self, patched):
        patched["v"] = _make_vault({"KEY": {"value": "hello", "masked": True}})
        unmark_masked("v", "KEY", "pw")
        entry = patched["v"]["secrets"]["KEY"]
        assert not is_masked(entry)

    def test_unmark_collapses_to_plain_string_when_only_value(self, patched):
        patched["v"] = _make_vault({"KEY": {"value": "hello", "masked": True}})
        unmark_masked("v", "KEY", "pw")
        assert patched["v"]["secrets"]["KEY"] == "hello"


# --- list_masked_keys ---

def test_list_masked_keys_returns_only_masked(patched):
    patched["v"] = _make_vault({
        "A": {"value": "x", "masked": True},
        "B": "plain",
        "C": {"value": "y", "masked": False},
    })
    result = list_masked_keys("v", "pw")
    assert result == ["A"]


# --- apply_visibility ---

class TestApplyVisibility:
    def test_replaces_masked_value_with_placeholder(self):
        secrets = {"TOKEN": {"value": "abc123", "masked": True}}
        out = apply_visibility(secrets)
        assert out["TOKEN"] == _MASKED_PLACEHOLDER

    def test_reveals_masked_value_when_flag_set(self):
        secrets = {"TOKEN": {"value": "abc123", "masked": True}}
        out = apply_visibility(secrets, reveal=True)
        assert out["TOKEN"] == "abc123"

    def test_plain_string_passes_through(self):
        secrets = {"KEY": "value"}
        out = apply_visibility(secrets)
        assert out["KEY"] == "value"

    def test_unmasked_dict_entry_passes_through(self):
        secrets = {"KEY": {"value": "hello"}}
        out = apply_visibility(secrets)
        assert out["KEY"] == "hello"
