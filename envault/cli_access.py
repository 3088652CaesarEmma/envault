"""CLI commands for managing per-vault access control profiles."""

from __future__ import annotations

from pathlib import Path

import click

from envault.access_control import (
    check_access,
    grant_access,
    list_access,
    revoke_access,
)

VAULT_DIR = Path.home() / ".envault" / "vaults"


@click.group("access")
def access_group() -> None:
    """Manage per-vault access control profiles."""


@access_group.command("grant")
@click.argument("vault_name")
@click.argument("profile")
@click.argument("permission", type=click.Choice(["read", "write"]))
def grant_cmd(vault_name: str, profile: str, permission: str) -> None:
    """Grant PERMISSION (read|write) on VAULT_NAME to PROFILE."""
    try:
        grant_access(VAULT_DIR, vault_name, profile, permission)
        click.echo(f"Granted '{permission}' on '{vault_name}' to profile '{profile}'.")
    except Exception as exc:  # pragma: no cover
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@access_group.command("revoke")
@click.argument("vault_name")
@click.argument("profile")
@click.argument("permission", type=click.Choice(["read", "write"]))
def revoke_cmd(vault_name: str, profile: str, permission: str) -> None:
    """Revoke PERMISSION from PROFILE on VAULT_NAME."""
    try:
        revoke_access(VAULT_DIR, vault_name, profile, permission)
        click.echo(f"Revoked '{permission}' on '{vault_name}' from profile '{profile}'.")
    except Exception as exc:  # pragma: no cover
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@access_group.command("check")
@click.argument("vault_name")
@click.argument("profile")
@click.argument("permission", type=click.Choice(["read", "write"]))
def check_cmd(vault_name: str, profile: str, permission: str) -> None:
    """Check whether PROFILE has PERMISSION on VAULT_NAME."""
    allowed = check_access(VAULT_DIR, vault_name, profile, permission)
    status = "ALLOWED" if allowed else "DENIED"
    click.echo(f"[{status}] '{profile}' {permission} access on '{vault_name}'")


@access_group.command("list")
@click.argument("vault_name", required=False, default=None)
def list_cmd(vault_name: str | None) -> None:
    """List all access rules, optionally filtered to VAULT_NAME."""
    policy = list_access(VAULT_DIR, vault_name)
    if not policy:
        click.echo("No access rules defined.")
        return
    for key, perms in sorted(policy.items()):
        click.echo(f"  {key}: {', '.join(perms)}")
