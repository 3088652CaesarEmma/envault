"""Tests for envault.reminders."""

from __future__ import annotations

from datetime import datetime, timezone, timedelta
from unittest.mock import patch, MagicMock

import pytest

from envault.reminders import get_expiring_keys, format_reminders, DEFAULT_WARN_DAYS


def _make_secret(expires_at: str | None) -> dict:
    if expires_at is None:
        return {"value": "plain"}
    return {"value": "secret", "expires_at": expires_at}


def _iso(delta_days: int) -> str:
    dt = datetime.now(tz=timezone.utc) + timedelta(days=delta_days)
    return dt.isoformat()


@pytest.fixture()
def no_audit():
    with patch("envault.reminders.record_event"):
        yield


@pytest.fixture()
def patched_load():
    with patch("envault.reminders.load_vault") as mock:
        yield mock


class TestGetExpiringKeys:
    def test_returns_empty_when_no_secrets(self, patched_load, no_audit):
        patched_load.return_value = {"secrets": {}}
        result = get_expiring_keys("myvault", "pass")
        assert result == []

    def test_returns_empty_for_plain_string_values(self, patched_load, no_audit):
        patched_load.return_value = {"secrets": {"KEY": "plain_string"}}
        result = get_expiring_keys("myvault", "pass")
        assert result == []

    def test_detects_key_expiring_within_warn_days(self, patched_load, no_audit):
        patched_load.return_value = {
            "secrets": {"TOKEN": _make_secret(_iso(3))}
        }
        result = get_expiring_keys("myvault", "pass", warn_days=7)
        assert len(result) == 1
        assert result[0]["key"] == "TOKEN"
        assert result[0]["vault"] == "myvault"
        assert result[0]["days_left"] == 3

    def test_ignores_key_expiring_after_warn_window(self, patched_load, no_audit):
        patched_load.return_value = {
            "secrets": {"TOKEN": _make_secret(_iso(30))}
        }
        result = get_expiring_keys("myvault", "pass", warn_days=7)
        assert result == []

    def test_ignores_already_expired_key(self, patched_load, no_audit):
        patched_load.return_value = {
            "secrets": {"OLD": _make_secret(_iso(-1))}
        }
        result = get_expiring_keys("myvault", "pass")
        assert result == []

    def test_results_sorted_by_days_left(self, patched_load, no_audit):
        patched_load.return_value = {
            "secrets": {
                "A": _make_secret(_iso(5)),
                "B": _make_secret(_iso(2)),
                "C": _make_secret(_iso(4)),
            }
        }
        result = get_expiring_keys("myvault", "pass", warn_days=7)
        assert [r["key"] for r in result] == ["B", "C", "A"]

    def test_records_audit_event_when_reminders_found(self, patched_load):
        patched_load.return_value = {
            "secrets": {"TOKEN": _make_secret(_iso(1))}
        }
        with patch("envault.reminders.record_event") as mock_audit:
            get_expiring_keys("myvault", "pass")
            mock_audit.assert_called_once()
            args = mock_audit.call_args[0]
            assert args[0] == "reminders_checked"

    def test_no_audit_when_no_reminders(self, patched_load):
        patched_load.return_value = {"secrets": {}}
        with patch("envault.reminders.record_event") as mock_audit:
            get_expiring_keys("myvault", "pass")
            mock_audit.assert_not_called()


class TestFormatReminders:
    def test_empty_list_returns_no_keys_message(self):
        assert format_reminders([]) == "No keys expiring soon."

    def test_single_reminder_contains_key_name(self):
        reminder = {
            "key": "API_KEY",
            "vault": "prod",
            "expires_at": "2099-01-01T00:00:00+00:00",
            "days_left": 5,
        }
        output = format_reminders([reminder])
        assert "API_KEY" in output
        assert "prod" in output
        assert "5 day(s)" in output

    def test_multiple_reminders_all_present(self):
        reminders = [
            {"key": "A", "vault": "v", "expires_at": "2099-01-01T00:00:00+00:00", "days_left": 1},
            {"key": "B", "vault": "v", "expires_at": "2099-01-02T00:00:00+00:00", "days_left": 2},
        ]
        output = format_reminders(reminders)
        assert "A" in output
        assert "B" in output
