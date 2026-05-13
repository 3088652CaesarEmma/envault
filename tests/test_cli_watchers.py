"""Tests for envault.cli_watchers."""

from __future__ import annotations

from unittest.mock import patch

import pytest
from click.testing import CliRunner

import envault.watchers as wmod
from envault.cli_watchers import watchers_group


@pytest.fixture(autouse=True)
def clear_registry():
    wmod._WATCHERS.clear()
    yield
    wmod._WATCHERS.clear()


@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture()
def mock_passphrase():
    with patch("envault.cli_watchers.get_passphrase", return_value="s3cr3t"):
        yield


@pytest.fixture()
def env_file(tmp_path):
    p = tmp_path / ".env"
    p.write_text("A=1\n")
    return str(p)


# ---------------------------------------------------------------------------
# add
# ---------------------------------------------------------------------------

def test_add_watcher_success(runner, env_file):
    with patch("envault.watchers.record_event"):
        result = runner.invoke(watchers_group, ["add", "myapp", env_file])
    assert result.exit_code == 0
    assert "myapp" in result.output


def test_add_watcher_missing_file(runner, tmp_path):
    ghost = str(tmp_path / "ghost.env")
    with patch("envault.watchers.record_event"):
        result = runner.invoke(watchers_group, ["add", "myapp", ghost])
    # File doesn't exist — add_watcher still registers with mtime 0; exit 0
    assert result.exit_code == 0


# ---------------------------------------------------------------------------
# remove
# ---------------------------------------------------------------------------

def test_remove_watcher_success(runner, env_file):
    with patch("envault.watchers.record_event"):
        wmod.add_watcher("myapp", env_file)
    with patch("envault.watchers.record_event"):
        result = runner.invoke(watchers_group, ["remove", "myapp"])
    assert result.exit_code == 0
    assert "removed" in result.output


def test_remove_watcher_not_found(runner):
    result = runner.invoke(watchers_group, ["remove", "ghost"])
    assert result.exit_code == 1


# ---------------------------------------------------------------------------
# list
# ---------------------------------------------------------------------------

def test_list_empty(runner):
    result = runner.invoke(watchers_group, ["list"])
    assert result.exit_code == 0
    assert "No watchers" in result.output


def test_list_shows_entries(runner, env_file):
    with patch("envault.watchers.record_event"):
        wmod.add_watcher("myapp", env_file)
    result = runner.invoke(watchers_group, ["list"])
    assert "myapp" in result.output


# ---------------------------------------------------------------------------
# poll --once
# ---------------------------------------------------------------------------

def test_poll_once_no_changes(runner, env_file, mock_passphrase):
    with patch("envault.watchers.record_event"):
        wmod.add_watcher("myapp", env_file)
    result = runner.invoke(watchers_group, ["poll", "myapp", "--once"])
    assert result.exit_code == 0
    assert "No changes" in result.output


def test_poll_once_syncs(runner, env_file, mock_passphrase):
    with patch("envault.watchers.record_event"):
        entry = wmod.add_watcher("myapp", env_file)
    entry.last_mtime = 0.0
    with patch("envault.watchers.sync_env_to_vault"), \
         patch("envault.watchers.record_event"):
        result = runner.invoke(watchers_group, ["poll", "myapp", "--once"])
    assert result.exit_code == 0
    assert "Synced" in result.output
