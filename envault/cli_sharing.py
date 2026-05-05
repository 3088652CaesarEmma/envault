"""CLI commands for vault share export / import."""

from __future__ import annotations

import json
import sys

import click

from envault.passphrase import get_passphrase, prompt_new_passphrase
from envault.sharing import export_share, import_share


@click.group("share")
def share_group() -> None:
    """Export and import encrypted vault share bundles."""


@share_group.command("export")
@click.argument("vault_name")
@click.option("--out", "-o", default=None, help="Write bundle to this file (default: stdout).")
def export_cmd(vault_name: str, out: str | None) -> None:
    """Export VAULT_NAME as an encrypted share bundle."""
    passphrase = get_passphrase()
    share_passphrase = prompt_new_passphrase(prompt="Share passphrase")

    try:
        bundle = export_share(vault_name, passphrase, share_passphrase)
    except Exception as exc:  # noqa: BLE001
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)

    bundle_json = json.dumps(bundle, indent=2)
    if out:
        with open(out, "w") as fh:
            fh.write(bundle_json)
        click.echo(f"Share bundle written to {out}")
    else:
        click.echo(bundle_json)


@share_group.command("import")
@click.argument("bundle_file")
@click.argument("target_vault")
@click.option("--merge", is_flag=True, default=False, help="Merge into existing vault instead of replacing.")
def import_cmd(bundle_file: str, target_vault: str, merge: bool) -> None:
    """Import a share bundle into TARGET_VAULT."""
    try:
        with open(bundle_file) as fh:
            bundle = json.load(fh)
    except (OSError, json.JSONDecodeError) as exc:
        click.echo(f"Failed to read bundle: {exc}", err=True)
        sys.exit(1)

    share_passphrase = click.prompt("Share passphrase", hide_input=True)
    target_passphrase = get_passphrase()

    try:
        final = import_share(bundle, share_passphrase, target_vault, target_passphrase, merge=merge)
    except Exception as exc:  # noqa: BLE001
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)

    action = "merged into" if merge else "imported into"
    click.echo(f"Bundle {action} vault '{target_vault}' ({len(final)} keys).")
