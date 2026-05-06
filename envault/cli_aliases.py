"""CLI commands for managing key aliases."""

from __future__ import annotations

import click

from envault.aliases import set_alias, remove_alias, resolve_alias, list_aliases
from envault.vault import load_vault
from envault.passphrase import get_passphrase


@click.group("alias")
def alias_group() -> None:
    """Manage friendly aliases for vault keys."""


@alias_group.command("set")
@click.argument("vault_name")
@click.argument("alias")
@click.argument("target_key")
def set_alias_cmd(vault_name: str, alias: str, target_key: str) -> None:
    """Map ALIAS to TARGET_KEY inside VAULT_NAME."""
    try:
        passphrase = get_passphrase()
        set_alias(vault_name, alias, target_key, passphrase)
        click.echo(f"Alias '{alias}' -> '{target_key}' saved in vault '{vault_name}'.")
    except KeyError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@alias_group.command("remove")
@click.argument("vault_name")
@click.argument("alias")
def remove_alias_cmd(vault_name: str, alias: str) -> None:
    """Remove ALIAS from VAULT_NAME."""
    try:
        passphrase = get_passphrase()
        remove_alias(vault_name, alias, passphrase)
        click.echo(f"Alias '{alias}' removed from vault '{vault_name}'.")
    except KeyError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@alias_group.command("resolve")
@click.argument("vault_name")
@click.argument("alias")
def resolve_alias_cmd(vault_name: str, alias: str) -> None:
    """Print the key that ALIAS points to in VAULT_NAME."""
    passphrase = get_passphrase()
    vault = load_vault(vault_name, passphrase)
    target = resolve_alias(vault, alias)
    if target is None:
        click.echo(f"No alias '{alias}' found in vault '{vault_name}'.", err=True)
        raise SystemExit(1)
    click.echo(target)


@alias_group.command("list")
@click.argument("vault_name")
def list_aliases_cmd(vault_name: str) -> None:
    """List all aliases defined in VAULT_NAME."""
    passphrase = get_passphrase()
    vault = load_vault(vault_name, passphrase)
    entries = list_aliases(vault)
    if not entries:
        click.echo("No aliases defined.")
        return
    for entry in entries:
        click.echo(f"{entry['alias']} -> {entry['target']}")
