"""Tests for envault/templates.py"""

from __future__ import annotations

import pytest
from unittest.mock import patch, MagicMock

from envault import templates as tmpl


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _patched(store: dict):
    """Return a context manager that patches load/save with an in-memory store."""
    load = MagicMock(side_effect=lambda: dict(store))
    def save(data):
        store.clear()
        store.update(data)
    return patch.multiple(
        "envault.templates",
        _load_templates=load,
        _save_templates=MagicMock(side_effect=save),
    )


# ---------------------------------------------------------------------------
# save_template
# ---------------------------------------------------------------------------

class TestSaveTemplate:
    def test_saves_new_template(self):
        store: dict = {}
        with _patched(store):
            tmpl.save_template("django", ["SECRET_KEY", "DATABASE_URL"])
        assert store == {"django": ["SECRET_KEY", "DATABASE_URL"]}

    def test_overwrites_existing_template(self):
        store = {"django": ["OLD_KEY"]}
        with _patched(store):
            tmpl.save_template("django", ["SECRET_KEY"])
        assert store["django"] == ["SECRET_KEY"]

    def test_raises_on_empty_name(self):
        with pytest.raises(ValueError, match="empty"):
            tmpl.save_template("", ["KEY"])

    def test_raises_on_empty_keys(self):
        with pytest.raises(ValueError, match="at least one key"):
            tmpl.save_template("mytemplate", [])


# ---------------------------------------------------------------------------
# delete_template
# ---------------------------------------------------------------------------

class TestDeleteTemplate:
    def test_deletes_existing_template(self):
        store = {"django": ["SECRET_KEY"]}
        with _patched(store):
            tmpl.delete_template("django")
        assert "django" not in store

    def test_raises_on_missing_template(self):
        store: dict = {}
        with _patched(store):
            with pytest.raises(KeyError, match="does not exist"):
                tmpl.delete_template("ghost")


# ---------------------------------------------------------------------------
# list_templates
# ---------------------------------------------------------------------------

def test_list_templates_returns_all():
    store = {"a": ["K1"], "b": ["K2", "K3"]}
    with _patched(store):
        result = tmpl.list_templates()
    assert result == store


def test_list_templates_empty():
    store: dict = {}
    with _patched(store):
        result = tmpl.list_templates()
    assert result == {}


# ---------------------------------------------------------------------------
# apply_template
# ---------------------------------------------------------------------------

class TestApplyTemplate:
    def test_returns_matching_secrets(self):
        store = {"django": ["SECRET_KEY", "DATABASE_URL"]}
        vault_secrets = {"SECRET_KEY": "abc", "DATABASE_URL": "postgres://", "EXTRA": "x"}
        with _patched(store):
            result = tmpl.apply_template("django", vault_secrets)
        assert result == {"SECRET_KEY": "abc", "DATABASE_URL": "postgres://"}

    def test_raises_on_missing_template(self):
        store: dict = {}
        with _patched(store):
            with pytest.raises(KeyError):
                tmpl.apply_template("ghost", {})

    def test_raises_on_missing_vault_keys(self):
        store = {"t": ["REQUIRED_KEY"]}
        with _patched(store):
            with pytest.raises(ValueError, match="missing template keys"):
                tmpl.apply_template("t", {})
