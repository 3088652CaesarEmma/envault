"""Tests for envault.cli_labels."""

from __future__ import annotations

import pytest
from click.testing import CliRunner

from envault.cli_labels import labels_group


@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture(autouse=True)
def mock_passphrase(monkeypatch):
    monkeypatch.setattr("envault.cli_labels.get_passphrase", lambda: "masterpass")


# ---------------------------------------------------------------------------
# set
# ---------------------------------------------------------------------------

def test_set_label_success(runner, monkeypatch):
    monkeypatch.setattr("envault.cli_labels.set_label", lambda v, k, l, p: None)
    result = runner.invoke(labels_group, ["set", "myvault", "API_KEY", "API Key"])
    assert result.exit_code == 0
    assert "set" in result.output


def test_set_label_missing_key(runner, monkeypatch):
    def boom(v, k, l, p):
        raise KeyError("API_KEY")
    monkeypatch.setattr("envault.cli_labels.set_label", boom)
    result = runner.invoke(labels_group, ["set", "myvault", "API_KEY", "Label"])
    assert result.exit_code == 1


# ---------------------------------------------------------------------------
# get
# ---------------------------------------------------------------------------

def test_get_label_prints_label(runner, monkeypatch):
    monkeypatch.setattr("envault.cli_labels.get_label", lambda v, k, p: "My Label")
    result = runner.invoke(labels_group, ["get", "myvault", "API_KEY"])
    assert result.exit_code == 0
    assert "My Label" in result.output


def test_get_label_none_prints_message(runner, monkeypatch):
    monkeypatch.setattr("envault.cli_labels.get_label", lambda v, k, p: None)
    result = runner.invoke(labels_group, ["get", "myvault", "API_KEY"])
    assert result.exit_code == 0
    assert "No label" in result.output


def test_get_label_missing_key_exits_1(runner, monkeypatch):
    monkeypatch.setattr("envault.cli_labels.get_label", lambda v, k, p: (_ for _ in ()).throw(KeyError("X")))
    result = runner.invoke(labels_group, ["get", "myvault", "X"])
    assert result.exit_code == 1


# ---------------------------------------------------------------------------
# clear
# ---------------------------------------------------------------------------

def test_clear_label_success(runner, monkeypatch):
    monkeypatch.setattr("envault.cli_labels.clear_label", lambda v, k, p: None)
    result = runner.invoke(labels_group, ["clear", "myvault", "API_KEY"])
    assert result.exit_code == 0
    assert "cleared" in result.output


# ---------------------------------------------------------------------------
# list
# ---------------------------------------------------------------------------

def test_list_labels_prints_entries(runner, monkeypatch):
    monkeypatch.setattr(
        "envault.cli_labels.list_labeled_keys",
        lambda v, p: {"A": "Alpha", "B": "Beta"},
    )
    result = runner.invoke(labels_group, ["list", "myvault"])
    assert result.exit_code == 0
    assert "A: Alpha" in result.output
    assert "B: Beta" in result.output


def test_list_labels_empty(runner, monkeypatch):
    monkeypatch.setattr("envault.cli_labels.list_labeled_keys", lambda v, p: {})
    result = runner.invoke(labels_group, ["list", "myvault"])
    assert result.exit_code == 0
    assert "No labeled" in result.output
