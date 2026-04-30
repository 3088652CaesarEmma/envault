"""CLI commands for diffing vault secrets against .env files."""

import click

from envault.audit import record_event
from envault.diff import diff_vault_vs_env, format_diff
from envault.env_parser import parse_env_file
from envault.passphrase import get_passphrase
from envault.vault import load_vault


@click.group("diff")
def diff_group():
    """Compare vault secrets with .env files."""


@diff_group.command("show")
@click.argument("vault_name")
@click.argument("env_file", type=click.Path(exists=True))
@click.option("--show-values", is_flag=True, default=False, help="Show changed values in output.")
@click.option("--only", type=click.Choice(["added", "removed", "modified", "unchanged"]), default=None,
              help="Filter output to a specific diff status.")
def show_diff(vault_name: str, env_file: str, show_values: bool, only: str):
    """Show diff between VAULT_NAME and ENV_FILE."""
    try:
        passphrase = get_passphrase()
        vault = load_vault(vault_name, passphrase)
        vault_secrets = vault.get("secrets", {})
    except Exception as e:
        click.echo(f"Error loading vault '{vault_name}': {e}", err=True)
        raise SystemExit(1)

    try:
        env_secrets = parse_env_file(env_file)
    except Exception as e:
        click.echo(f"Error reading env file '{env_file}': {e}", err=True)
        raise SystemExit(1)

    entries = diff_vault_vs_env(vault_secrets, env_secrets)

    if only:
        entries = [e for e in entries if e.status == only]

    if not entries:
        click.echo("No differences found.")
        return

    summary = {"added": 0, "removed": 0, "modified": 0, "unchanged": 0}
    for entry in entries:
        summary[entry.status] += 1

    click.echo(format_diff(entries, show_values=show_values))
    click.echo()
    click.echo(
        f"Summary: +{summary['added']} added, -{summary['removed']} removed, "
        f"~{summary['modified']} modified, {summary['unchanged']} unchanged"
    )

    record_event("diff", {"vault": vault_name, "env_file": env_file})
