"""Pinned keys — mark vault secrets as pinned to prevent accidental deletion or overwrite."""

from __future__ import annotations

from typing import Any

from envault.vault import load_vault, save_vault
from envault.audit import record_event


def pin_key(vault_name: str, key: str, passphrase: str) -> None:
    """Mark a key as pinned in the given vault."""
    vault = load_vault(vault_name, passphrase)
    if key not in vault:
        raise KeyError(f"Key '{key}' not found in vault '{vault_name}'.")

    entry = vault[key]
    if isinstance(entry, dict):
        entry["pinned"] = True
    else:
        vault[key] = {"value": entry, "pinned": True}

    save_vault(vault_name, vault, passphrase)
    record_event("pin_key", {"vault": vault_name, "key": key})


def unpin_key(vault_name: str, key: str, passphrase: str) -> None:
    """Remove the pinned flag from a key."""
    vault = load_vault(vault_name, passphrase)
    if key not in vault:
        raise KeyError(f"Key '{key}' not found in vault '{vault_name}'.")

    entry = vault[key]
    if isinstance(entry, dict):
        entry.pop("pinned", None)
    # If it's a plain string, nothing to unpin — silently succeed

    save_vault(vault_name, vault, passphrase)
    record_event("unpin_key", {"vault": vault_name, "key": key})


def is_pinned(entry: Any) -> bool:
    """Return True if the vault entry has the pinned flag set."""
    if isinstance(entry, dict):
        return bool(entry.get("pinned", False))
    return False


def list_pinned_keys(vault_name: str, passphrase: str) -> list[str]:
    """Return a list of all pinned key names in the vault."""
    vault = load_vault(vault_name, passphrase)
    return [k for k, v in vault.items() if is_pinned(v)]


def assert_not_pinned(vault: dict, key: str, operation: str = "modify") -> None:
    """Raise ValueError if the key is pinned, preventing the operation."""
    if key in vault and is_pinned(vault[key]):
        raise ValueError(
            f"Key '{key}' is pinned and cannot be {operation}d. "
            "Unpin it first with 'envault pinned unpin'."
        )
