"""Key-level versioning: track value history per secret key within a vault."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from envault.vault import load_vault, save_vault
from envault.audit import record_event

_MAX_VERSIONS = 20


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def push_version(vault_name: str, key: str, passphrase: str) -> dict:
    """Snapshot the current value of *key* into its version history."""
    vault = load_vault(vault_name, passphrase)
    if key not in vault:
        raise KeyError(f"Key '{key}' not found in vault '{vault_name}'")

    raw = vault[key]
    value = raw["value"] if isinstance(raw, dict) else raw

    if not isinstance(raw, dict):
        vault[key] = {"value": raw, "versions": []}

    versions: list = vault[key].setdefault("versions", [])
    entry = {"value": value, "timestamp": _now_iso()}
    versions.append(entry)

    # Trim to max
    if len(versions) > _MAX_VERSIONS:
        vault[key]["versions"] = versions[-_MAX_VERSIONS:]

    save_vault(vault_name, vault, passphrase)
    record_event("version_pushed", {"vault": vault_name, "key": key})
    return entry


def list_versions(vault_name: str, key: str, passphrase: str) -> list[dict]:
    """Return the version history list for *key* (oldest first)."""
    vault = load_vault(vault_name, passphrase)
    if key not in vault:
        raise KeyError(f"Key '{key}' not found in vault '{vault_name}'")
    raw = vault[key]
    if not isinstance(raw, dict):
        return []
    return list(raw.get("versions", []))


def restore_version(vault_name: str, key: str, index: int, passphrase: str) -> Any:
    """Restore *key* to a previous version by *index* (0 = oldest)."""
    vault = load_vault(vault_name, passphrase)
    if key not in vault:
        raise KeyError(f"Key '{key}' not found in vault '{vault_name}'")

    raw = vault[key]
    if not isinstance(raw, dict) or not raw.get("versions"):
        raise ValueError(f"No version history for key '{key}'")

    versions = raw["versions"]
    if index < 0 or index >= len(versions):
        raise IndexError(f"Version index {index} out of range (0-{len(versions) - 1})")

    restored_value = versions[index]["value"]
    vault[key]["value"] = restored_value
    save_vault(vault_name, vault, passphrase)
    record_event("version_restored", {"vault": vault_name, "key": key, "index": index})
    return restored_value


def clear_versions(vault_name: str, key: str, passphrase: str) -> int:
    """Delete all version history for *key*. Returns number of entries removed."""
    vault = load_vault(vault_name, passphrase)
    if key not in vault:
        raise KeyError(f"Key '{key}' not found in vault '{vault_name}'")
    raw = vault[key]
    if not isinstance(raw, dict):
        return 0
    count = len(raw.get("versions", []))
    vault[key]["versions"] = []
    save_vault(vault_name, vault, passphrase)
    record_event("versions_cleared", {"vault": vault_name, "key": key})
    return count
