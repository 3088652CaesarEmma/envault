"""CLI commands for managing webhook notifications."""

import click
from envault.webhooks import (
    register_webhook,
    unregister_webhook,
    list_webhooks,
    fire_webhook,
)


@click.group(name="webhook")
def webhook_group():
    """Manage webhook notifications for vault events."""


@webhook_group.command("add")
@click.argument("name")
@click.argument("url")
def add_webhook(name: str, url: str):
    """Register a new webhook."""
    try:
        result = register_webhook(name, url)
        click.echo(f"Webhook '{result['name']}' registered -> {result['url']}")
    except ValueError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@webhook_group.command("remove")
@click.argument("name")
def remove_webhook(name: str):
    """Unregister a webhook by name."""
    try:
        unregister_webhook(name)
        click.echo(f"Webhook '{name}' removed.")
    except KeyError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@webhook_group.command("list")
def list_webhooks_cmd():
    """List all registered webhooks."""
    hooks = list_webhooks()
    if not hooks:
        click.echo("No webhooks registered.")
        return
    for hook in hooks:
        click.echo(f"  {hook['name']:20s}  {hook['url']}")


@webhook_group.command("fire")
@click.argument("name")
@click.argument("event")
@click.argument("vault")
def fire_cmd(name: str, event: str, vault: str):
    """Manually fire a webhook for testing."""
    try:
        result = fire_webhook(name, event, vault)
        if result["error"]:
            click.echo(f"Webhook failed: {result['error']}", err=True)
            raise SystemExit(1)
        click.echo(f"Webhook fired. HTTP status: {result['status']}")
    except KeyError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)
