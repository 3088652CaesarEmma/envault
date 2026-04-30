"""CLI commands for managing envault secret templates."""

from __future__ import annotations

import click

from envault.templates import (
    apply_template,
    delete_template,
    list_templates,
    save_template,
)
from envault.vault import load_vault
from envault.passphrase import get_passphrase
from envault.export_formats import render_secrets


@click.group("template")
def template_group() -> None:
    """Manage reusable secret key templates."""


@template_group.command("save")
@click.argument("name")
@click.argument("keys", nargs=-1, required=True)
def save_template_cmd(name: str, keys: tuple) -> None:
    """Save a named template with the given secret KEYS."""
    try:
        save_template(name, list(keys))
        click.echo(f"Template '{name}' saved with keys: {', '.join(keys)}")
    except ValueError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@template_group.command("delete")
@click.argument("name")
def delete_template_cmd(name: str) -> None:
    """Delete a saved template by NAME."""
    try:
        delete_template(name)
        click.echo(f"Template '{name}' deleted.")
    except KeyError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@template_group.command("list")
def list_templates_cmd() -> None:
    """List all saved templates."""
    templates = list_templates()
    if not templates:
        click.echo("No templates saved.")
        return
    for name, keys in templates.items():
        click.echo(f"{name}: {', '.join(keys)}")


@template_group.command("apply")
@click.argument("template_name")
@click.argument("vault_name")
@click.option("--format", "fmt", default="dotenv", show_default=True,
              type=click.Choice(["dotenv", "json", "shell"]),
              help="Output format.")
def apply_template_cmd(template_name: str, vault_name: str, fmt: str) -> None:
    """Apply TEMPLATE_NAME to VAULT_NAME and print matching secrets."""
    try:
        passphrase = get_passphrase()
        vault = load_vault(vault_name, passphrase)
        secrets = apply_template(template_name, vault.get("secrets", {}))
        click.echo(render_secrets(secrets, fmt))
    except (KeyError, ValueError) as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)
