"""Tests for envault.cli_workflows."""
from __future__ import annotations

import json
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from envault.cli_workflows import workflow_group


@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture(autouse=True)
def mock_passphrase():
    with patch("envault.cli_workflows.get_passphrase", return_value="s3cr3t"):
        yield


STEPS = json.dumps([{"action": "set", "vault": "app", "key": "K", "value": "V"}])


def test_save_workflow_success(runner):
    with patch("envault.cli_workflows.save_workflow", return_value={"name": "deploy", "steps": []}) as m:
        result = runner.invoke(workflow_group, ["save", "deploy", STEPS])
    assert result.exit_code == 0
    assert "deploy" in result.output
    m.assert_called_once()


def test_save_workflow_invalid_json(runner):
    result = runner.invoke(workflow_group, ["save", "deploy", "not-json"])
    assert result.exit_code == 1
    assert "Invalid JSON" in result.output


def test_save_workflow_value_error(runner):
    with patch("envault.cli_workflows.save_workflow", side_effect=ValueError("empty")):
        result = runner.invoke(workflow_group, ["save", "x", STEPS])
    assert result.exit_code == 1


def test_delete_workflow_success(runner):
    with patch("envault.cli_workflows.delete_workflow") as m:
        result = runner.invoke(workflow_group, ["delete", "deploy"])
    assert result.exit_code == 0
    m.assert_called_once_with("deploy")


def test_delete_workflow_missing(runner):
    with patch("envault.cli_workflows.delete_workflow", side_effect=KeyError("deploy")):
        result = runner.invoke(workflow_group, ["delete", "deploy"])
    assert result.exit_code == 1


def test_list_workflows_empty(runner):
    with patch("envault.cli_workflows.list_workflows", return_value=[]):
        result = runner.invoke(workflow_group, ["list"])
    assert "No workflows" in result.output


def test_list_workflows_shows_names(runner):
    with patch("envault.cli_workflows.list_workflows", return_value=["a", "b"]):
        result = runner.invoke(workflow_group, ["list"])
    assert "a" in result.output
    assert "b" in result.output


def test_run_workflow_all_ok(runner):
    results = [{"step": {"action": "set", "vault": "v", "key": "K"}, "status": "ok"}]
    with patch("envault.cli_workflows.run_workflow", return_value=results):
        result = runner.invoke(workflow_group, ["run", "deploy"])
    assert result.exit_code == 0
    assert "✓" in result.output


def test_run_workflow_with_failure(runner):
    results = [{"step": {"action": "set", "vault": "v", "key": "K"}, "status": "error", "reason": "oops"}]
    with patch("envault.cli_workflows.run_workflow", return_value=results):
        result = runner.invoke(workflow_group, ["run", "deploy"])
    assert result.exit_code == 1
    assert "✗" in result.output


def test_run_workflow_missing(runner):
    with patch("envault.cli_workflows.run_workflow", side_effect=KeyError("ghost")):
        result = runner.invoke(workflow_group, ["run", "ghost"])
    assert result.exit_code == 1
