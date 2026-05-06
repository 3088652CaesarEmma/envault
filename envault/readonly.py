"""Read-only mode enforcement for vault keys."""

from __future__ import annotations

from envault.vault import load_vault, save_vault
from envault.audit import record_event


class ReadOnlyViolationError(Exception):
    """Raised when a write is attempted on a read-only key."""


def mark_readonly(vault_name: str, key: str, passphrase: str) -> dict:
    """Mark a key as read-only within a vault."""
    vault = load_vault(vault_name, passphrase)
    if key not in vault:
        raise KeyError(f"Key '{key}' not found in vault '{vault_name}'.")

    entry = vault[key]
    if not isinstance(entry, dict):
        entry = {"value": entry}

    entry["readonly"] = True
    vault[key] = entry
    save_vault(vault_name, vault, passphrase)
    record_event("readonly.mark", {"vault": vault_name, "key": key})
    return entry


def unmark_readonly(vault_name: str, key: str, passphrase: str) -> dict:
    """Remove the read-only flag from a key."""
    vault = load_vault(vault_name, passphrase)
    if key not in vault:
        raise KeyError(f"Key '{key}' not found in vault '{vault_name}'.")

    entry = vault[key]
    if not isinstance(entry, dict):
        return entry  # plain string, nothing to remove

    entry.pop("readonly", None)
    vault[key] = entry
    save_vault(vault_name, vault, passphrase)
    record_event("readonly.unmark", {"vault": vault_name, "key": key})
    return entry


def is_readonly(entry: object) -> bool:
    """Return True if the vault entry is marked read-only."""
    if not isinstance(entry, dict):
        return False
    return bool(entry.get("readonly", False))


def assert_not_readonly(vault_name: str, key: str, entry: object) -> None:
    """Raise ReadOnlyViolationError if the entry is read-only."""
    if is_readonly(entry):
        raise ReadOnlyViolationError(
            f"Key '{key}' in vault '{vault_name}' is read-only and cannot be modified."
        )


def list_readonly_keys(vault_name: str, passphrase: str) -> list[str]:
    """Return all keys in the vault that are marked read-only."""
    vault = load_vault(vault_name, passphrase)
    return [k for k, v in vault.items() if is_readonly(v)]
