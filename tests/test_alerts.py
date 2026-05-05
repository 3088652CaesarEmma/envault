"""Tests for envault.alerts."""

from __future__ import annotations

from datetime import datetime, timezone, timedelta
from unittest.mock import patch

import pytest

from envault.alerts import check_expiring_soon, check_missing_keys


VAULT_NAME = "my-vault"
PASSPHRASE = "s3cret"


def _make_secret(expires_at: str | None) -> dict:
    d: dict = {"value": "abc"}
    if expires_at is not None:
        d["expires_at"] = expires_at
    return d


@pytest.fixture()
def no_audit():
    with patch("envault.alerts.record_event"):
        yield


# ---------------------------------------------------------------------------
# check_expiring_soon
# ---------------------------------------------------------------------------

class TestCheckExpiringSoon:
    def _run(self, secrets: dict, warn_days: int = 7):
        with patch("envault.alerts.load_vault", return_value=secrets), \
             patch("envault.alerts.record_event"):
            return check_expiring_soon(VAULT_NAME, PASSPHRASE, warn_days=warn_days)

    def test_returns_empty_when_no_expiry(self):
        results = self._run({"KEY": "plain_value"})
        assert results == []

    def test_detects_key_expiring_within_window(self):
        soon = (datetime.now(timezone.utc) + timedelta(days=3)).isoformat()
        results = self._run({"TOKEN": _make_secret(soon)})
        assert len(results) == 1
        assert results[0]["key"] == "TOKEN"
        assert results[0]["vault"] == VAULT_NAME
        assert results[0]["days_remaining"] == 3

    def test_ignores_key_expiring_outside_window(self):
        far = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
        results = self._run({"TOKEN": _make_secret(far)}, warn_days=7)
        assert results == []

    def test_ignores_already_expired_key(self):
        past = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
        results = self._run({"TOKEN": _make_secret(past)})
        assert results == []

    def test_multiple_keys_mixed(self):
        soon = (datetime.now(timezone.utc) + timedelta(days=2)).isoformat()
        far = (datetime.now(timezone.utc) + timedelta(days=20)).isoformat()
        secrets = {
            "A": _make_secret(soon),
            "B": _make_secret(far),
            "C": "plain",
        }
        results = self._run(secrets)
        assert len(results) == 1
        assert results[0]["key"] == "A"

    def test_records_audit_event_when_expiring(self):
        soon = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
        with patch("envault.alerts.load_vault", return_value={"K": _make_secret(soon)}), \
             patch("envault.alerts.record_event") as mock_rec:
            check_expiring_soon(VAULT_NAME, PASSPHRASE)
            mock_rec.assert_called_once()
            assert mock_rec.call_args[0][0] == "alerts.expiring_soon"


# ---------------------------------------------------------------------------
# check_missing_keys
# ---------------------------------------------------------------------------

class TestCheckMissingKeys:
    def _run(self, secrets: dict, required: list[str]):
        with patch("envault.alerts.load_vault", return_value=secrets), \
             patch("envault.alerts.record_event"):
            return check_missing_keys(VAULT_NAME, PASSPHRASE, required)

    def test_returns_empty_when_all_present(self):
        assert self._run({"A": "1", "B": "2"}, ["A", "B"]) == []

    def test_returns_missing_keys(self):
        missing = self._run({"A": "1"}, ["A", "B", "C"])
        assert set(missing) == {"B", "C"}

    def test_records_audit_event_on_missing(self):
        with patch("envault.alerts.load_vault", return_value={}), \
             patch("envault.alerts.record_event") as mock_rec:
            check_missing_keys(VAULT_NAME, PASSPHRASE, ["X"])
            mock_rec.assert_called_once()
            assert mock_rec.call_args[0][0] == "alerts.missing_keys"

    def test_no_audit_when_nothing_missing(self):
        with patch("envault.alerts.load_vault", return_value={"X": "v"}), \
             patch("envault.alerts.record_event") as mock_rec:
            check_missing_keys(VAULT_NAME, PASSPHRASE, ["X"])
            mock_rec.assert_not_called()
