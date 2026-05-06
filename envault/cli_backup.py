"""CLI commands for backup and restore of vault data."""

import click
from envault.backup import create_backup, restore_backup, list_backups, delete_backup
from envault.passphrase import get_passphrase


@click.group("backup")
def backup_group():
    """Backup and restore encrypted vault archives."""


@backup_group.command("create")
@click.argument("vaults", nargs=-1, required=True)
@click.option("--label", default=None, help="Custom label for the backup.")
def create_cmd(vaults, label):
    """Create an encrypted backup of one or more vaults."""
    try:
        passphrase = get_passphrase()
        result = create_backup(list(vaults), passphrase, label=label)
        click.echo(f"Backup created: {result['label']} ({result['path']})")
        click.echo(f"  Vaults: {', '.join(result['vaults'])}")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise SystemExit(1)


@backup_group.command("restore")
@click.argument("label")
@click.option("--overwrite", is_flag=True, default=False, help="Overwrite existing vaults.")
def restore_cmd(label, overwrite):
    """Restore vaults from an encrypted backup."""
    try:
        passphrase = get_passphrase()
        result = restore_backup(label, passphrase, overwrite=overwrite)
        if result["restored"]:
            click.echo(f"Restored: {', '.join(result['restored'])}")
        if result["skipped"]:
            click.echo(f"Skipped (already exist): {', '.join(result['skipped'])}")
            click.echo("Use --overwrite to replace existing vaults.")
    except FileNotFoundError as e:
        click.echo(f"Error: {e}", err=True)
        raise SystemExit(1)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise SystemExit(1)


@backup_group.command("list")
def list_cmd():
    """List all available backups."""
    backups = list_backups()
    if not backups:
        click.echo("No backups found.")
        return
    for b in backups:
        click.echo(f"{b['label']}  created={b['created_at']}  vaults={', '.join(b['vaults'])}")


@backup_group.command("delete")
@click.argument("label")
@click.confirmation_option(prompt="Are you sure you want to delete this backup?")
def delete_cmd(label):
    """Delete a backup archive."""
    try:
        delete_backup(label)
        click.echo(f"Backup '{label}' deleted.")
    except FileNotFoundError as e:
        click.echo(f"Error: {e}", err=True)
        raise SystemExit(1)
