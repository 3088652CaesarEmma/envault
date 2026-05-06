"""Main CLI entry point for envault."""

import click

from envault.cli_env import import_env, export_env, list_env_keys
from envault.cli_passphrase import passphrase_group
from envault.cli_vault import vault_group
from envault.cli_export import export_group
from envault.cli_diff import diff_group
from envault.cli_rotate import rotate_group
from envault.cli_tags import tags_group
from envault.cli_search import search_group
from envault.cli_templates import template_group
from envault.cli_access import access_group
from envault.cli_sharing import share_group
from envault.cli_expiry import expiry_group
from envault.cli_reminders import reminders_group
from envault.cli_backup import backup_group


@click.group()
@click.version_option("0.1.0", prog_name="envault")
def cli():
    """envault — local secrets manager with encryption and sync."""


cli.add_command(import_env, name="import")
cli.add_command(export_env, name="export")
cli.add_command(list_env_keys, name="list-keys")
cli.add_command(passphrase_group, name="passphrase")
cli.add_command(vault_group, name="vault")
cli.add_command(export_group, name="render")
cli.add_command(diff_group, name="diff")
cli.add_command(rotate_group, name="rotate")
cli.add_command(tags_group, name="tags")
cli.add_command(search_group, name="search")
cli.add_command(template_group, name="template")
cli.add_command(access_group, name="access")
cli.add_command(share_group, name="share")
cli.add_command(expiry_group, name="expiry")
cli.add_command(reminders_group, name="reminders")
cli.add_command(backup_group, name="backup")
