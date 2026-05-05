"""CLI commands for expiration reminders."""

import click

from envault.reminders import get_expiring_keys, format_reminders
from envault.passphrase import get_passphrase


@click.group(name="reminders", help="Remind about keys expiring soon.")
def reminders_group() -> None:  # pragma: no cover
    pass


@reminders_group.command(name="check")
@click.argument("vault_name")
@click.option(
    "--days",
    default=7,
    show_default=True,
    type=int,
    help="Warn about keys expiring within this many days.",
)
@click.option("--quiet", is_flag=True, help="Exit with code 1 if any reminders found.")
def check_reminders(vault_name: str, days: int, quiet: bool) -> None:
    """List keys in VAULT_NAME that will expire within --days days."""
    try:
        passphrase = get_passphrase()
        reminders = get_expiring_keys(vault_name, passphrase, warn_days=days)
        output = format_reminders(reminders)
        click.echo(output)
        if quiet and reminders:
            raise SystemExit(1)
    except FileNotFoundError:
        click.echo(f"Error: vault '{vault_name}' not found.", err=True)
        raise SystemExit(2)
    except Exception as exc:  # noqa: BLE001
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(2)
