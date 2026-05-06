"""Tests for envault/namespace.py"""

import pytest
from envault.namespace import (
    add_to_namespace,
    remove_from_namespace,
    get_namespace,
    list_by_namespace,
    list_namespaces,
)


def _make_vault():
    return {
        "DB_HOST": "localhost",
        "DB_PORT": {"value": "5432", "namespace": "database"},
        "API_KEY": {"value": "secret", "namespace": "api"},
        "LOG_LEVEL": "info",
    }


class TestAddToNamespace:
    def test_adds_namespace_to_plain_string(self):
        vault = _make_vault()
        result = add_to_namespace(vault, "DB_HOST", "database")
        assert result["DB_HOST"]["namespace"] == "database"

    def test_adds_namespace_to_dict_value(self):
        vault = _make_vault()
        result = add_to_namespace(vault, "DB_PORT", "infra")
        assert result["DB_PORT"]["namespace"] == "infra"

    def test_preserves_existing_value(self):
        vault = _make_vault()
        add_to_namespace(vault, "DB_HOST", "database")
        assert vault["DB_HOST"]["value"] == "localhost"

    def test_raises_on_missing_key(self):
        vault = _make_vault()
        with pytest.raises(KeyError, match="MISSING"):
            add_to_namespace(vault, "MISSING", "ns")


class TestRemoveFromNamespace:
    def test_removes_namespace_from_dict(self):
        vault = _make_vault()
        remove_from_namespace(vault, "DB_PORT")
        assert "namespace" not in vault["DB_PORT"]

    def test_collapses_to_plain_string_when_only_value_remains(self):
        vault = _make_vault()
        remove_from_namespace(vault, "DB_PORT")
        assert vault["DB_PORT"] == "5432"

    def test_no_op_on_plain_string(self):
        vault = _make_vault()
        remove_from_namespace(vault, "DB_HOST")
        assert vault["DB_HOST"] == "localhost"

    def test_raises_on_missing_key(self):
        vault = _make_vault()
        with pytest.raises(KeyError):
            remove_from_namespace(vault, "NOPE")


class TestGetNamespace:
    def test_returns_namespace_for_dict_entry(self):
        vault = _make_vault()
        assert get_namespace(vault, "DB_PORT") == "database"

    def test_returns_none_for_plain_string(self):
        vault = _make_vault()
        assert get_namespace(vault, "DB_HOST") is None

    def test_raises_on_missing_key(self):
        vault = _make_vault()
        with pytest.raises(KeyError):
            get_namespace(vault, "UNKNOWN")


class TestListByNamespace:
    def test_returns_matching_keys(self):
        vault = _make_vault()
        result = list_by_namespace(vault, "database")
        assert "DB_PORT" in result
        assert "API_KEY" not in result

    def test_returns_empty_when_no_match(self):
        vault = _make_vault()
        result = list_by_namespace(vault, "nonexistent")
        assert result == {}

    def test_plain_strings_excluded(self):
        vault = _make_vault()
        result = list_by_namespace(vault, "database")
        assert "DB_HOST" not in result


class TestListNamespaces:
    def test_returns_all_distinct_namespaces(self):
        vault = _make_vault()
        ns = list_namespaces(vault)
        assert "database" in ns
        assert "api" in ns

    def test_returns_sorted_list(self):
        vault = _make_vault()
        ns = list_namespaces(vault)
        assert ns == sorted(ns)

    def test_plain_strings_not_counted(self):
        vault = {"PLAIN": "value"}
        assert list_namespaces(vault) == []
