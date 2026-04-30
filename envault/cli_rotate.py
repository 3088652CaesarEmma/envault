"""CLI commands for passphrase rotation."""

import click
from envault.rotate import rotate_vault_passphrase, rotate_all_vaults
from envault.passphrase import prompt_new_passphrase, validate_passphrase_strength


@click.group("rotate")
def rotate_group():
    """Rotate the master passphrase for one or all vaults."""


@rotate_group.command("vault")
@click.argument("vault_name")
@click.option(
    "--old-passphrase",
    prompt=True,
    hide_input=True,
    help="Current master passphrase.",
)
@click.option(
    "--new-passphrase",
    default=None,
    hide_input=True,
    help="New master passphrase (prompted if omitted).",
)
def rotate_one(vault_name: str, old_passphrase: str, new_passphrase: str):
    """Re-encrypt VAULT_NAME under a new passphrase."""
    if not new_passphrase:
        new_passphrase = prompt_new_passphrase()

    warnings = validate_passphrase_strength(new_passphrase)
    for w in warnings:
        click.echo(click.style(f"Warning: {w}", fg="yellow"))

    try:
        summary = rotate_vault_passphrase(vault_name, old_passphrase, new_passphrase)
    except Exception as exc:
        click.echo(click.style(f"Error: {exc}", fg="red"), err=True)
        raise SystemExit(1)

    count = len(summary["rotated_keys"])
    click.echo(click.style(f"✓ Rotated {count} key(s) in '{vault_name}'.", fg="green"))


@rotate_group.command("all")
@click.option(
    "--old-passphrase",
    prompt=True,
    hide_input=True,
    help="Current master passphrase.",
)
@click.option(
    "--new-passphrase",
    default=None,
    hide_input=True,
    help="New master passphrase (prompted if omitted).",
)
def rotate_all(old_passphrase: str, new_passphrase: str):
    """Re-encrypt ALL vaults under a new passphrase."""
    if not new_passphrase:
        new_passphrase = prompt_new_passphrase()

    warnings = validate_passphrase_strength(new_passphrase)
    for w in warnings:
        click.echo(click.style(f"Warning: {w}", fg="yellow"))

    results = rotate_all_vaults(old_passphrase, new_passphrase)
    ok = [r for r in results if "error" not in r]
    failed = [r for r in results if "error" in r]

    for r in ok:
        click.echo(click.style(f"✓ {r['vault']}: {len(r['rotated_keys'])} key(s) rotated.", fg="green"))
    for r in failed:
        click.echo(click.style(f"✗ {r['vault']}: {r['error']}", fg="red"))

    if failed:
        raise SystemExit(1)
