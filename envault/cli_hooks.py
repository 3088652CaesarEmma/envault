"""CLI commands for managing envault operation hooks."""

import click
from envault.hooks import list_hooks, clear_hooks, _registry

HOOK_PHASES = ["pre", "post"]
HOOK_EVENTS = ["save", "load", "delete", "rotate", "export"]


@click.group("hooks")
def hooks_group() -> None:
    """Manage pre/post operation hooks."""


@hooks_group.command("list")
@click.option("--phase", type=click.Choice(HOOK_PHASES), default=None, help="Filter by phase.")
@click.option("--event", type=click.Choice(HOOK_EVENTS), default=None, help="Filter by event.")
def list_hooks_cmd(phase: str | None, event: str | None) -> None:
    """List all registered hooks."""
    phases = [phase] if phase else HOOK_PHASES
    events = [event] if event else HOOK_EVENTS

    found = False
    for p in phases:
        for e in events:
            hooks = list_hooks(p, e)  # type: ignore[arg-type]
            for fn in hooks:
                click.echo(f"{p}:{e}  {fn.__module__}.{fn.__qualname__}")
                found = True

    if not found:
        click.echo("No hooks registered.")


@hooks_group.command("clear")
@click.option("--phase", type=click.Choice(HOOK_PHASES), default=None)
@click.option("--event", type=click.Choice(HOOK_EVENTS), default=None)
@click.confirmation_option(prompt="Clear hooks — are you sure?")
def clear_hooks_cmd(phase: str | None, event: str | None) -> None:
    """Clear registered hooks."""
    if phase and event:
        clear_hooks(phase, event)  # type: ignore[arg-type]
        click.echo(f"Cleared hooks for {phase}:{event}.")
    else:
        clear_hooks()
        click.echo("All hooks cleared.")


@hooks_group.command("summary")
def summary_cmd() -> None:
    """Print a summary count of registered hooks per slot."""
    if not _registry:
        click.echo("No hooks registered.")
        return
    for slot, fns in sorted(_registry.items()):
        click.echo(f"{slot}: {len(fns)} hook(s)")
