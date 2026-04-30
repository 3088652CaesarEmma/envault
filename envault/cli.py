"""Main CLI entry point for envault."""

import click
from envault.cli_env import import_env, export_env, list_env_keys
from envault.cli_passphrase import passphrase_group
from envault.cli_vault import vault_group
from envault.cli_export import export_group
from envault.cli_diff import diff_group
from envault.cli_rotate import rotate_group
from envault.cli_tags import tags_group


@click.group()
def cli():
    """envault — local secrets manager for .env files."""


cli.add_command(import_env, name="import")
cli.add_command(export_env, name="export")
cli.add_command(list_env_keys, name="list")
cli.add_command(passphrase_group)
cli.add_command(vault_group)
cli.add_command(export_group)
cli.add_command(diff_group)
cli.add_command(rotate_group)
cli.add_command(tags_group)
