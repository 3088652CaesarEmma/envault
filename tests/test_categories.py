"""Tests for envault.categories."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from envault.categories import (
    clear_category,
    get_category,
    list_by_category,
    list_categories,
    set_category,
)

PASSPHRASE = "test-passphrase"


def _make_vault(**kwargs):
    return dict(**kwargs)


@pytest.fixture()
def no_audit():
    with patch("envault.categories.record_event"):
        yield


@pytest.fixture()
def patched(no_audit):
    """Patch load_vault and save_vault for isolation."""
    store: dict = {}

    def fake_load(name, pw):
        return dict(store)

    def fake_save(name, data, pw):
        store.clear()
        store.update(data)

    with patch("envault.categories.load_vault", side_effect=fake_load), \
         patch("envault.categories.save_vault", side_effect=fake_save):
        yield store


# ---------------------------------------------------------------------------
# set_category
# ---------------------------------------------------------------------------

def test_set_category_on_plain_string(patched):
    patched["DB_HOST"] = "localhost"
    set_category("myvault", "DB_HOST", "database", PASSPHRASE)
    assert patched["DB_HOST"] == {"value": "localhost", "category": "database"}


def test_set_category_on_dict_value(patched):
    patched["API_KEY"] = {"value": "abc123", "tag": "prod"}
    set_category("myvault", "API_KEY", "api", PASSPHRASE)
    assert patched["API_KEY"]["category"] == "api"
    assert patched["API_KEY"]["value"] == "abc123"


def test_set_category_raises_on_missing_key(patched):
    with pytest.raises(KeyError, match="MISSING"):
        set_category("myvault", "MISSING", "infra", PASSPHRASE)


# ---------------------------------------------------------------------------
# get_category
# ---------------------------------------------------------------------------

def test_get_category_returns_value(patched):
    patched["PORT"] = {"value": "5432", "category": "database"}
    assert get_category("myvault", "PORT", PASSPHRASE) == "database"


def test_get_category_returns_none_for_plain_string(patched):
    patched["SECRET"] = "plain"
    assert get_category("myvault", "SECRET", PASSPHRASE) is None


def test_get_category_raises_on_missing_key(patched):
    with pytest.raises(KeyError):
        get_category("myvault", "NOPE", PASSPHRASE)


# ---------------------------------------------------------------------------
# clear_category
# ---------------------------------------------------------------------------

def test_clear_category_removes_field(patched):
    patched["HOST"] = {"value": "db.local", "category": "network"}
    clear_category("myvault", "HOST", PASSPHRASE)
    assert "category" not in patched["HOST"]


def test_clear_category_noop_when_absent(patched):
    patched["HOST"] = {"value": "db.local"}
    clear_category("myvault", "HOST", PASSPHRASE)  # should not raise
    assert "category" not in patched["HOST"]


# ---------------------------------------------------------------------------
# list_by_category / list_categories
# ---------------------------------------------------------------------------

def test_list_by_category_returns_matching_keys(patched):
    patched.update({
        "DB_HOST": {"value": "localhost", "category": "database"},
        "DB_PORT": {"value": "5432", "category": "database"},
        "API_KEY": {"value": "key", "category": "api"},
    })
    result = list_by_category("myvault", "database", PASSPHRASE)
    assert result == ["DB_HOST", "DB_PORT"]


def test_list_by_category_returns_empty_when_none_match(patched):
    patched["X"] = {"value": "1", "category": "other"}
    assert list_by_category("myvault", "missing", PASSPHRASE) == []


def test_list_categories_returns_distinct_sorted(patched):
    patched.update({
        "A": {"value": "1", "category": "zebra"},
        "B": {"value": "2", "category": "alpha"},
        "C": {"value": "3", "category": "zebra"},
    })
    assert list_categories("myvault", PASSPHRASE) == ["alpha", "zebra"]


def test_list_categories_excludes_uncategorised(patched):
    patched["PLAIN"] = "no-category"
    assert list_categories("myvault", PASSPHRASE) == []
