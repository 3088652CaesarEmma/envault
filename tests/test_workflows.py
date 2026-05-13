"""Tests for envault.workflows."""
from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from envault.workflows import (
    delete_workflow,
    get_workflow,
    list_workflows,
    run_workflow,
    save_workflow,
)


@pytest.fixture()
def patched(tmp_path, monkeypatch):
    wf_file = tmp_path / "workflows.json"
    monkeypatch.setattr("envault.workflows._WORKFLOWS_FILE", wf_file)
    monkeypatch.setattr("envault.workflows.record_event", lambda *a, **kw: None)
    return wf_file


SIMPLE_STEP = [{"action": "set", "vault": "myapp", "key": "TOKEN", "value": "abc"}]


class TestSaveWorkflow:
    def test_saves_and_returns_entry(self, patched):
        entry = save_workflow("deploy", SIMPLE_STEP)
        assert entry["name"] == "deploy"
        assert entry["steps"] == SIMPLE_STEP

    def test_persists_to_file(self, patched):
        save_workflow("deploy", SIMPLE_STEP)
        data = json.loads(patched.read_text())
        assert "deploy" in data

    def test_overwrites_existing(self, patched):
        save_workflow("deploy", SIMPLE_STEP)
        new_steps = [{"action": "delete", "vault": "myapp", "key": "TOKEN"}]
        save_workflow("deploy", new_steps)
        wf = get_workflow("deploy")
        assert wf["steps"][0]["action"] == "delete"

    def test_raises_on_empty_name(self, patched):
        with pytest.raises(ValueError, match="name"):
            save_workflow("", SIMPLE_STEP)

    def test_raises_on_empty_steps(self, patched):
        with pytest.raises(ValueError, match="step"):
            save_workflow("empty", [])


class TestDeleteWorkflow:
    def test_removes_workflow(self, patched):
        save_workflow("ci", SIMPLE_STEP)
        delete_workflow("ci")
        assert "ci" not in list_workflows()

    def test_raises_on_missing(self, patched):
        with pytest.raises(KeyError):
            delete_workflow("nonexistent")


class TestListWorkflows:
    def test_empty_when_none_saved(self, patched):
        assert list_workflows() == []

    def test_returns_all_names(self, patched):
        save_workflow("a", SIMPLE_STEP)
        save_workflow("b", SIMPLE_STEP)
        assert set(list_workflows()) == {"a", "b"}


class TestRunWorkflow:
    def _fake_vault(self):
        return {"secrets": {"EXISTING": "val"}}

    def test_set_action_returns_ok(self, patched):
        save_workflow("w", SIMPLE_STEP)
        with patch("envault.workflows.load_vault", return_value=self._fake_vault()), \
             patch("envault.workflows.save_vault"):
            results = run_workflow("w", "passphrase")
        assert results[0]["status"] == "ok"

    def test_delete_action_returns_ok(self, patched):
        steps = [{"action": "delete", "vault": "myapp", "key": "TOKEN"}]
        save_workflow("del_wf", steps)
        with patch("envault.workflows.load_vault", return_value=self._fake_vault()), \
             patch("envault.workflows.save_vault"):
            results = run_workflow("del_wf", "passphrase")
        assert results[0]["status"] == "ok"

    def test_unknown_action_returns_error(self, patched):
        steps = [{"action": "explode", "vault": "myapp", "key": "K"}]
        save_workflow("bad", steps)
        with patch("envault.workflows.load_vault", return_value=self._fake_vault()), \
             patch("envault.workflows.save_vault"):
            results = run_workflow("bad", "passphrase")
        assert results[0]["status"] == "error"
        assert "explode" in results[0]["reason"]

    def test_load_vault_error_captured(self, patched):
        save_workflow("err", SIMPLE_STEP)
        with patch("envault.workflows.load_vault", side_effect=RuntimeError("boom")):
            results = run_workflow("err", "passphrase")
        assert results[0]["status"] == "error"
        assert "boom" in results[0]["reason"]

    def test_raises_key_error_for_missing_workflow(self, patched):
        with pytest.raises(KeyError):
            run_workflow("ghost", "passphrase")
