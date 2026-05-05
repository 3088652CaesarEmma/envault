"""Tests for envault.history."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from envault.history import (
    record_history_event,
    read_history,
    clear_history,
    _get_history_path,
)


@pytest.fixture(autouse=True)
def history_dir(tmp_path, monkeypatch):
    monkeypatch.setenv("ENVAULT_HISTORY_DIR", str(tmp_path))
    return tmp_path


class TestRecordHistoryEvent:
    def test_returns_entry_dict(self):
        entry = record_history_event("myvault", "import")
        assert entry["vault"] == "myvault"
        assert entry["event"] == "import"
        assert "timestamp" in entry

    def test_creates_log_file(self, history_dir):
        record_history_event("myvault", "import")
        log_file = history_dir / "myvault.jsonl"
        assert log_file.exists()

    def test_appends_multiple_events(self):
        record_history_event("myvault", "import")
        record_history_event("myvault", "passphrase_rotate")
        entries = read_history("myvault")
        assert len(entries) == 2
        assert entries[0]["event"] == "import"
        assert entries[1]["event"] == "passphrase_rotate"

    def test_stores_metadata(self):
        record_history_event("myvault", "export", metadata={"format": "json"})
        entries = read_history("myvault")
        assert entries[0]["metadata"] == {"format": "json"}

    def test_entry_without_metadata_has_no_metadata_key(self):
        entry = record_history_event("myvault", "import")
        assert "metadata" not in entry

    def test_log_lines_are_valid_json(self, history_dir):
        record_history_event("myvault", "import")
        record_history_event("myvault", "export", metadata={"format": "dotenv"})
        log_file = history_dir / "myvault.jsonl"
        lines = log_file.read_text().strip().splitlines()
        assert len(lines) == 2
        for line in lines:
            obj = json.loads(line)
            assert "vault" in obj


class TestReadHistory:
    def test_returns_empty_list_for_unknown_vault(self):
        assert read_history("nonexistent") == []

    def test_returns_entries_in_order(self):
        for event in ("a", "b", "c"):
            record_history_event("ordered", event)
        entries = read_history("ordered")
        assert [e["event"] for e in entries] == ["a", "b", "c"]


class TestClearHistory:
    def test_removes_log_file(self, history_dir):
        record_history_event("myvault", "import")
        clear_history("myvault")
        assert not (history_dir / "myvault.jsonl").exists()

    def test_clear_nonexistent_does_not_raise(self):
        clear_history("ghost_vault")  # should not raise

    def test_read_after_clear_returns_empty(self):
        record_history_event("myvault", "import")
        clear_history("myvault")
        assert read_history("myvault") == []
