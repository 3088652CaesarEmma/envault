"""Alert rules for vault secrets — notify when keys are expiring soon or missing."""

from __future__ import annotations

from datetime import datetime, timezone, timedelta
from typing import Any

from envault.vault import load_vault
from envault.audit import record_event


def _parse_expires_at(value: Any) -> datetime | None:
    """Extract expiry datetime from a secret value dict, or None."""
    if not isinstance(value, dict):
        return None
    raw = value.get("expires_at")
    if not raw:
        return None
    try:
        return datetime.fromisoformat(raw)
    except (ValueError, TypeError):
        return None


def check_expiring_soon(
    vault_name: str,
    passphrase: str,
    *,
    warn_days: int = 7,
) -> list[dict]:
    """Return a list of keys expiring within *warn_days* days.

    Each entry is a dict with keys: vault, key, expires_at, days_remaining.
    """
    secrets = load_vault(vault_name, passphrase)
    now = datetime.now(timezone.utc)
    threshold = now + timedelta(days=warn_days)
    results: list[dict] = []

    for key, value in secrets.items():
        exp = _parse_expires_at(value)
        if exp is None:
            continue
        if exp.tzinfo is None:
            exp = exp.replace(tzinfo=timezone.utc)
        if now < exp <= threshold:
            days_remaining = (exp - now).days
            results.append(
                {
                    "vault": vault_name,
                    "key": key,
                    "expires_at": exp.isoformat(),
                    "days_remaining": days_remaining,
                }
            )

    if results:
        record_event(
            "alerts.expiring_soon",
            {"vault": vault_name, "count": len(results), "warn_days": warn_days},
        )

    return results


def check_missing_keys(
    vault_name: str,
    passphrase: str,
    required_keys: list[str],
) -> list[str]:
    """Return keys from *required_keys* that are absent in the vault."""
    secrets = load_vault(vault_name, passphrase)
    missing = [k for k in required_keys if k not in secrets]

    if missing:
        record_event(
            "alerts.missing_keys",
            {"vault": vault_name, "missing": missing},
        )

    return missing
