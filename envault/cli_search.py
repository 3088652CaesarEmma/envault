"""CLI commands for searching secrets across vaults."""

import click

from envault.passphrase import get_passphrase
from envault.search import search_by_key, search_by_value


@click.group("search")
def search_group() -> None:
    """Search secrets across vaults."""


@search_group.command("key")
@click.argument("pattern")
@click.option("--vault", "-v", "vault_names", multiple=True, help="Vault(s) to search (default: all).")
@click.option("--regex", is_flag=True, default=False, help="Treat pattern as a regex instead of a glob.")
@click.option("--show-values", is_flag=True, default=False, help="Print secret values alongside keys.")
def search_key(pattern: str, vault_names: tuple, regex: bool, show_values: bool) -> None:
    """Search for keys matching PATTERN across vaults."""
    passphrase = get_passphrase()
    vaults = list(vault_names) or None
    results = search_by_key(pattern, passphrase, vault_names=vaults, glob=not regex)

    if not results:
        click.echo("No matching keys found.")
        return

    for r in results:
        tag_str = f"  [{', '.join(r.tags)}]" if r.tags else ""
        if show_values:
            click.echo(f"{r.vault_name}  {r.key}={r.value}{tag_str}")
        else:
            click.echo(f"{r.vault_name}  {r.key}{tag_str}")


@search_group.command("value")
@click.argument("pattern")
@click.option("--vault", "-v", "vault_names", multiple=True, help="Vault(s) to search (default: all).")
def search_value(pattern: str, vault_names: tuple) -> None:
    """Search for secrets whose value matches the regex PATTERN."""
    passphrase = get_passphrase()
    vaults = list(vault_names) or None
    results = search_by_value(pattern, passphrase, vault_names=vaults)

    if not results:
        click.echo("No matching secrets found.")
        return

    for r in results:
        tag_str = f"  [{', '.join(r.tags)}]" if r.tags else ""
        click.echo(f"{r.vault_name}  {r.key}={r.value}{tag_str}")
