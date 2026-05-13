"""Tests for envault/cli_groups.py."""

from __future__ import annotations

import pytest
from click.testing import CliRunner

from envault.cli_groups import groups_group


@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture()
def mock_passphrase(monkeypatch):
    monkeypatch.setattr("envault.cli_groups.get_passphrase", lambda *a: "testpass")


@pytest.fixture()
def mock_ops(monkeypatch):
    calls: dict = {}

    def fake_add(vault, group, key, pw):
        calls["add"] = (vault, group, key)

    def fake_remove(vault, group, key, pw):
        calls["remove"] = (vault, group, key)

    def fake_list(vault, pw):
        return {"grp1": ["KEY_A", "KEY_B"], "grp2": ["KEY_C"]}

    def fake_members(vault, group, pw):
        if group == "grp1":
            return ["KEY_A", "KEY_B"]
        raise KeyError(group)

    def fake_delete(vault, group, pw):
        calls["delete"] = (vault, group)

    monkeypatch.setattr("envault.cli_groups.add_to_group", fake_add)
    monkeypatch.setattr("envault.cli_groups.remove_from_group", fake_remove)
    monkeypatch.setattr("envault.cli_groups.list_groups", fake_list)
    monkeypatch.setattr("envault.cli_groups.get_group_members", fake_members)
    monkeypatch.setattr("envault.cli_groups.delete_group", fake_delete)
    return calls


def test_add_success(runner, mock_passphrase, mock_ops):
    result = runner.invoke(groups_group, ["add", "myvault", "grp1", "KEY_A"])
    assert result.exit_code == 0
    assert "KEY_A" in result.output
    assert "grp1" in result.output


def test_add_missing_key_exits_1(runner, mock_passphrase, monkeypatch):
    monkeypatch.setattr(
        "envault.cli_groups.add_to_group",
        lambda *a: (_ for _ in ()).throw(KeyError("MISSING")),
    )
    result = runner.invoke(groups_group, ["add", "myvault", "grp", "MISSING"])
    assert result.exit_code == 1


def test_remove_success(runner, mock_passphrase, mock_ops):
    result = runner.invoke(groups_group, ["remove", "myvault", "grp1", "KEY_A"])
    assert result.exit_code == 0
    assert "KEY_A" in result.output


def test_list_all_groups(runner, mock_passphrase, mock_ops):
    result = runner.invoke(groups_group, ["list", "myvault"])
    assert result.exit_code == 0
    assert "grp1" in result.output
    assert "grp2" in result.output


def test_list_specific_group(runner, mock_passphrase, mock_ops):
    result = runner.invoke(groups_group, ["list", "myvault", "--group", "grp1"])
    assert result.exit_code == 0
    assert "KEY_A" in result.output


def test_list_unknown_group_exits_1(runner, mock_passphrase, mock_ops):
    result = runner.invoke(groups_group, ["list", "myvault", "--group", "nope"])
    assert result.exit_code == 1


def test_delete_success(runner, mock_passphrase, mock_ops):
    result = runner.invoke(groups_group, ["delete", "myvault", "grp1"])
    assert result.exit_code == 0
    assert "grp1" in result.output


def test_delete_nonexistent_exits_1(runner, mock_passphrase, monkeypatch):
    monkeypatch.setattr(
        "envault.cli_groups.delete_group",
        lambda *a: (_ for _ in ()).throw(KeyError("ghost")),
    )
    result = runner.invoke(groups_group, ["delete", "myvault", "ghost"])
    assert result.exit_code == 1
