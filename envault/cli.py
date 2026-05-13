"""Main CLI entry-point for envault."""

import click

from envault.cli_access import access_group
from envault.cli_aliases import alias_group
from envault.cli_annotations import annotations_group
from envault.cli_backup import backup_group
from envault.cli_dependencies import deps_group
from envault.cli_diff import diff_group
from envault.cli_env import export_env, import_env, list_env_keys
from envault.cli_expiry import expiry_group
from envault.cli_export import export_group
from envault.cli_favorites import favorites_group
from envault.cli_groups import groups_group
from envault.cli_labels import labels_group
from envault.cli_namespace import namespace_group  # type: ignore[import]
from envault.cli_passphrase import passphrase_group
from envault.cli_readonly import readonly_group
from envault.cli_reminders import reminders_group
from envault.cli_rotate import rotate_group
from envault.cli_scoring import scoring_group
from envault.cli_sharing import share_group
from envault.cli_tags import tags_group
from envault.cli_templates import template_group
from envault.cli_vault import vault_group
from envault.cli_versioning import version_group
from envault.cli_watchers import watchers_group
from envault.cli_webhooks import webhook_group


@click.group()
@click.version_option()
def cli() -> None:
    """envault — local secrets manager."""


# Core
cli.add_command(vault_group)
cli.add_command(passphrase_group)
cli.add_command(import_env)
cli.add_command(export_env)
cli.add_command(list_env_keys)
cli.add_command(export_group)
cli.add_command(diff_group)
cli.add_command(rotate_group)
cli.add_command(share_group)

# Metadata / organisation
cli.add_command(tags_group)
cli.add_command(annotations_group)
cli.add_command(labels_group)
cli.add_command(favorites_group)
cli.add_command(groups_group)
cli.add_command(namespace_group)
cli.add_command(alias_group)

# Lifecycle
cli.add_command(expiry_group)
cli.add_command(version_group)
cli.add_command(readonly_group)
cli.add_command(deps_group)
cli.add_command(template_group)
cli.add_command(scoring_group)

# Infrastructure
cli.add_command(backup_group)
cli.add_command(access_group)
cli.add_command(watchers_group)
cli.add_command(webhook_group)
cli.add_command(reminders_group)
