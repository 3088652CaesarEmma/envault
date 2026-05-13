"""Tests for envault/environments.py"""

import pytest
from unittest.mock import patch, MagicMock

from envault.environments import (
    set_environment,
    get_environment,
    clear_environment,
    list_by_environment,
)

PASSPHRASE = "test-passphrase"


def _make_vault(secrets=None):
    return {"secrets": secrets or {}}


@pytest.fixture(autouse=True)
def no_audit():
    with patch("envault.environments.record_event"):
        yield


@pytest.fixture()
def patched():
    vault = _make_vault({"DB_URL": "postgres://localhost", "API_KEY": {"value": "abc123"}})
    with patch("envault.environments.load_vault", return_value=vault) as lv, \
         patch("envault.environments.save_vault") as sv:
        yield lv, sv, vault


class TestSetEnvironment:
    def test_sets_env_on_plain_string(self, patched):
        _, sv, vault = patched
        set_environment("myvault", "DB_URL", "prod", PASSPHRASE)
        assert vault["secrets"]["DB_URL"]["environment"] == "prod"

    def test_sets_env_on_dict_value(self, patched):
        _, sv, vault = patched
        set_environment("myvault", "API_KEY", "staging", PASSPHRASE)
        assert vault["secrets"]["API_KEY"]["environment"] == "staging"

    def test_raises_on_invalid_env(self, patched):
        with pytest.raises(ValueError, match="Invalid environment"):
            set_environment("myvault", "DB_URL", "production", PASSPHRASE)

    def test_raises_on_missing_key(self, patched):
        with pytest.raises(KeyError):
            set_environment("myvault", "MISSING", "dev", PASSPHRASE)

    def test_calls_save_vault(self, patched):
        _, sv, _ = patched
        set_environment("myvault", "DB_URL", "dev", PASSPHRASE)
        sv.assert_called_once()


class TestGetEnvironment:
    def test_returns_env_when_set(self, patched):
        lv, _, vault = patched
        vault["secrets"]["API_KEY"]["environment"] = "prod"
        result = get_environment("myvault", "API_KEY", PASSPHRASE)
        assert result == "prod"

    def test_returns_none_for_plain_string(self, patched):
        result = get_environment("myvault", "DB_URL", PASSPHRASE)
        assert result is None

    def test_raises_on_missing_key(self, patched):
        with pytest.raises(KeyError):
            get_environment("myvault", "GHOST", PASSPHRASE)


class TestClearEnvironment:
    def test_removes_environment_field(self, patched):
        _, sv, vault = patched
        vault["secrets"]["API_KEY"]["environment"] = "dev"
        clear_environment("myvault", "API_KEY", PASSPHRASE)
        assert "environment" not in vault["secrets"]["API_KEY"]

    def test_noop_when_no_env_set(self, patched):
        _, sv, _ = patched
        clear_environment("myvault", "DB_URL", PASSPHRASE)
        sv.assert_not_called()


class TestListByEnvironment:
    def test_returns_matching_keys(self, patched):
        _, _, vault = patched
        vault["secrets"]["DB_URL"] = {"value": "postgres://", "environment": "prod"}
        vault["secrets"]["API_KEY"]["environment"] = "prod"
        vault["secrets"]["SECRET"] = {"value": "x", "environment": "dev"}
        result = list_by_environment("myvault", "prod", PASSPHRASE)
        assert "DB_URL" in result
        assert "API_KEY" in result
        assert "SECRET" not in result

    def test_returns_empty_when_none_match(self, patched):
        result = list_by_environment("myvault", "test", PASSPHRASE)
        assert result == []

    def test_raises_on_invalid_env(self, patched):
        with pytest.raises(ValueError):
            list_by_environment("myvault", "local", PASSPHRASE)
