"""Tests for envault.lock session lock management."""

import pytest
from unittest.mock import patch, MagicMock

from envault import lock as lock_module
from envault.lock import (
    lock_session,
    unlock_session,
    is_locked,
    set_auto_lock,
    get_lock_status,
    reset_lock_state,
)


@pytest.fixture(autouse=True)
def reset_state():
    """Ensure lock state is clean before and after every test."""
    reset_lock_state()
    yield
    reset_lock_state()


@pytest.fixture(autouse=True)
def mock_audit():
    with patch("envault.lock.record_event") as m:
        yield m


class TestLockSession:
    def test_lock_sets_locked_state(self):
        with patch("envault.lock.clear_session_passphrase") as mock_clear:
            lock_session()
            mock_clear.assert_called_once()
            assert lock_module._locked_at is not None

    def test_is_locked_returns_true_after_lock(self):
        with patch("envault.lock.clear_session_passphrase"):
            lock_session()
        assert is_locked() is True

    def test_lock_records_audit_event(self, mock_audit):
        with patch("envault.lock.clear_session_passphrase"):
            lock_session()
        mock_audit.assert_called_with("session_locked", {})


class TestUnlockSession:
    def test_unlock_clears_locked_at(self):
        with patch("envault.lock.clear_session_passphrase"):
            lock_session()
        with patch("envault.lock.set_session_passphrase"):
            result = unlock_session("strongpass")
        assert result is True
        assert lock_module._locked_at is None

    def test_unlock_returns_false_for_empty_passphrase(self):
        result = unlock_session("")
        assert result is False

    def test_unlock_records_audit_event(self, mock_audit):
        with patch("envault.lock.set_session_passphrase"):
            unlock_session("strongpass")
        mock_audit.assert_called_with("session_unlocked", {})

    def test_is_locked_returns_false_after_unlock(self):
        with patch("envault.lock.clear_session_passphrase"):
            lock_session()
        with patch("envault.lock.set_session_passphrase"):
            unlock_session("strongpass")
        assert is_locked() is False


class TestSetAutoLock:
    def test_sets_auto_lock_seconds(self):
        set_auto_lock(300)
        assert lock_module._auto_lock_seconds == 300

    def test_raises_on_non_positive_value(self):
        with pytest.raises(ValueError, match="positive integer"):
            set_auto_lock(0)

    def test_raises_on_negative_value(self):
        with pytest.raises(ValueError):
            set_auto_lock(-60)


class TestGetLockStatus:
    def test_returns_unlocked_by_default(self):
        status = get_lock_status()
        assert status["locked"] is False
        assert status["locked_at"] is None
        assert status["auto_lock_seconds"] is None

    def test_returns_locked_status_after_lock(self):
        with patch("envault.lock.clear_session_passphrase"):
            lock_session()
        status = get_lock_status()
        assert status["locked"] is True
        assert status["locked_at"] is not None

    def test_reflects_auto_lock_seconds(self):
        set_auto_lock(120)
        status = get_lock_status()
        assert status["auto_lock_seconds"] == 120
