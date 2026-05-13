"""CLI commands for environment profile management."""

import click

from envault.environments import (
    set_environment,
    get_environment,
    clear_environment,
    list_by_environment,
    VALID_ENVS,
)
from envault.passphrase import get_passphrase


@click.group("env-profile")
def environments_group():
    """Manage environment profiles for vault keys."""


@environments_group.command("set")
@click.argument("vault_name")
@click.argument("key")
@click.argument("env", type=click.Choice(sorted(VALID_ENVS)))
def set_env_cmd(vault_name, key, env):
    """Tag KEY in VAULT_NAME with an environment profile."""
    passphrase = get_passphrase()
    try:
        set_environment(vault_name, key, env, passphrase)
        click.echo(f"Set environment '{env}' on '{key}' in '{vault_name}'.")
    except (KeyError, ValueError) as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@environments_group.command("get")
@click.argument("vault_name")
@click.argument("key")
def get_env_cmd(vault_name, key):
    """Show the environment profile for KEY."""
    passphrase = get_passphrase()
    try:
        env = get_environment(vault_name, key, passphrase)
        if env:
            click.echo(env)
        else:
            click.echo("(none)")
    except KeyError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@environments_group.command("clear")
@click.argument("vault_name")
@click.argument("key")
def clear_env_cmd(vault_name, key):
    """Remove the environment profile from KEY."""
    passphrase = get_passphrase()
    try:
        clear_environment(vault_name, key, passphrase)
        click.echo(f"Cleared environment tag from '{key}'.")
    except KeyError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@environments_group.command("list")
@click.argument("vault_name")
@click.argument("env", type=click.Choice(sorted(VALID_ENVS)))
def list_env_cmd(vault_name, env):
    """List all keys tagged with ENV in VAULT_NAME."""
    passphrase = get_passphrase()
    try:
        keys = list_by_environment(vault_name, env, passphrase)
        if keys:
            for k in keys:
                click.echo(k)
        else:
            click.echo(f"No keys tagged as '{env}'.")
    except (KeyError, ValueError) as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)
