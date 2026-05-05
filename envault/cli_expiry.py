"""CLI commands for managing secret expiry in envault."""

import click
from envault.expiry import set_expiry, clear_expiry, list_expired_keys, purge_expired_keys
from envault.passphrase import get_passphrase


@click.group(name="expiry")
def expiry_group():
    """Manage secret expiry / TTL settings."""


@expiry_group.command("set")
@click.argument("vault_name")
@click.argument("key")
@click.argument("ttl", type=int)
def set_expiry_cmd(vault_name: str, key: str, ttl: int):
    """Set TTL (seconds) on KEY in VAULT_NAME."""
    try:
        passphrase = get_passphrase()
        result = set_expiry(vault_name, key, ttl, passphrase)
        click.echo(f"Expiry set for '{key}': expires_at={result['expires_at']} ({ttl}s from now)")
    except KeyError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@expiry_group.command("clear")
@click.argument("vault_name")
@click.argument("key")
def clear_expiry_cmd(vault_name: str, key: str):
    """Remove expiry from KEY in VAULT_NAME."""
    try:
        passphrase = get_passphrase()
        clear_expiry(vault_name, key, passphrase)
        click.echo(f"Expiry cleared for '{key}'.")
    except KeyError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@expiry_group.command("list-expired")
@click.argument("vault_name")
def list_expired_cmd(vault_name: str):
    """List all expired keys in VAULT_NAME."""
    passphrase = get_passphrase()
    expired = list_expired_keys(vault_name, passphrase)
    if not expired:
        click.echo("No expired keys found.")
    else:
        click.echo(f"Expired keys in '{vault_name}':")
        for key in expired:
            click.echo(f"  - {key}")


@expiry_group.command("purge")
@click.argument("vault_name")
@click.confirmation_option(prompt="This will permanently delete all expired keys. Continue?")
def purge_expired_cmd(vault_name: str):
    """Purge all expired keys from VAULT_NAME."""
    passphrase = get_passphrase()
    purged = purge_expired_keys(vault_name, passphrase)
    if not purged:
        click.echo("Nothing to purge.")
    else:
        click.echo(f"Purged {len(purged)} expired key(s): {', '.join(purged)}")
