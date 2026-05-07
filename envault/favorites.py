"""Favorites module — mark vault keys as favorites for quick access."""

from __future__ import annotations

from typing import Dict, List

from envault.vault import load_vault, save_vault
from envault.audit import record_event


def mark_favorite(vault_name: str, key: str, passphrase: str) -> None:
    """Mark a key as a favorite in the given vault."""
    vault = load_vault(vault_name, passphrase)
    if key not in vault:
        raise KeyError(f"Key '{key}' not found in vault '{vault_name}'.")

    entry = vault[key]
    if isinstance(entry, dict):
        entry["favorite"] = True
    else:
        vault[key] = {"value": entry, "favorite": True}

    save_vault(vault_name, vault, passphrase)
    record_event("favorite_marked", {"vault": vault_name, "key": key})


def unmark_favorite(vault_name: str, key: str, passphrase: str) -> None:
    """Remove the favorite flag from a key."""
    vault = load_vault(vault_name, passphrase)
    if key not in vault:
        raise KeyError(f"Key '{key}' not found in vault '{vault_name}'.")

    entry = vault[key]
    if isinstance(entry, dict):
        entry.pop("favorite", None)
    # If it's a plain string, there's nothing to unmark.

    save_vault(vault_name, vault, passphrase)
    record_event("favorite_unmarked", {"vault": vault_name, "key": key})


def is_favorite(entry: object) -> bool:
    """Return True if the vault entry is marked as a favorite."""
    if isinstance(entry, dict):
        return bool(entry.get("favorite", False))
    return False


def list_favorites(vault_name: str, passphrase: str) -> List[str]:
    """Return a list of keys that are marked as favorites."""
    vault = load_vault(vault_name, passphrase)
    return [k for k, v in vault.items() if is_favorite(v)]
