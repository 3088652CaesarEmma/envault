import click
from envault.vault import save_vault, load_vault, list_vaults
from envault.passphrase import get_passphrase
from envault.crypto import encrypt, decrypt


@click.group(name="vault")
def vault_group():
    """Manage envault vaults."""
    pass


@vault_group.command(name="create")
@click.argument("vault_name")
def create_vault(vault_name: str):
    """Create a new empty vault with the given name."""
    try:
        passphrase = get_passphrase()
        save_vault(vault_name, {}, passphrase)
        click.echo(f"Vault '{vault_name}' created successfully.")
    except ValueError as e:
        click.echo(f"Error: {e}", err=True)
        raise SystemExit(1)


@vault_group.command(name="list")
def list_vaults_cmd():
    """List all available vaults."""
    vaults = list_vaults()
    if not vaults:
        click.echo("No vaults found.")
    else:
        click.echo("Available vaults:")
        for name in vaults:
            click.echo(f"  - {name}")


@vault_group.command(name="delete")
@click.argument("vault_name")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation prompt.")
def delete_vault(vault_name: str, yes: bool):
    """Delete a vault by name."""
    import os
    from envault.vault import _get_vault_path

    vault_path = _get_vault_path(vault_name)
    if not vault_path.exists():
        click.echo(f"Vault '{vault_name}' does not exist.", err=True)
        raise SystemExit(1)

    if not yes:
        confirmed = click.confirm(
            f"Are you sure you want to delete vault '{vault_name}'?"
        )
        if not confirmed:
            click.echo("Aborted.")
            return

    os.remove(vault_path)
    click.echo(f"Vault '{vault_name}' deleted.")


@vault_group.command(name="info")
@click.argument("vault_name")
def vault_info(vault_name: str):
    """Show metadata about a vault."""
    try:
        passphrase = get_passphrase()
        data = load_vault(vault_name, passphrase)
        key_count = len(data)
        click.echo(f"Vault: {vault_name}")
        click.echo(f"Keys stored: {key_count}")
    except FileNotFoundError:
        click.echo(f"Vault '{vault_name}' not found.", err=True)
        raise SystemExit(1)
    except Exception as e:
        click.echo(f"Failed to load vault: {e}", err=True)
        raise SystemExit(1)
