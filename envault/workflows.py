"""Workflow automation: chain multiple vault operations into named sequences."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from envault.vault import _get_vault_path, load_vault, save_vault
from envault.audit import record_event

_WORKFLOWS_FILE = Path.home() / ".envault" / "workflows.json"


def _load_workflows() -> dict[str, Any]:
    if not _WORKFLOWS_FILE.exists():
        return {}
    return json.loads(_WORKFLOWS_FILE.read_text())


def _save_workflows(data: dict[str, Any]) -> None:
    _WORKFLOWS_FILE.parent.mkdir(parents=True, exist_ok=True)
    _WORKFLOWS_FILE.write_text(json.dumps(data, indent=2))


def save_workflow(name: str, steps: list[dict[str, Any]]) -> dict[str, Any]:
    """Persist a named workflow with an ordered list of step definitions."""
    if not name:
        raise ValueError("Workflow name must not be empty")
    if not steps:
        raise ValueError("Workflow must contain at least one step")
    workflows = _load_workflows()
    entry = {"name": name, "steps": steps}
    workflows[name] = entry
    _save_workflows(workflows)
    record_event("workflow_saved", {"workflow": name, "step_count": len(steps)})
    return entry


def delete_workflow(name: str) -> None:
    """Remove a workflow by name."""
    workflows = _load_workflows()
    if name not in workflows:
        raise KeyError(f"Workflow '{name}' not found")
    del workflows[name]
    _save_workflows(workflows)
    record_event("workflow_deleted", {"workflow": name})


def list_workflows() -> list[str]:
    """Return names of all saved workflows."""
    return list(_load_workflows().keys())


def get_workflow(name: str) -> dict[str, Any]:
    """Fetch a single workflow definition by name."""
    workflows = _load_workflows()
    if name not in workflows:
        raise KeyError(f"Workflow '{name}' not found")
    return workflows[name]


def run_workflow(name: str, passphrase: str) -> list[dict[str, Any]]:
    """Execute every step in a workflow and return per-step results."""
    workflow = get_workflow(name)
    results: list[dict[str, Any]] = []
    for step in workflow["steps"]:
        action = step.get("action")
        vault_name = step.get("vault")
        key = step.get("key")
        value = step.get("value")
        try:
            vault = load_vault(vault_name, passphrase)
            if action == "set":
                vault["secrets"][key] = value
                save_vault(vault_name, vault, passphrase)
                results.append({"step": step, "status": "ok"})
            elif action == "delete":
                vault["secrets"].pop(key, None)
                save_vault(vault_name, vault, passphrase)
                results.append({"step": step, "status": "ok"})
            else:
                results.append({"step": step, "status": "error", "reason": f"unknown action '{action}'"})
        except Exception as exc:  # noqa: BLE001
            results.append({"step": step, "status": "error", "reason": str(exc)})
    record_event("workflow_run", {"workflow": name, "steps": len(workflow["steps"])})
    return results
