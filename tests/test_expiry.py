"""Tests for envault.expiry module."""

import time
import pytest
from unittest.mock import patch, MagicMock

from envault.expiry import set_expiry, clear_expiry, is_expired, list_expired_keys, purge_expired_keys


PASSPHRASE = "test-passphrase"


def _make_vault(data: dict):
    load = MagicMock(return_value=data)
    save = MagicMock()
    audit = MagicMock()
    return load, save, audit


@pytest.fixture(autouse=True)
def no_audit(monkeypatch):
    monkeypatch.setattr("envault.expiry.record_event", MagicMock())


class TestIsExpired:
    def test_returns_false_for_plain_string(self):
        assert is_expired("some_value") is False

    def test_returns_false_when_no_expires_at(self):
        assert is_expired({"value": "x"}) is False

    def test_returns_false_when_not_yet_expired(self):
        future = int(time.time()) + 9999
        assert is_expired({"value": "x", "expires_at": future}) is False

    def test_returns_true_when_expired(self):
        past = int(time.time()) - 1
        assert is_expired({"value": "x", "expires_at": past}) is True


class TestSetExpiry:
    def test_sets_expires_at_on_plain_value(self):
        vault_data = {"MY_KEY": "secret"}
        with patch("envault.expiry.load_vault", return_value=vault_data), \
             patch("envault.expiry.save_vault") as mock_save:
            result = set_expiry("myvault", "MY_KEY", 3600, PASSPHRASE)
            assert "expires_at" in result
            assert result["ttl_seconds"] == 3600
            mock_save.assert_called_once()

    def test_raises_on_missing_key(self):
        with patch("envault.expiry.load_vault", return_value={}):
            with pytest.raises(KeyError, match="MY_KEY"):
                set_expiry("myvault", "MY_KEY", 60, PASSPHRASE)

    def test_preserves_existing_dict_fields(self):
        vault_data = {"MY_KEY": {"value": "secret", "tags": ["prod"]}}
        with patch("envault.expiry.load_vault", return_value=vault_data), \
             patch("envault.expiry.save_vault"):
            set_expiry("myvault", "MY_KEY", 100, PASSPHRASE)
            assert vault_data["MY_KEY"]["tags"] == ["prod"]


class TestClearExpiry:
    def test_removes_expires_at(self):
        vault_data = {"K": {"value": "v", "expires_at": 12345}}
        with patch("envault.expiry.load_vault", return_value=vault_data), \
             patch("envault.expiry.save_vault") as mock_save:
            clear_expiry("myvault", "K", PASSPHRASE)
            assert "expires_at" not in vault_data["K"]
            mock_save.assert_called_once()

    def test_raises_on_missing_key(self):
        with patch("envault.expiry.load_vault", return_value={}):
            with pytest.raises(KeyError):
                clear_expiry("myvault", "MISSING", PASSPHRASE)


class TestListAndPurge:
    def _vault(self):
        past = int(time.time()) - 10
        future = int(time.time()) + 9999
        return {
            "OLD": {"value": "x", "expires_at": past},
            "NEW": {"value": "y", "expires_at": future},
            "PLAIN": "z",
        }

    def test_list_expired_returns_only_expired(self):
        with patch("envault.expiry.load_vault", return_value=self._vault()):
            result = list_expired_keys("v", PASSPHRASE)
            assert result == ["OLD"]

    def test_purge_removes_expired_and_returns_keys(self):
        vault_data = self._vault()
        with patch("envault.expiry.load_vault", return_value=vault_data), \
             patch("envault.expiry.save_vault"):
            purged = purge_expired_keys("v", PASSPHRASE)
            assert "OLD" in purged
            assert "OLD" not in vault_data
            assert "NEW" in vault_data
