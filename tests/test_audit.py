"""Tests for envault/audit.py"""

import json
import pytest
from pathlib import Path

from envault.audit import record_event, read_events, clear_audit_log


@pytest.fixture
def audit_dir(tmp_path):
    return str(tmp_path)


class TestRecordEvent:
    def test_creates_log_file_on_first_write(self, audit_dir):
        record_event("import", "myapp", vault_dir=audit_dir)
        log_path = Path(audit_dir) / "audit.log"
        assert log_path.exists()

    def test_log_entry_has_expected_keys(self, audit_dir):
        record_event("export", "myapp", details="exported 3 keys", vault_dir=audit_dir)
        log_path = Path(audit_dir) / "audit.log"
        with open(log_path) as f:
            entry = json.loads(f.readline())
        assert "timestamp" in entry
        assert entry["action"] == "export"
        assert entry["vault"] == "myapp"
        assert entry["details"] == "exported 3 keys"

    def test_multiple_events_are_appended(self, audit_dir):
        record_event("import", "app1", vault_dir=audit_dir)
        record_event("export", "app1", vault_dir=audit_dir)
        record_event("delete", "app2", vault_dir=audit_dir)
        events = read_events(vault_dir=audit_dir)
        assert len(events) == 3

    def test_details_can_be_none(self, audit_dir):
        record_event("create", "newvault", vault_dir=audit_dir)
        events = read_events(vault_dir=audit_dir)
        assert events[0]["details"] is None


class TestReadEvents:
    def test_returns_empty_list_when_no_log(self, audit_dir):
        events = read_events(vault_dir=audit_dir)
        assert events == []

    def test_filters_by_vault_name(self, audit_dir):
        record_event("import", "alpha", vault_dir=audit_dir)
        record_event("import", "beta", vault_dir=audit_dir)
        record_event("export", "alpha", vault_dir=audit_dir)
        events = read_events(vault_name="alpha", vault_dir=audit_dir)
        assert len(events) == 2
        assert all(e["vault"] == "alpha" for e in events)

    def test_respects_limit(self, audit_dir):
        for i in range(10):
            record_event("import", "myvault", details=f"entry {i}", vault_dir=audit_dir)
        events = read_events(limit=5, vault_dir=audit_dir)
        assert len(events) == 5

    def test_returns_most_recent_events_when_limited(self, audit_dir):
        for i in range(5):
            record_event("import", "myvault", details=f"entry {i}", vault_dir=audit_dir)
        events = read_events(limit=3, vault_dir=audit_dir)
        assert events[-1]["details"] == "entry 4"


class TestClearAuditLog:
    def test_removes_log_file(self, audit_dir):
        record_event("import", "myvault", vault_dir=audit_dir)
        clear_audit_log(vault_dir=audit_dir)
        log_path = Path(audit_dir) / "audit.log"
        assert not log_path.exists()

    def test_clear_on_missing_log_does_not_raise(self, audit_dir):
        clear_audit_log(vault_dir=audit_dir)  # should not raise
