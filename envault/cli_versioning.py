"""CLI commands for key-level versioning."""

import click
from envault.versioning import push_version, list_versions, restore_version, clear_versions
from envault.passphrase import get_passphrase


@click.group("version")
def version_group():
    """Manage per-key version history."""


@version_group.command("push")
@click.argument("vault_name")
@click.argument("key")
def push_cmd(vault_name: str, key: str):
    """Snapshot the current value of KEY into its history."""
    passphrase = get_passphrase()
    try:
        entry = push_version(vault_name, key, passphrase)
        click.echo(f"Pushed version at {entry['timestamp']}")
    except (KeyError, ValueError) as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@version_group.command("list")
@click.argument("vault_name")
@click.argument("key")
def list_cmd(vault_name: str, key: str):
    """List version history for KEY."""
    passphrase = get_passphrase()
    try:
        versions = list_versions(vault_name, key, passphrase)
    except KeyError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)

    if not versions:
        click.echo("No version history found.")
        return

    for idx, v in enumerate(versions):
        click.echo(f"[{idx}] {v['timestamp']}  value={v['value']!r}")


@version_group.command("restore")
@click.argument("vault_name")
@click.argument("key")
@click.argument("index", type=int)
def restore_cmd(vault_name: str, key: str, index: int):
    """Restore KEY to version INDEX."""
    passphrase = get_passphrase()
    try:
        value = restore_version(vault_name, key, index, passphrase)
        click.echo(f"Restored '{key}' to version {index}: {value!r}")
    except (KeyError, ValueError, IndexError) as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@version_group.command("clear")
@click.argument("vault_name")
@click.argument("key")
@click.confirmation_option(prompt="Delete all version history for this key?")
def clear_cmd(vault_name: str, key: str):
    """Clear all version history for KEY."""
    passphrase = get_passphrase()
    try:
        count = clear_versions(vault_name, key, passphrase)
        click.echo(f"Cleared {count} version(s) for '{key}'.")
    except KeyError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)
