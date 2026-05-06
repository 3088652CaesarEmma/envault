"""Tests for envault.aliases."""

from __future__ import annotations

import pytest
from unittest.mock import patch

from envault.aliases import (
    _ALIAS_META_KEY,
    _get_aliases,
    set_alias,
    remove_alias,
    resolve_alias,
    list_aliases,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_vault(**keys) -> dict:
    return {k: v for k, v in keys.items()}


@pytest.fixture()
def no_audit():
    with patch("envault.aliases.record_event"):
        yield


@pytest.fixture()
def patched(no_audit):
    """Patch load_vault / save_vault so tests stay in-memory."""
    store: dict = {}

    def _load(name, pw):
        return dict(store.get(name, {}))

    def _save(name, vault, pw):
        store[name] = dict(vault)

    with (
        patch("envault.aliases.load_vault", side_effect=_load),
        patch("envault.aliases.save_vault", side_effect=_save),
    ):
        yield store


# ---------------------------------------------------------------------------
# _get_aliases
# ---------------------------------------------------------------------------

class TestGetAliases:
    def test_returns_empty_dict_when_key_absent(self):
        assert _get_aliases({}) == {}

    def test_returns_empty_dict_when_meta_not_a_dict(self):
        assert _get_aliases({_ALIAS_META_KEY: "bad"}) == {}

    def test_returns_stored_aliases(self):
        vault = {_ALIAS_META_KEY: {"DB": "DATABASE_URL"}}
        assert _get_aliases(vault) == {"DB": "DATABASE_URL"}


# ---------------------------------------------------------------------------
# set_alias
# ---------------------------------------------------------------------------

class TestSetAlias:
    def test_stores_alias(self, patched):
        patched["myv"] = {"DATABASE_URL": "postgres://localhost"}
        set_alias("myv", "DB", "DATABASE_URL", "pw")
        assert patched["myv"][_ALIAS_META_KEY]["DB"] == "DATABASE_URL"

    def test_raises_when_target_missing(self, patched):
        patched["myv"] = {}
        with pytest.raises(KeyError, match="TARGET"):
            set_alias("myv", "X", "TARGET", "pw")

    def test_overwrites_existing_alias(self, patched):
        patched["myv"] = {
            "KEY_A": "a",
            "KEY_B": "b",
            _ALIAS_META_KEY: {"ALIAS": "KEY_A"},
        }
        set_alias("myv", "ALIAS", "KEY_B", "pw")
        assert patched["myv"][_ALIAS_META_KEY]["ALIAS"] == "KEY_B"


# ---------------------------------------------------------------------------
# remove_alias
# ---------------------------------------------------------------------------

class TestRemoveAlias:
    def test_removes_existing_alias(self, patched):
        patched["myv"] = {
            "SECRET": "val",
            _ALIAS_META_KEY: {"S": "SECRET"},
        }
        remove_alias("myv", "S", "pw")
        assert "S" not in patched["myv"].get(_ALIAS_META_KEY, {})

    def test_raises_when_alias_not_found(self, patched):
        patched["myv"] = {"KEY": "v", _ALIAS_META_KEY: {}}
        with pytest.raises(KeyError, match="GHOST"):
            remove_alias("myv", "GHOST", "pw")


# ---------------------------------------------------------------------------
# resolve_alias / list_aliases
# ---------------------------------------------------------------------------

class TestResolveAndList:
    def test_resolve_returns_target(self):
        vault = {_ALIAS_META_KEY: {"DB": "DATABASE_URL"}}
        assert resolve_alias(vault, "DB") == "DATABASE_URL"

    def test_resolve_returns_none_for_unknown(self):
        assert resolve_alias({}, "NOPE") is None

    def test_list_aliases_sorted(self):
        vault = {_ALIAS_META_KEY: {"Z": "KEY_Z", "A": "KEY_A"}}
        result = list_aliases(vault)
        assert result == [
            {"alias": "A", "target": "KEY_A"},
            {"alias": "Z", "target": "KEY_Z"},
        ]

    def test_list_aliases_empty(self):
        assert list_aliases({}) == []
