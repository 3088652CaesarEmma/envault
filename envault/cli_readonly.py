"""CLI commands for managing read-only key flags."""

import click

from envault.readonly import (
    mark_readonly,
    unmark_readonly,
    is_readonly,
    list_readonly_keys,
    ReadOnlyViolationError,
)
from envault.passphrase import get_passphrase
from envault.vault import load_vault


@click.group(name="readonly")
def readonly_group():
    """Manage read-only flags on vault keys."""


@readonly_group.command("mark")
@click.argument("vault_name")
@click.argument("key")
def mark_cmd(vault_name: str, key: str):
    """Mark KEY in VAULT_NAME as read-only."""
    passphrase = get_passphrase()
    try:
        mark_readonly(vault_name, key, passphrase)
        click.echo(f"Key '{key}' in '{vault_name}' is now read-only.")
    except KeyError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@readonly_group.command("unmark")
@click.argument("vault_name")
@click.argument("key")
def unmark_cmd(vault_name: str, key: str):
    """Remove the read-only flag from KEY in VAULT_NAME."""
    passphrase = get_passphrase()
    try:
        unmark_readonly(vault_name, key, passphrase)
        click.echo(f"Key '{key}' in '{vault_name}' is no longer read-only.")
    except KeyError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@readonly_group.command("check")
@click.argument("vault_name")
@click.argument("key")
def check_cmd(vault_name: str, key: str):
    """Check whether KEY in VAULT_NAME is read-only."""
    passphrase = get_passphrase()
    vault = load_vault(vault_name, passphrase)
    if key not in vault:
        click.echo(f"Error: Key '{key}' not found.", err=True)
        raise SystemExit(1)
    status = "read-only" if is_readonly(vault[key]) else "writable"
    click.echo(f"'{key}' is {status}.")


@readonly_group.command("list")
@click.argument("vault_name")
def list_cmd(vault_name: str):
    """List all read-only keys in VAULT_NAME."""
    passphrase = get_passphrase()
    keys = list_readonly_keys(vault_name, passphrase)
    if not keys:
        click.echo("No read-only keys found.")
    else:
        for k in keys:
            click.echo(k)
