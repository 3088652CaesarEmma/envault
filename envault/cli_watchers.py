"""CLI commands for managing file-system watchers."""

from __future__ import annotations

import time

import click

from envault.passphrase import get_passphrase
from envault.watchers import (
    add_watcher,
    get_watcher,
    list_watchers,
    poll_once,
    remove_watcher,
)


@click.group("watch")
def watchers_group() -> None:
    """Monitor .env files and auto-sync changes into a vault."""


@watchers_group.command("add")
@click.argument("vault_name")
@click.argument("env_path")
def add_watcher_cmd(vault_name: str, env_path: str) -> None:
    """Register a watcher for ENV_PATH linked to VAULT_NAME."""
    try:
        entry = add_watcher(vault_name, env_path)
        click.echo(f"Watching '{entry.env_path}' → vault '{vault_name}'")
    except Exception as exc:  # noqa: BLE001
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@watchers_group.command("remove")
@click.argument("vault_name")
def remove_watcher_cmd(vault_name: str) -> None:
    """Remove the watcher for VAULT_NAME."""
    try:
        remove_watcher(vault_name)
        click.echo(f"Watcher for '{vault_name}' removed.")
    except KeyError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@watchers_group.command("list")
def list_watchers_cmd() -> None:
    """List all registered watchers."""
    entries = list_watchers()
    if not entries:
        click.echo("No watchers registered.")
        return
    for e in entries:
        status = "enabled" if e.enabled else "disabled"
        click.echo(f"{e.vault_name:20s}  {e.env_path}  [{status}]  syncs={e.hit_count}")


@watchers_group.command("poll")
@click.argument("vault_name")
@click.option("--interval", default=5, show_default=True, help="Poll interval in seconds.")
@click.option("--once", is_flag=True, help="Run a single check then exit.")
def poll_cmd(vault_name: str, interval: int, once: bool) -> None:
    """Poll VAULT_NAME's watched file for changes and sync if needed."""
    passphrase = get_passphrase()
    if once:
        synced = poll_once(vault_name, passphrase)
        click.echo("Synced." if synced else "No changes detected.")
        return

    click.echo(f"Polling every {interval}s. Press Ctrl+C to stop.")
    try:
        while True:
            poll_once(vault_name, passphrase)
            time.sleep(interval)
    except KeyboardInterrupt:
        click.echo("\nStopped.")
