"""CLI commands for managing key dependencies within a vault."""

import click

from envault.dependencies import (
    add_dependency,
    get_dependencies,
    get_dependents,
    remove_dependency,
)
from envault.passphrase import get_passphrase


@click.group(name="deps")
def deps_group() -> None:
    """Manage key dependency relationships."""


@deps_group.command("add")
@click.argument("vault_name")
@click.argument("key")
@click.argument("depends_on")
def add_dep_cmd(vault_name: str, key: str, depends_on: str) -> None:
    """Record that KEY depends on DEPENDS_ON inside VAULT_NAME."""
    try:
        passphrase = get_passphrase()
        add_dependency(vault_name, key, depends_on, passphrase)
        click.echo(f"Dependency added: '{key}' depends on '{depends_on}'.")
    except KeyError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@deps_group.command("remove")
@click.argument("vault_name")
@click.argument("key")
@click.argument("depends_on")
def remove_dep_cmd(vault_name: str, key: str, depends_on: str) -> None:
    """Remove a dependency between KEY and DEPENDS_ON."""
    try:
        passphrase = get_passphrase()
        remove_dependency(vault_name, key, depends_on, passphrase)
        click.echo(f"Dependency removed: '{key}' no longer depends on '{depends_on}'.")
    except KeyError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@deps_group.command("list")
@click.argument("vault_name")
@click.argument("key")
def list_deps_cmd(vault_name: str, key: str) -> None:
    """List all keys that KEY depends on."""
    passphrase = get_passphrase()
    deps = get_dependencies(vault_name, key, passphrase)
    if deps:
        click.echo(f"'{key}' depends on:")
        for dep in deps:
            click.echo(f"  - {dep}")
    else:
        click.echo(f"'{key}' has no recorded dependencies.")


@deps_group.command("dependents")
@click.argument("vault_name")
@click.argument("key")
def list_dependents_cmd(vault_name: str, key: str) -> None:
    """List all keys that depend on KEY."""
    passphrase = get_passphrase()
    dependents = get_dependents(vault_name, key, passphrase)
    if dependents:
        click.echo(f"Keys that depend on '{key}':")
        for dep in dependents:
            click.echo(f"  - {dep}")
    else:
        click.echo(f"No keys depend on '{key}'.")
