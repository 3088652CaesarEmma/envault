"""Tests for envault.policy_check."""

import pytest
from unittest.mock import patch

from envault.policy_check import (
    PolicyViolationError,
    require_permission,
    assert_admin,
    can_read,
    can_write,
)

PATCH_TARGET = "envault.policy_check.check_access"


# ---------------------------------------------------------------------------
# require_permission
# ---------------------------------------------------------------------------

class TestRequirePermission:
    def test_returns_true_when_access_granted(self):
        with patch(PATCH_TARGET, return_value=True):
            result = require_permission("myvault", "alice", "read")
        assert result is True

    def test_returns_false_non_strict_when_denied(self):
        with patch(PATCH_TARGET, return_value=False):
            result = require_permission("myvault", "alice", "read", strict=False)
        assert result is False

    def test_raises_on_denied_when_strict(self):
        with patch(PATCH_TARGET, return_value=False):
            with pytest.raises(PolicyViolationError, match="'read' permission"):
                require_permission("myvault", "alice", "read", strict=True)

    def test_error_message_contains_user(self):
        with patch(PATCH_TARGET, return_value=False):
            with pytest.raises(PolicyViolationError, match="alice"):
                require_permission("myvault", "alice", "write")

    def test_error_message_contains_vault_name(self):
        with patch(PATCH_TARGET, return_value=False):
            with pytest.raises(PolicyViolationError, match="myvault"):
                require_permission("myvault", "alice", "write")

    def test_passes_correct_args_to_check_access(self):
        with patch(PATCH_TARGET, return_value=True) as mock_check:
            require_permission("vault1", "bob", "admin")
        mock_check.assert_called_once_with("vault1", "bob", "admin")


# ---------------------------------------------------------------------------
# assert_admin
# ---------------------------------------------------------------------------

class TestAssertAdmin:
    def test_does_not_raise_when_admin(self):
        with patch(PATCH_TARGET, return_value=True):
            assert_admin("myvault", "alice")  # should not raise

    def test_raises_when_not_admin(self):
        with patch(PATCH_TARGET, return_value=False):
            with pytest.raises(PolicyViolationError):
                assert_admin("myvault", "alice")


# ---------------------------------------------------------------------------
# can_read / can_write
# ---------------------------------------------------------------------------

class TestCanReadWrite:
    def test_can_read_true(self):
        with patch(PATCH_TARGET, return_value=True):
            assert can_read("myvault", "alice") is True

    def test_can_read_false_no_exception(self):
        with patch(PATCH_TARGET, return_value=False):
            assert can_read("myvault", "alice") is False

    def test_can_write_true(self):
        with patch(PATCH_TARGET, return_value=True):
            assert can_write("myvault", "alice") is True

    def test_can_write_false_no_exception(self):
        with patch(PATCH_TARGET, return_value=False):
            assert can_write("myvault", "alice") is False
