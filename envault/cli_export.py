"""CLI commands for exporting vault secrets in various formats."""

import sys
import click

from envault.vault import load_vault
from envault.crypto import decrypt
from envault.passphrase import get_passphrase
from envault.export_formats import render_secrets, SUPPORTED_FORMATS
from envault.audit import record_event


@click.group(name="export")
def export_group():
    """Export secrets from a vault in different formats."""


@export_group.command(name="render")
@click.argument("vault_name")
@click.option(
    "--format", "fmt",
    default="dotenv",
    show_default=True,
    type=click.Choice(SUPPORTED_FORMATS, case_sensitive=False),
    help="Output format for the secrets.",
)
@click.option(
    "--output", "-o",
    default=None,
    type=click.Path(),
    help="Write output to a file instead of stdout.",
)
def render_vault(vault_name: str, fmt: str, output):
    """Render all secrets from VAULT_NAME in the chosen format."""
    try:
        passphrase = get_passphrase()
        vault = load_vault(vault_name, passphrase)
    except FileNotFoundError:
        click.echo(f"Error: vault '{vault_name}' not found.", err=True)
        sys.exit(1)
    except Exception as exc:  # noqa: BLE001
        click.echo(f"Error loading vault: {exc}", err=True)
        sys.exit(1)

    secrets = vault.get("secrets", {})

    try:
        rendered = render_secrets(secrets, fmt.lower())
    except ValueError as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)

    if output:
        with open(output, "w", encoding="utf-8") as fh:
            fh.write(rendered)
        click.echo(f"Secrets written to {output} ({fmt} format).")
    else:
        click.echo(rendered, nl=False)

    record_event("export_render", {"vault": vault_name, "format": fmt})
