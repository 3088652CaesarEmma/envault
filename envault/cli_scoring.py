"""CLI commands for secret strength scoring."""

from __future__ import annotations

import click

from envault.passphrase import get_passphrase
from envault.vault import load_vault
from envault.scoring import score_vault, vault_health
from envault.export_formats import render_secrets


@click.group("score")
def scoring_group() -> None:
    """Analyse the strength of secrets stored in a vault."""


@scoring_group.command("key")
@click.argument("vault_name")
@click.argument("key")
def score_key_cmd(vault_name: str, key: str) -> None:
    """Show the strength score for a single KEY in VAULT_NAME."""
    passphrase = get_passphrase()
    try:
        vault = load_vault(vault_name, passphrase)
    except Exception as exc:
        click.echo(f"Error loading vault: {exc}", err=True)
        raise SystemExit(1)

    secrets = render_secrets(vault)
    if key not in secrets:
        click.echo(f"Key '{key}' not found in vault '{vault_name}'.", err=True)
        raise SystemExit(1)

    from envault.scoring import score_secret
    result = score_secret(key, secrets[key])
    click.echo(f"Key   : {result.key}")
    click.echo(f"Score : {result.score}/100  [{result.grade}]")
    if result.issues:
        click.echo("Issues:")
        for issue in result.issues:
            click.echo(f"  - {issue}")
    else:
        click.echo("Issues: none")


@scoring_group.command("vault")
@click.argument("vault_name")
@click.option("--show-all", is_flag=True, default=False,
              help="Print a score line for every key.")
def score_vault_cmd(vault_name: str, show_all: bool) -> None:
    """Show a health summary (and optionally per-key scores) for VAULT_NAME."""
    passphrase = get_passphrase()
    try:
        vault = load_vault(vault_name, passphrase)
    except Exception as exc:
        click.echo(f"Error loading vault: {exc}", err=True)
        raise SystemExit(1)

    secrets = render_secrets(vault)
    scores = score_vault(secrets)
    health = vault_health(scores)

    click.echo(f"Vault          : {vault_name}")
    click.echo(f"Total keys     : {health['total_keys']}")
    click.echo(f"Average score  : {health['average_score']}/100  [{health['grade']}]")

    if health["weak_keys"]:
        click.echo("Weak keys (D/F): " + ", ".join(health["weak_keys"]))
    else:
        click.echo("Weak keys (D/F): none")

    if show_all:
        click.echo("\nPer-key scores:")
        for k, s in sorted(scores.items()):
            issues_str = "; ".join(s.issues) if s.issues else "ok"
            click.echo(f"  {k:<30} {s.score:>3}/100  [{s.grade}]  {issues_str}")
