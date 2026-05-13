"""Root CLI entry-point for envault."""
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
from envault.cli_annotations import annotations_group
from envault.cli_backup import backup_group
from envault.cli_versioning import version_group
from envault.cli_favorites import favorites_group
from envault.cli_labels import labels_group
from envault.cli_scoring import scoring_group
from envault.cli_watchers import watchers_group
from envault.cli_groups import groups_group
from envault.cli_dependencies import deps_group
from envault.cli_webhooks import webhook_group
from envault.cli_readonly import readonly_group
from envault.cli_aliases import alias_group
from envault.cli_environments import environments_group
from envault.cli_mentions import mentions_group
from envault.cli_visibility import readonly_group as visibility_group  # noqa: F401 alias
from envault.cli_workflows import workflow_group


@click.group()
@click.version_option(prog_name="envault")
def cli() -> None:
    """envault — local encrypted secrets manager."""


# env operations
cli.add_command(import_env, name="import")
cli.add_command(export_env, name="export")
cli.add_command(list_env_keys, name="keys")

# groups
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
cli.add_command(annotations_group, name="annotate")
cli.add_command(backup_group, name="backup")
cli.add_command(version_group, name="version")
cli.add_command(favorites_group, name="favorites")
cli.add_command(labels_group, name="labels")
cli.add_command(scoring_group, name="score")
cli.add_command(watchers_group, name="watch")
cli.add_command(groups_group, name="groups")
cli.add_command(deps_group, name="deps")
cli.add_command(webhook_group, name="webhook")
cli.add_command(readonly_group, name="readonly")
cli.add_command(alias_group, name="alias")
cli.add_command(environments_group, name="env")
cli.add_command(mentions_group, name="mentions")
cli.add_command(workflow_group, name="workflow")
