"""Secret expiry management for envault vaults."""

from __future__ import annotations

import time
from typing import Any

from envault.vault import load_vault, save_vault
from envault.audit import record_event


def set_expiry(vault_name: str, key: str, ttl_seconds: int, passphrase: str) -> dict:
    """Set an expiry TTL (in seconds from now) on a vault key."""
    vault = load_vault(vault_name, passphrase)
    if key not in vault:
        raise KeyError(f"Key '{key}' not found in vault '{vault_name}'")

    entry = vault[key]
    if not isinstance(entry, dict):
        entry = {"value": entry}

    expires_at = int(time.time()) + ttl_seconds
    entry["expires_at"] = expires_at
    vault[key] = entry

    save_vault(vault_name, vault, passphrase)
    record_event("set_expiry", {"vault": vault_name, "key": key, "expires_at": expires_at})
    return {"key": key, "expires_at": expires_at, "ttl_seconds": ttl_seconds}


def clear_expiry(vault_name: str, key: str, passphrase: str) -> None:
    """Remove expiry from a vault key."""
    vault = load_vault(vault_name, passphrase)
    if key not in vault:
        raise KeyError(f"Key '{key}' not found in vault '{vault_name}'")

    entry = vault[key]
    if isinstance(entry, dict) and "expires_at" in entry:
        del entry["expires_at"]
        vault[key] = entry
        save_vault(vault_name, vault, passphrase)
    record_event("clear_expiry", {"vault": vault_name, "key": key})


def is_expired(entry: Any) -> bool:
    """Return True if the entry has an expiry timestamp that has passed."""
    if not isinstance(entry, dict):
        return False
    expires_at = entry.get("expires_at")
    if expires_at is None:
        return False
    return int(time.time()) >= expires_at


def list_expired_keys(vault_name: str, passphrase: str) -> list[str]:
    """Return a list of keys in the vault that have expired."""
    vault = load_vault(vault_name, passphrase)
    return [k for k, v in vault.items() if is_expired(v)]


def purge_expired_keys(vault_name: str, passphrase: str) -> list[str]:
    """Delete all expired keys from the vault. Returns list of purged keys."""
    vault = load_vault(vault_name, passphrase)
    expired = [k for k, v in vault.items() if is_expired(v)]
    for key in expired:
        del vault[key]
    if expired:
        save_vault(vault_name, vault, passphrase)
        record_event("purge_expired", {"vault": vault_name, "keys": expired})
    return expired
