"""CLI commands for managing secret groups."""

import click

from envault.groups import (
    add_to_group,
    delete_group,
    get_group_members,
    list_groups,
    remove_from_group,
)
from envault.passphrase import get_passphrase


@click.group("groups", help="Organise vault keys into named groups.")
def groups_group() -> None:  # pragma: no cover
    pass


@groups_group.command("add")
@click.argument("vault")
@click.argument("group")
@click.argument("key")
def add_cmd(vault: str, group: str, key: str) -> None:
    """Add KEY to GROUP inside VAULT."""
    passphrase = get_passphrase(vault)
    try:
        add_to_group(vault, group, key, passphrase)
        click.echo(f"Added '{key}' to group '{group}' in vault '{vault}'.")
    except KeyError as exc:
        click.echo(str(exc), err=True)
        raise SystemExit(1)


@groups_group.command("remove")
@click.argument("vault")
@click.argument("group")
@click.argument("key")
def remove_cmd(vault: str, group: str, key: str) -> None:
    """Remove KEY from GROUP inside VAULT."""
    passphrase = get_passphrase(vault)
    try:
        remove_from_group(vault, group, key, passphrase)
        click.echo(f"Removed '{key}' from group '{group}' in vault '{vault}'.")
    except KeyError as exc:
        click.echo(str(exc), err=True)
        raise SystemExit(1)


@groups_group.command("list")
@click.argument("vault")
@click.option("--group", default=None, help="Show members of a specific group.")
def list_cmd(vault: str, group: str | None) -> None:
    """List all groups (or members of a specific group) in VAULT."""
    passphrase = get_passphrase(vault)
    try:
        if group:
            members = get_group_members(vault, group, passphrase)
            if members:
                click.echo("\n".join(members))
            else:
                click.echo(f"Group '{group}' is empty.")
        else:
            groups = list_groups(vault, passphrase)
            if not groups:
                click.echo("No groups defined.")
            else:
                for g, members in groups.items():
                    click.echo(f"{g}: {', '.join(members)}")
    except KeyError as exc:
        click.echo(str(exc), err=True)
        raise SystemExit(1)


@groups_group.command("delete")
@click.argument("vault")
@click.argument("group")
def delete_cmd(vault: str, group: str) -> None:
    """Delete GROUP from VAULT (keys are preserved)."""
    passphrase = get_passphrase(vault)
    try:
        delete_group(vault, group, passphrase)
        click.echo(f"Deleted group '{group}' from vault '{vault}'.")
    except KeyError as exc:
        click.echo(str(exc), err=True)
        raise SystemExit(1)
