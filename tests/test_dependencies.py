"""Tests for envault.dependencies."""

from __future__ import annotations

import pytest
from unittest.mock import patch

from envault.dependencies import (
    add_dependency,
    get_dependencies,
    get_dependents,
    remove_dependency,
)

_VAULT_NAME = "testvault"
_PASSPHRASE = "s3cr3t"


def _make_vault(secrets: dict, deps: dict | None = None) -> dict:
    vault: dict = {"secrets": secrets}
    if deps:
        vault["__dependencies__"] = deps
    return vault


@pytest.fixture()
def patched(tmp_path):
    """Patch load_vault and save_vault so no disk I/O occurs."""
    store: dict = {}

    def _load(name, pw):
        return store.get(name, _make_vault({}))

    def _save(name, vault, pw):
        store[name] = vault

    with (
        patch("envault.dependencies.load_vault", side_effect=_load),
        patch("envault.dependencies.save_vault", side_effect=_save),
    ):
        yield store


class TestAddDependency:
    def test_adds_dependency_successfully(self, patched):
        patched[_VAULT_NAME] = _make_vault({"API_KEY": "v1", "DB_URL": "v2"})
        add_dependency(_VAULT_NAME, "API_KEY", "DB_URL", _PASSPHRASE)
        deps = patched[_VAULT_NAME].get("__dependencies__", {})
        assert "DB_URL" in deps.get("API_KEY", [])

    def test_does_not_duplicate_dependency(self, patched):
        patched[_VAULT_NAME] = _make_vault({"A": "1", "B": "2"})
        add_dependency(_VAULT_NAME, "A", "B", _PASSPHRASE)
        add_dependency(_VAULT_NAME, "A", "B", _PASSPHRASE)
        deps = patched[_VAULT_NAME]["__dependencies__"]["A"]
        assert deps.count("B") == 1

    def test_raises_when_key_missing(self, patched):
        patched[_VAULT_NAME] = _make_vault({"A": "1"})
        with pytest.raises(KeyError, match="MISSING"):
            add_dependency(_VAULT_NAME, "MISSING", "A", _PASSPHRASE)

    def test_raises_when_depends_on_missing(self, patched):
        patched[_VAULT_NAME] = _make_vault({"A": "1"})
        with pytest.raises(KeyError, match="MISSING"):
            add_dependency(_VAULT_NAME, "A", "MISSING", _PASSPHRASE)


class TestRemoveDependency:
    def test_removes_existing_dependency(self, patched):
        patched[_VAULT_NAME] = _make_vault(
            {"A": "1", "B": "2"}, deps={"A": ["B"]}
        )
        remove_dependency(_VAULT_NAME, "A", "B", _PASSPHRASE)
        deps = patched[_VAULT_NAME].get("__dependencies__", {})
        assert "A" not in deps

    def test_raises_when_dependency_absent(self, patched):
        patched[_VAULT_NAME] = _make_vault({"A": "1", "B": "2"})
        with pytest.raises(KeyError):
            remove_dependency(_VAULT_NAME, "A", "B", _PASSPHRASE)


class TestGetDependencies:
    def test_returns_direct_dependencies(self, patched):
        patched[_VAULT_NAME] = _make_vault(
            {"A": "1", "B": "2", "C": "3"}, deps={"A": ["B", "C"]}
        )
        result = get_dependencies(_VAULT_NAME, "A", _PASSPHRASE)
        assert result == ["B", "C"]

    def test_returns_empty_list_when_no_deps(self, patched):
        patched[_VAULT_NAME] = _make_vault({"A": "1"})
        assert get_dependencies(_VAULT_NAME, "A", _PASSPHRASE) == []


class TestGetDependents:
    def test_returns_keys_that_depend_on_target(self, patched):
        patched[_VAULT_NAME] = _make_vault(
            {"A": "1", "B": "2", "C": "3"},
            deps={"A": ["B"], "C": ["B"]},
        )
        result = get_dependents(_VAULT_NAME, "B", _PASSPHRASE)
        assert sorted(result) == ["A", "C"]

    def test_returns_empty_when_nothing_depends_on_key(self, patched):
        patched[_VAULT_NAME] = _make_vault({"A": "1", "B": "2"})
        assert get_dependents(_VAULT_NAME, "A", _PASSPHRASE) == []
