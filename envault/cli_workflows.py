"""CLI commands for workflow automation."""
import json

import click

from envault.workflows import (
    delete_workflow,
    get_workflow,
    list_workflows,
    run_workflow,
    save_workflow,
)
from envault.passphrase import get_passphrase


@click.group("workflow")
def workflow_group() -> None:
    """Manage and run multi-step vault workflows."""


@workflow_group.command("save")
@click.argument("name")
@click.argument("steps_json")
def save_cmd(name: str, steps_json: str) -> None:
    """Save a workflow from a JSON array of steps.

    STEPS_JSON  JSON array, e.g. '[{"action":"set","vault":"v","key":"K","value":"V"}]'
    """
    try:
        steps = json.loads(steps_json)
    except json.JSONDecodeError as exc:
        click.echo(f"Invalid JSON: {exc}", err=True)
        raise SystemExit(1)
    try:
        save_workflow(name, steps)
        click.echo(f"Workflow '{name}' saved with {len(steps)} step(s).")
    except ValueError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@workflow_group.command("delete")
@click.argument("name")
def delete_cmd(name: str) -> None:
    """Delete a saved workflow."""
    try:
        delete_workflow(name)
        click.echo(f"Workflow '{name}' deleted.")
    except KeyError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@workflow_group.command("list")
def list_cmd() -> None:
    """List all saved workflows."""
    names = list_workflows()
    if not names:
        click.echo("No workflows saved.")
        return
    for n in names:
        click.echo(n)


@workflow_group.command("show")
@click.argument("name")
def show_cmd(name: str) -> None:
    """Show steps of a workflow."""
    try:
        wf = get_workflow(name)
        click.echo(json.dumps(wf, indent=2))
    except KeyError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@workflow_group.command("run")
@click.argument("name")
def run_cmd(name: str) -> None:
    """Execute all steps in a workflow."""
    passphrase = get_passphrase()
    try:
        results = run_workflow(name, passphrase)
    except KeyError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)
    ok = sum(1 for r in results if r["status"] == "ok")
    fail = len(results) - ok
    for r in results:
        icon = "✓" if r["status"] == "ok" else "✗"
        action = r["step"].get("action", "?")
        key = r["step"].get("key", "?")
        vault = r["step"].get("vault", "?")
        line = f"  {icon} [{vault}] {action} {key}"
        if r["status"] == "error":
            line += f" — {r.get('reason', '')}"
        click.echo(line)
    click.echo(f"\nDone: {ok} succeeded, {fail} failed.")
    if fail:
        raise SystemExit(1)
