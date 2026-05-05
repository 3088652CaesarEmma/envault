"""Reminders: notify users about upcoming key expirations and stale secrets."""

from __future__ import annotations

from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any

from envault.vault import load_vault
from envault.audit import record_event


DEFAULT_WARN_DAYS = 7


def _parse_expires_at(value: Any) -> datetime | None:
    """Return a timezone-aware datetime from an ISO string, or None."""
    if not isinstance(value, dict):
        return None
    raw = value.get("expires_at")
    if not raw:
        return None
    try:
        dt = datetime.fromisoformat(raw)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except ValueError:
        return None


def get_expiring_keys(
    vault_name: str,
    passphrase: str,
    warn_days: int = DEFAULT_WARN_DAYS,
) -> List[Dict[str, Any]]:
    """Return a list of reminder dicts for keys expiring within *warn_days*."""
    vault = load_vault(vault_name, passphrase)
    secrets: dict = vault.get("secrets", {})
    now = datetime.now(tz=timezone.utc)
    cutoff = now + timedelta(days=warn_days)

    results = []
    for key, value in secrets.items():
        expires_at = _parse_expires_at(value)
        if expires_at is None:
            continue
        if now < expires_at <= cutoff:
            days_left = (expires_at - now).days
            results.append(
                {
                    "key": key,
                    "vault": vault_name,
                    "expires_at": expires_at.isoformat(),
                    "days_left": days_left,
                }
            )

    if results:
        record_event(
            "reminders_checked",
            {"vault": vault_name, "expiring_count": len(results), "warn_days": warn_days},
        )

    return sorted(results, key=lambda r: r["days_left"])


def format_reminders(reminders: List[Dict[str, Any]]) -> str:
    """Return a human-readable summary of expiring keys."""
    if not reminders:
        return "No keys expiring soon."
    lines = ["Keys expiring soon:"]
    for r in reminders:
        lines.append(
            f"  [{r['vault']}] {r['key']} — expires in {r['days_left']} day(s) ({r['expires_at']})"
        )
    return "\n".join(lines)
