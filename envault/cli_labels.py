"""CLI commands for managing key labels."""

from __future__ import annotations

import click

from envault.labels import set_label, get_label, clear_label, list_labeled_keys
from envault.passphrase import get_passphrase


@click.group("labels")
def labels_group() -> None:
    """Manage human-readable labels for vault keys."""


@labels_group.command("set")
@click.argument("vault_name")
@click.argument("key")
@click.argument("label")
def set_label_cmd(vault_name: str, key: str, label: str) -> None:
    """Attach LABEL to KEY in VAULT_NAME."""
    try:
        passphrase = get_passphrase()
        set_label(vault_name, key, label, passphrase)
        click.echo(f"Label '{label}' set on key '{key}'.")
    except KeyError as exc:
        click.echo(str(exc), err=True)
        raise SystemExit(1)


@labels_group.command("get")
@click.argument("vault_name")
@click.argument("key")
def get_label_cmd(vault_name: str, key: str) -> None:
    """Print the label attached to KEY in VAULT_NAME."""
    try:
        passphrase = get_passphrase()
        label = get_label(vault_name, key, passphrase)
        if label is None:
            click.echo(f"No label set for key '{key}'.")
        else:
            click.echo(label)
    except KeyError as exc:
        click.echo(str(exc), err=True)
        raise SystemExit(1)


@labels_group.command("clear")
@click.argument("vault_name")
@click.argument("key")
def clear_label_cmd(vault_name: str, key: str) -> None:
    """Remove the label from KEY in VAULT_NAME."""
    try:
        passphrase = get_passphrase()
        clear_label(vault_name, key, passphrase)
        click.echo(f"Label cleared from key '{key}'.")
    except KeyError as exc:
        click.echo(str(exc), err=True)
        raise SystemExit(1)


@labels_group.command("list")
@click.argument("vault_name")
def list_labels_cmd(vault_name: str) -> None:
    """List all labeled keys in VAULT_NAME."""
    passphrase = get_passphrase()
    labeled = list_labeled_keys(vault_name, passphrase)
    if not labeled:
        click.echo("No labeled keys found.")
        return
    for key, label in sorted(labeled.items()):
        click.echo(f"{key}: {label}")
