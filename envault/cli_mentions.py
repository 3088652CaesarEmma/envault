"""cli_mentions.py – CLI commands for the mentions / cross-reference feature."""
import click

from envault.mentions import find_mentions, list_cross_references, format_mentions
from envault.passphrase import get_passphrase


@click.group("mentions", help="Search for key mentions across all vaults.")
def mentions_group() -> None:  # pragma: no cover
    pass


@mentions_group.command("find")
@click.argument("key")
def find_cmd(key: str) -> None:
    """Find all vaults that contain a key matching KEY (case-insensitive substring)."""
    passphrase = get_passphrase()
    results = find_mentions(key, passphrase)
    if not results:
        click.echo(f"No mentions of '{key}' found across vaults.")
        return
    click.echo(f"Mentions of '{key}':")
    click.echo(format_mentions(results))


@mentions_group.command("xref")
@click.option("--min-vaults", default=2, show_default=True,
              help="Only show keys present in at least this many vaults.")
def xref_cmd(min_vaults: int) -> None:
    """List keys that appear in multiple vaults (cross-reference report)."""
    passphrase = get_passphrase()
    cross = list_cross_references(passphrase)
    found_any = False
    for key, vault_map in sorted(cross.items()):
        if len(vault_map) >= min_vaults:
            found_any = True
            vaults_str = ", ".join(sorted(vault_map.keys()))
            click.echo(f"  {key}  →  {vaults_str}")
    if not found_any:
        click.echo(f"No keys found in {min_vaults}+ vaults.")
