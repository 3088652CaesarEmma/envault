import click
from envault.cli_passphrase import passphrase_group
from envault.cli_vault import vault_group
from envault.cli_env import import_env, export_env, list_env_keys


@click.group()
@click.version_option(version="0.1.0", prog_name="envault")
def cli():
    """envault — A local secrets manager that encrypts and syncs .env files."""
    pass


cli.add_command(passphrase_group)
cli.add_command(vault_group)
cli.add_command(import_env, name="import")
cli.add_command(export_env, name="export")
cli.add_command(list_env_keys, name="list-keys")


if __name__ == "__main__":
    cli()
