"""CLI commands for tag management on vault secrets."""

import click
from envault.tags import add_tag, remove_tag, list_tags, filter_by_tag
from envault.passphrase import get_passphrase


@click.group(name="tags")
def tags_group():
    """Manage tags on vault secrets."""


@tags_group.command(name="add")
@click.argument("vault_name")
@click.argument("key")
@click.argument("tag")
def add_tag_cmd(vault_name: str, key: str, tag: str):
    """Add TAG to KEY in VAULT_NAME."""
    try:
        passphrase = get_passphrase()
        add_tag(vault_name, key, tag, passphrase)
        click.echo(f"Tag '{tag}' added to '{key}' in vault '{vault_name}'.")
    except (KeyError, ValueError) as e:
        click.echo(f"Error: {e}", err=True)
        raise SystemExit(1)


@tags_group.command(name="remove")
@click.argument("vault_name")
@click.argument("key")
@click.argument("tag")
def remove_tag_cmd(vault_name: str, key: str, tag: str):
    """Remove TAG from KEY in VAULT_NAME."""
    try:
        passphrase = get_passphrase()
        remove_tag(vault_name, key, tag, passphrase)
        click.echo(f"Tag '{tag}' removed from '{key}' in vault '{vault_name}'.")
    except (KeyError, ValueError) as e:
        click.echo(f"Error: {e}", err=True)
        raise SystemExit(1)


@tags_group.command(name="list")
@click.argument("vault_name")
@click.argument("key")
def list_tags_cmd(vault_name: str, key: str):
    """List all tags on KEY in VAULT_NAME."""
    try:
        passphrase = get_passphrase()
        tags = list_tags(vault_name, key, passphrase)
        if tags:
            click.echo("\n".join(tags))
        else:
            click.echo(f"No tags found for '{key}'.")
    except KeyError as e:
        click.echo(f"Error: {e}", err=True)
        raise SystemExit(1)


@tags_group.command(name="filter")
@click.argument("vault_name")
@click.argument("tag")
def filter_by_tag_cmd(vault_name: str, tag: str):
    """List all keys in VAULT_NAME that have TAG."""
    try:
        passphrase = get_passphrase()
        matches = filter_by_tag(vault_name, tag, passphrase)
        if matches:
            for k, v in matches.items():
                click.echo(f"{k}={v}")
        else:
            click.echo(f"No keys found with tag '{tag}'.")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise SystemExit(1)
