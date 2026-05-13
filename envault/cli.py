"""Main CLI entry-point for envault."""

from __future__ import annotations

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
from envault.cli_backup import backup_group
from envault.cli_sharing import share_group
from envault.cli_expiry import expiry_group
from envault.cli_reminders import reminders_group
from envault.cli_readonly import readonly_group
from envault.cli_aliases import alias_group
from envault.cli_versioning import version_group
from envault.cli_favorites import favorites_group
from envault.cli_annotations import annotations_group
from envault.cli_access import access_group
from envault.cli_webhooks import webhook_group
from envault.cli_dependencies import deps_group
from envault.cli_labels import labels_group


@click.group()
def cli() -> None:
    """envault — local secrets manager."""


# env commands
cli.add_command(import_env, "import")
cli.add_command(export_env, "export")
cli.add_command(list_env_keys, "list")

# groups
cli.add_command(passphrase_group, "passphrase")
cli.add_command(vault_group, "vault")
cli.add_command(export_group, "render")
cli.add_command(diff_group, "diff")
cli.add_command(rotate_group, "rotate")
cli.add_command(tags_group, "tags")
cli.add_command(search_group, "search")
cli.add_command(template_group, "template")
cli.add_command(backup_group, "backup")
cli.add_command(share_group, "share")
cli.add_command(expiry_group, "expiry")
cli.add_command(reminders_group, "reminders")
cli.add_command(readonly_group, "readonly")
cli.add_command(alias_group, "alias")
cli.add_command(version_group, "version")
cli.add_command(favorites_group, "favorites")
cli.add_command(annotations_group, "annotations")
cli.add_command(access_group, "access")
cli.add_command(webhook_group, "webhook")
cli.add_command(deps_group, "deps")
cli.add_command(labels_group, "labels")
