"""CLI commands for managing key annotations."""

import click

from envault.annotations import (
    set_annotation,
    get_annotation,
    clear_annotation,
    list_annotated_keys,
)
from envault.passphrase import get_passphrase


@click.group("annotations")
def annotations_group():
    """Attach notes/annotations to secret keys."""


@annotations_group.command("set")
@click.argument("vault_name")
@click.argument("key")
@click.argument("note")
def set_annotation_cmd(vault_name: str, key: str, note: str) -> None:
    """Set an annotation on KEY in VAULT_NAME."""
    passphrase = get_passphrase()
    try:
        set_annotation(vault_name, key, note, passphrase)
        click.echo(f"Annotation set on '{key}' in vault '{vault_name}'.")
    except KeyError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@annotations_group.command("get")
@click.argument("vault_name")
@click.argument("key")
def get_annotation_cmd(vault_name: str, key: str) -> None:
    """Get the annotation for KEY in VAULT_NAME."""
    passphrase = get_passphrase()
    try:
        note = get_annotation(vault_name, key, passphrase)
        if note is None:
            click.echo(f"No annotation set for '{key}'.")
        else:
            click.echo(note)
    except KeyError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@annotations_group.command("clear")
@click.argument("vault_name")
@click.argument("key")
def clear_annotation_cmd(vault_name: str, key: str) -> None:
    """Remove the annotation from KEY in VAULT_NAME."""
    passphrase = get_passphrase()
    try:
        clear_annotation(vault_name, key, passphrase)
        click.echo(f"Annotation cleared for '{key}'.")
    except KeyError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@annotations_group.command("list")
@click.argument("vault_name")
def list_annotations_cmd(vault_name: str) -> None:
    """List all annotated keys in VAULT_NAME."""
    passphrase = get_passphrase()
    entries = list_annotated_keys(vault_name, passphrase)
    if not entries:
        click.echo("No annotated keys found.")
        return
    for item in entries:
        click.echo(f"  {item['key']}: {item['annotation']}")
