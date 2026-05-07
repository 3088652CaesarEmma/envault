"""CLI commands for managing favorite keys in a vault."""

import click

from envault.favorites import mark_favorite, unmark_favorite, list_favorites
from envault.passphrase import get_passphrase


@click.group("favorites")
def favorites_group() -> None:
    """Manage favorite keys."""


@favorites_group.command("mark")
@click.argument("vault_name")
@click.argument("key")
def mark_cmd(vault_name: str, key: str) -> None:
    """Mark KEY as a favorite in VAULT_NAME."""
    try:
        passphrase = get_passphrase()
        mark_favorite(vault_name, key, passphrase)
        click.echo(f"✓ '{key}' marked as favorite in '{vault_name}'.")
    except KeyError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)
    except Exception as exc:  # noqa: BLE001
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@favorites_group.command("unmark")
@click.argument("vault_name")
@click.argument("key")
def unmark_cmd(vault_name: str, key: str) -> None:
    """Remove the favorite flag from KEY in VAULT_NAME."""
    try:
        passphrase = get_passphrase()
        unmark_favorite(vault_name, key, passphrase)
        click.echo(f"✓ '{key}' removed from favorites in '{vault_name}'.")
    except KeyError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)
    except Exception as exc:  # noqa: BLE001
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@favorites_group.command("list")
@click.argument("vault_name")
def list_cmd(vault_name: str) -> None:
    """List all favorite keys in VAULT_NAME."""
    try:
        passphrase = get_passphrase()
        keys = list_favorites(vault_name, passphrase)
        if not keys:
            click.echo("No favorites found.")
        else:
            for key in keys:
                click.echo(f"  ★ {key}")
    except Exception as exc:  # noqa: BLE001
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)
