"""Category management for vault secrets."""

from __future__ import annotations

from typing import Any

from envault.audit import record_event
from envault.vault import load_vault, save_vault


def _to_dict(value: Any) -> dict:
    """Ensure a vault entry is represented as a dict."""
    if isinstance(value, dict):
        return value
    return {"value": value}


def set_category(vault_name: str, key: str, category: str, passphrase: str) -> None:
    """Assign a category to a secret key."""
    vault = load_vault(vault_name, passphrase)
    if key not in vault:
        raise KeyError(f"Key '{key}' not found in vault '{vault_name}'.")
    entry = _to_dict(vault[key])
    entry["category"] = category
    vault[key] = entry
    save_vault(vault_name, vault, passphrase)
    record_event("set_category", {"vault": vault_name, "key": key, "category": category})


def get_category(vault_name: str, key: str, passphrase: str) -> str | None:
    """Return the category assigned to a key, or None."""
    vault = load_vault(vault_name, passphrase)
    if key not in vault:
        raise KeyError(f"Key '{key}' not found in vault '{vault_name}'.")
    entry = vault[key]
    if isinstance(entry, dict):
        return entry.get("category")
    return None


def clear_category(vault_name: str, key: str, passphrase: str) -> None:
    """Remove the category from a secret key."""
    vault = load_vault(vault_name, passphrase)
    if key not in vault:
        raise KeyError(f"Key '{key}' not found in vault '{vault_name}'.")
    entry = _to_dict(vault[key])
    entry.pop("category", None)
    vault[key] = entry
    save_vault(vault_name, vault, passphrase)
    record_event("clear_category", {"vault": vault_name, "key": key})


def list_by_category(vault_name: str, category: str, passphrase: str) -> list[str]:
    """Return all keys in the vault that belong to the given category."""
    vault = load_vault(vault_name, passphrase)
    results = []
    for key, value in vault.items():
        if isinstance(value, dict) and value.get("category") == category:
            results.append(key)
    return sorted(results)


def list_categories(vault_name: str, passphrase: str) -> list[str]:
    """Return a sorted list of all distinct categories used in the vault."""
    vault = load_vault(vault_name, passphrase)
    seen: set[str] = set()
    for value in vault.values():
        if isinstance(value, dict) and "category" in value:
            seen.add(value["category"])
    return sorted(seen)
