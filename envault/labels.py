"""Key labeling — attach human-readable display labels to vault keys."""

from __future__ import annotations

from envault.vault import load_vault, save_vault
from envault.audit import record_event


def set_label(vault_name: str, key: str, label: str, passphrase: str) -> None:
    """Attach a display label to *key* in *vault_name*."""
    vault = load_vault(vault_name, passphrase)
    if key not in vault["secrets"]:
        raise KeyError(f"Key '{key}' not found in vault '{vault_name}'.")

    entry = vault["secrets"][key]
    if isinstance(entry, str):
        entry = {"value": entry}
    entry["label"] = label
    vault["secrets"][key] = entry

    save_vault(vault_name, vault, passphrase)
    record_event("label_set", {"vault": vault_name, "key": key, "label": label})


def get_label(vault_name: str, key: str, passphrase: str) -> str | None:
    """Return the display label for *key*, or *None* if unset."""
    vault = load_vault(vault_name, passphrase)
    if key not in vault["secrets"]:
        raise KeyError(f"Key '{key}' not found in vault '{vault_name}'.")

    entry = vault["secrets"][key]
    if isinstance(entry, dict):
        return entry.get("label")
    return None


def clear_label(vault_name: str, key: str, passphrase: str) -> None:
    """Remove the display label from *key*."""
    vault = load_vault(vault_name, passphrase)
    if key not in vault["secrets"]:
        raise KeyError(f"Key '{key}' not found in vault '{vault_name}'.")

    entry = vault["secrets"][key]
    if isinstance(entry, dict):
        entry.pop("label", None)
        vault["secrets"][key] = entry
        save_vault(vault_name, vault, passphrase)
        record_event("label_cleared", {"vault": vault_name, "key": key})


def list_labeled_keys(vault_name: str, passphrase: str) -> dict[str, str]:
    """Return a mapping of key -> label for all labeled keys in *vault_name*."""
    vault = load_vault(vault_name, passphrase)
    result: dict[str, str] = {}
    for key, entry in vault["secrets"].items():
        if isinstance(entry, dict) and "label" in entry:
            result[key] = entry["label"]
    return result
