"""CLI commands for passphrase management in envault."""

import click
from envault.passphrase import (
    set_session_passphrase,
    clear_session_passphrase,
    prompt_new_passphrase,
    validate_passphrase_strength,
    ENVAULT_PASSPHRASE_ENV_VAR,
)


@click.group("passphrase")
def passphrase_group():
    """Manage the envault master passphrase."""


@passphrase_group.command("set")
@click.option(
    "--warn-weak/--no-warn-weak",
    default=True,
    help="Warn if passphrase is considered weak.",
)
def set_passphrase(warn_weak: bool):
    """Interactively set a new master passphrase for this session."""
    try:
        new_pass = prompt_new_passphrase()
    except (KeyboardInterrupt, EOFError):
        click.echo("\nAborted.", err=True)
        raise SystemExit(1)

    if warn_weak:
        warnings = validate_passphrase_strength(new_pass)
        for w in warnings:
            click.echo(click.style(f"Warning: {w}", fg="yellow"), err=True)

    set_session_passphrase(new_pass)
    click.echo(click.style("Passphrase set for current session.", fg="green"))


@passphrase_group.command("clear")
def clear_passphrase():
    """Clear the cached session passphrase."""
    clear_session_passphrase()
    click.echo("Session passphrase cleared.")


@passphrase_group.command("check")
@click.argument("passphrase", envvar=ENVAULT_PASSPHRASE_ENV_VAR)
def check_passphrase(passphrase: str):
    """Check the strength of a given passphrase."""
    warnings = validate_passphrase_strength(passphrase)
    if not warnings:
        click.echo(click.style("Passphrase looks strong.", fg="green"))
    else:
        for w in warnings:
            click.echo(click.style(f"Warning: {w}", fg="yellow"))
        raise SystemExit(1)
