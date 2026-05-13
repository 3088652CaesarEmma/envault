"""Visibility control for vault secrets (mask/unmask values in output)."""

from __future__ import annotations

from typing import Any

from envault.vault import load_vault, save_vault
from envault.audit import record_event

_MASKED_PLACEHOLDER = "***"


def mark_masked(vault_name: str, key: str, passphrase: str) -> dict:
    """Mark a secret as masked so its value is hidden in rendered output."""
    vault = load_vault(vault_name, passphrase)
    if key not in vault["secrets"]:
        raise KeyError(f"Key '{key}' not found in vault '{vault_name}'")

    entry = vault["secrets"][key]
    if isinstance(entry, dict):
        entry["masked"] = True
    else:
        vault["secrets"][key] = {"value": entry, "masked": True}

    save_vault(vault_name, vault, passphrase)
    record_event(vault_name, "mark_masked", {"key": key})
    return vault["secrets"][key]


def unmark_masked(vault_name: str, key: str, passphrase: str) -> dict:
    """Remove the masked flag from a secret."""
    vault = load_vault(vault_name, passphrase)
    if key not in vault["secrets"]:
        raise KeyError(f"Key '{key}' not found in vault '{vault_name}'")

    entry = vault["secrets"][key]
    if isinstance(entry, dict):
        entry.pop("masked", None)
        if list(entry.keys()) == ["value"]:
            vault["secrets"][key] = entry["value"]
    # plain string — already not masked, nothing to do

    save_vault(vault_name, vault, passphrase)
    record_event(vault_name, "unmark_masked", {"key": key})
    return vault["secrets"].get(key, {})


def is_masked(entry: Any) -> bool:
    """Return True if the given secret entry has the masked flag set."""
    if isinstance(entry, dict):
        return bool(entry.get("masked", False))
    return False


def list_masked_keys(vault_name: str, passphrase: str) -> list[str]:
    """Return all keys in the vault that are currently masked."""
    vault = load_vault(vault_name, passphrase)
    return [
        key
        for key, entry in vault["secrets"].items()
        if is_masked(entry)
    ]


def apply_visibility(secrets: dict[str, Any], reveal: bool = False) -> dict[str, str]:
    """Render secrets dict, replacing masked values with placeholder unless reveal=True."""
    result: dict[str, str] = {}
    for key, entry in secrets.items():
        if isinstance(entry, dict):
            raw_value = entry.get("value", "")
            if not reveal and entry.get("masked", False):
                result[key] = _MASKED_PLACEHOLDER
            else:
                result[key] = str(raw_value)
        else:
            result[key] = str(entry)
    return result
