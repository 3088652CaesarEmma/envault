"""Tests for envault.versioning."""

from unittest.mock import patch, MagicMock
import pytest

from envault.versioning import (
    push_version,
    list_versions,
    restore_version,
    clear_versions,
    _MAX_VERSIONS,
)

_PASSPHRASE = "test-pass"
_VAULT = "myvault"


def _patched(vault_data: dict):
    """Context manager that patches load/save/audit with *vault_data*."""
    store = {"data": vault_data}

    def fake_load(name, pw):
        return dict(store["data"])

    def fake_save(name, data, pw):
        store["data"] = dict(data)

    return (
        patch("envault.versioning.load_vault", side_effect=fake_load),
        patch("envault.versioning.save_vault", side_effect=fake_save),
        patch("envault.versioning.record_event"),
        store,
    )


class TestPushVersion:
    def test_creates_version_entry(self):
        p1, p2, p3, store = _patched({"KEY": "hello"})
        with p1, p2, p3:
            entry = push_version(_VAULT, "KEY", _PASSPHRASE)
        assert entry["value"] == "hello"
        assert "timestamp" in entry

    def test_converts_plain_string_to_dict(self):
        p1, p2, p3, store = _patched({"KEY": "hello"})
        with p1, p2, p3:
            push_version(_VAULT, "KEY", _PASSPHRASE)
        assert isinstance(store["data"]["KEY"], dict)

    def test_appends_to_existing_versions(self):
        initial = {"KEY": {"value": "v2", "versions": [{"value": "v1", "timestamp": "t"}]}}
        p1, p2, p3, store = _patched(initial)
        with p1, p2, p3:
            push_version(_VAULT, "KEY", _PASSPHRASE)
        assert len(store["data"]["KEY"]["versions"]) == 2

    def test_trims_to_max_versions(self):
        versions = [{"value": f"v{i}", "timestamp": "t"} for i in range(_MAX_VERSIONS)]
        initial = {"KEY": {"value": "latest", "versions": versions}}
        p1, p2, p3, store = _patched(initial)
        with p1, p2, p3:
            push_version(_VAULT, "KEY", _PASSPHRASE)
        assert len(store["data"]["KEY"]["versions"]) == _MAX_VERSIONS

    def test_raises_on_missing_key(self):
        p1, p2, p3, store = _patched({})
        with p1, p2, p3, pytest.raises(KeyError):
            push_version(_VAULT, "MISSING", _PASSPHRASE)


class TestListVersions:
    def test_returns_empty_for_plain_string(self):
        p1, p2, p3, store = _patched({"KEY": "plain"})
        with p1, p2, p3:
            result = list_versions(_VAULT, "KEY", _PASSPHRASE)
        assert result == []

    def test_returns_versions_list(self):
        versions = [{"value": "a", "timestamp": "t1"}, {"value": "b", "timestamp": "t2"}]
        p1, p2, p3, store = _patched({"KEY": {"value": "c", "versions": versions}})
        with p1, p2, p3:
            result = list_versions(_VAULT, "KEY", _PASSPHRASE)
        assert len(result) == 2
        assert result[0]["value"] == "a"

    def test_raises_on_missing_key(self):
        p1, p2, p3, store = _patched({})
        with p1, p2, p3, pytest.raises(KeyError):
            list_versions(_VAULT, "MISSING", _PASSPHRASE)


class TestRestoreVersion:
    def test_restores_correct_value(self):
        versions = [{"value": "old", "timestamp": "t1"}]
        initial = {"KEY": {"value": "new", "versions": versions}}
        p1, p2, p3, store = _patched(initial)
        with p1, p2, p3:
            val = restore_version(_VAULT, "KEY", 0, _PASSPHRASE)
        assert val == "old"
        assert store["data"]["KEY"]["value"] == "old"

    def test_raises_on_out_of_range_index(self):
        initial = {"KEY": {"value": "v", "versions": [{"value": "x", "timestamp": "t"}]}}
        p1, p2, p3, store = _patched(initial)
        with p1, p2, p3, pytest.raises(IndexError):
            restore_version(_VAULT, "KEY", 5, _PASSPHRASE)

    def test_raises_when_no_history(self):
        p1, p2, p3, store = _patched({"KEY": "plain"})
        with p1, p2, p3, pytest.raises(ValueError):
            restore_version(_VAULT, "KEY", 0, _PASSPHRASE)


class TestClearVersions:
    def test_returns_count_cleared(self):
        versions = [{"value": "a", "timestamp": "t"}, {"value": "b", "timestamp": "t"}]
        p1, p2, p3, store = _patched({"KEY": {"value": "c", "versions": versions}})
        with p1, p2, p3:
            count = clear_versions(_VAULT, "KEY", _PASSPHRASE)
        assert count == 2

    def test_versions_list_is_empty_after_clear(self):
        versions = [{"value": "a", "timestamp": "t"}]
        p1, p2, p3, store = _patched({"KEY": {"value": "c", "versions": versions}})
        with p1, p2, p3:
            clear_versions(_VAULT, "KEY", _PASSPHRASE)
        assert store["data"]["KEY"]["versions"] == []

    def test_returns_zero_for_plain_string(self):
        p1, p2, p3, store = _patched({"KEY": "plain"})
        with p1, p2, p3:
            count = clear_versions(_VAULT, "KEY", _PASSPHRASE)
        assert count == 0
