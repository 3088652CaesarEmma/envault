"""Tests for envault.watchers."""

from __future__ import annotations

import os
import time
from unittest.mock import MagicMock, patch

import pytest

import envault.watchers as wmod
from envault.watchers import (
    WatchEntry,
    add_watcher,
    get_watcher,
    list_watchers,
    poll_once,
    remove_watcher,
)


@pytest.fixture(autouse=True)
def clear_registry():
    wmod._WATCHERS.clear()
    yield
    wmod._WATCHERS.clear()


@pytest.fixture()
def env_file(tmp_path):
    p = tmp_path / ".env"
    p.write_text("KEY=value\n")
    return str(p)


# ---------------------------------------------------------------------------
# add_watcher
# ---------------------------------------------------------------------------

class TestAddWatcher:
    def test_returns_watch_entry(self, env_file):
        with patch("envault.watchers.record_event"):
            entry = add_watcher("myapp", env_file)
        assert isinstance(entry, WatchEntry)

    def test_stores_absolute_path(self, env_file):
        with patch("envault.watchers.record_event"):
            entry = add_watcher("myapp", env_file)
        assert os.path.isabs(entry.env_path)

    def test_records_current_mtime(self, env_file):
        with patch("envault.watchers.record_event"):
            entry = add_watcher("myapp", env_file)
        assert entry.last_mtime == pytest.approx(os.path.getmtime(env_file), abs=1)

    def test_watcher_appears_in_list(self, env_file):
        with patch("envault.watchers.record_event"):
            add_watcher("myapp", env_file)
        assert get_watcher("myapp") is not None


# ---------------------------------------------------------------------------
# remove_watcher
# ---------------------------------------------------------------------------

class TestRemoveWatcher:
    def test_removes_existing(self, env_file):
        with patch("envault.watchers.record_event"):
            add_watcher("myapp", env_file)
            remove_watcher("myapp")
        assert get_watcher("myapp") is None

    def test_raises_on_missing(self):
        with pytest.raises(KeyError, match="myapp"):
            remove_watcher("myapp")


# ---------------------------------------------------------------------------
# list_watchers
# ---------------------------------------------------------------------------

def test_list_returns_all_entries(env_file, tmp_path):
    second = tmp_path / ".env2"
    second.write_text("X=1\n")
    with patch("envault.watchers.record_event"):
        add_watcher("app1", env_file)
        add_watcher("app2", str(second))
    assert len(list_watchers()) == 2


# ---------------------------------------------------------------------------
# poll_once
# ---------------------------------------------------------------------------

class TestPollOnce:
    def test_no_sync_when_file_unchanged(self, env_file):
        with patch("envault.watchers.record_event"):
            add_watcher("myapp", env_file)
        with patch("envault.watchers.sync_env_to_vault") as mock_sync:
            result = poll_once("myapp", "secret")
        assert result is False
        mock_sync.assert_not_called()

    def test_syncs_when_mtime_advances(self, env_file):
        with patch("envault.watchers.record_event"):
            entry = add_watcher("myapp", env_file)
        # Force mtime to appear older
        entry.last_mtime = 0.0
        with patch("envault.watchers.sync_env_to_vault") as mock_sync, \
             patch("envault.watchers.record_event"):
            result = poll_once("myapp", "secret")
        assert result is True
        mock_sync.assert_called_once()

    def test_increments_hit_count(self, env_file):
        with patch("envault.watchers.record_event"):
            entry = add_watcher("myapp", env_file)
        entry.last_mtime = 0.0
        with patch("envault.watchers.sync_env_to_vault"), \
             patch("envault.watchers.record_event"):
            poll_once("myapp", "secret")
        assert entry.hit_count == 1

    def test_returns_false_for_unknown_vault(self):
        result = poll_once("ghost", "secret")
        assert result is False

    def test_skips_disabled_watcher(self, env_file):
        with patch("envault.watchers.record_event"):
            entry = add_watcher("myapp", env_file)
        entry.enabled = False
        entry.last_mtime = 0.0
        with patch("envault.watchers.sync_env_to_vault") as mock_sync:
            result = poll_once("myapp", "secret")
        assert result is False
        mock_sync.assert_not_called()
