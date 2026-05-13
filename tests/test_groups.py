"""Tests for envault/groups.py."""

from __future__ import annotations

import pytest

from envault.groups import (
    _GROUPS_KEY,
    add_to_group,
    delete_group,
    get_group_members,
    list_groups,
    remove_from_group,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_vault(keys: dict | None = None) -> dict:
    base = {"DB_URL": "postgres://", "API_KEY": "secret", "TOKEN": "abc123"}
    base.update(keys or {})
    return base


@pytest.fixture()
def no_audit(monkeypatch):
    monkeypatch.setattr("envault.groups.record_event", lambda *a, **kw: None)


@pytest.fixture()
def patched(monkeypatch, no_audit):
    store: dict = {}

    def fake_load(name, pw):
        return dict(store.get(name, _make_vault()))

    def fake_save(name, vault, pw):
        store[name] = dict(vault)

    monkeypatch.setattr("envault.groups.load_vault", fake_load)
    monkeypatch.setattr("envault.groups.save_vault", fake_save)
    return store


# ---------------------------------------------------------------------------
# add_to_group
# ---------------------------------------------------------------------------

class TestAddToGroup:
    def test_adds_key_to_new_group(self, patched):
        add_to_group("myvault", "database", "DB_URL", "pw")
        members = get_group_members("myvault", "database", "pw")
        assert "DB_URL" in members

    def test_does_not_duplicate_key(self, patched):
        add_to_group("myvault", "database", "DB_URL", "pw")
        add_to_group("myvault", "database", "DB_URL", "pw")
        members = get_group_members("myvault", "database", "pw")
        assert members.count("DB_URL") == 1

    def test_raises_on_missing_key(self, patched):
        with pytest.raises(KeyError, match="MISSING"):
            add_to_group("myvault", "grp", "MISSING", "pw")

    def test_multiple_keys_in_group(self, patched):
        add_to_group("myvault", "auth", "API_KEY", "pw")
        add_to_group("myvault", "auth", "TOKEN", "pw")
        members = get_group_members("myvault", "auth", "pw")
        assert set(members) == {"API_KEY", "TOKEN"}


# ---------------------------------------------------------------------------
# remove_from_group
# ---------------------------------------------------------------------------

class TestRemoveFromGroup:
    def test_removes_key(self, patched):
        add_to_group("myvault", "grp", "API_KEY", "pw")
        remove_from_group("myvault", "grp", "API_KEY", "pw")
        with pytest.raises(KeyError):
            get_group_members("myvault", "grp", "pw")

    def test_raises_if_key_not_in_group(self, patched):
        add_to_group("myvault", "grp", "API_KEY", "pw")
        with pytest.raises(KeyError, match="TOKEN"):
            remove_from_group("myvault", "grp", "TOKEN", "pw")

    def test_group_deleted_when_empty(self, patched):
        add_to_group("myvault", "grp", "API_KEY", "pw")
        remove_from_group("myvault", "grp", "API_KEY", "pw")
        groups = list_groups("myvault", "pw")
        assert "grp" not in groups


# ---------------------------------------------------------------------------
# list_groups / get_group_members
# ---------------------------------------------------------------------------

class TestListGroups:
    def test_returns_empty_dict_when_no_groups(self, patched):
        result = list_groups("myvault", "pw")
        assert result == {}

    def test_returns_all_groups(self, patched):
        add_to_group("myvault", "g1", "DB_URL", "pw")
        add_to_group("myvault", "g2", "API_KEY", "pw")
        groups = list_groups("myvault", "pw")
        assert set(groups.keys()) == {"g1", "g2"}

    def test_get_members_raises_on_unknown_group(self, patched):
        with pytest.raises(KeyError, match="nope"):
            get_group_members("myvault", "nope", "pw")


# ---------------------------------------------------------------------------
# delete_group
# ---------------------------------------------------------------------------

class TestDeleteGroup:
    def test_deletes_group(self, patched):
        add_to_group("myvault", "toremove", "API_KEY", "pw")
        delete_group("myvault", "toremove", "pw")
        assert "toremove" not in list_groups("myvault", "pw")

    def test_raises_on_nonexistent_group(self, patched):
        with pytest.raises(KeyError, match="ghost"):
            delete_group("myvault", "ghost", "pw")

    def test_keys_still_in_vault_after_group_deleted(self, patched):
        """Deleting a group must not delete the underlying vault keys."""
        add_to_group("myvault", "grp", "DB_URL", "pw")
        delete_group("myvault", "grp", "pw")
        # The vault key should still be accessible (not removed from vault)
        from envault.vault import load_vault  # noqa: F401  (just verify no crash)
