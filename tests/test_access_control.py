"""Tests for envault.access_control."""

from __future__ import annotations

import pytest

from envault.access_control import (
    check_access,
    grant_access,
    list_access,
    revoke_access,
)


@pytest.fixture()
def vault_dir(tmp_path):
    return tmp_path / "vaults"


class TestGrantAccess:
    def test_creates_policy_file(self, vault_dir):
        grant_access(vault_dir, "myapp", "alice", "read")
        assert (vault_dir / ".envault_access.json").exists()

    def test_single_permission_stored(self, vault_dir):
        grant_access(vault_dir, "myapp", "alice", "read")
        assert check_access(vault_dir, "myapp", "alice", "read") is True

    def test_two_permissions_stored(self, vault_dir):
        grant_access(vault_dir, "myapp", "alice", "read")
        grant_access(vault_dir, "myapp", "alice", "write")
        assert check_access(vault_dir, "myapp", "alice", "read") is True
        assert check_access(vault_dir, "myapp", "alice", "write") is True

    def test_idempotent_grant(self, vault_dir):
        grant_access(vault_dir, "myapp", "bob", "read")
        grant_access(vault_dir, "myapp", "bob", "read")
        policy = list_access(vault_dir, "myapp")
        assert policy["myapp:bob"] == ["read"]

    def test_invalid_permission_raises(self, vault_dir):
        with pytest.raises(ValueError, match="Invalid permission"):
            grant_access(vault_dir, "myapp", "alice", "admin")


class TestRevokeAccess:
    def test_revoke_removes_permission(self, vault_dir):
        grant_access(vault_dir, "myapp", "alice", "read")
        revoke_access(vault_dir, "myapp", "alice", "read")
        assert check_access(vault_dir, "myapp", "alice", "read") is False

    def test_revoke_one_keeps_other(self, vault_dir):
        grant_access(vault_dir, "myapp", "alice", "read")
        grant_access(vault_dir, "myapp", "alice", "write")
        revoke_access(vault_dir, "myapp", "alice", "write")
        assert check_access(vault_dir, "myapp", "alice", "read") is True
        assert check_access(vault_dir, "myapp", "alice", "write") is False

    def test_revoke_nonexistent_is_noop(self, vault_dir):
        revoke_access(vault_dir, "myapp", "ghost", "read")  # should not raise


class TestCheckAccess:
    def test_returns_false_when_no_policy(self, vault_dir):
        assert check_access(vault_dir, "myapp", "alice", "read") is False

    def test_returns_false_for_missing_profile(self, vault_dir):
        grant_access(vault_dir, "myapp", "alice", "read")
        assert check_access(vault_dir, "myapp", "bob", "read") is False


class TestListAccess:
    def test_returns_empty_when_no_policy(self, vault_dir):
        assert list_access(vault_dir) == {}

    def test_filters_by_vault_name(self, vault_dir):
        grant_access(vault_dir, "app1", "alice", "read")
        grant_access(vault_dir, "app2", "bob", "write")
        result = list_access(vault_dir, "app1")
        assert "app1:alice" in result
        assert "app2:bob" not in result

    def test_returns_all_when_no_filter(self, vault_dir):
        grant_access(vault_dir, "app1", "alice", "read")
        grant_access(vault_dir, "app2", "bob", "write")
        result = list_access(vault_dir)
        assert len(result) == 2
