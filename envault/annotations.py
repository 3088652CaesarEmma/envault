"""Key annotations: attach freeform notes/metadata to vault secrets."""

from __future__ import annotations

from typing import Any

from envault.vault import load_vault, save_vault
from envault.audit import record_event


def set_annotation(vault_name: str, key: str, note: str, passphrase: str) -> dict:
    """Attach an annotation (note) to a secret key."""
    vault = load_vault(vault_name, passphrase)
    if key not in vault:
        raise KeyError(f"Key '{key}' not found in vault '{vault_name}'")

    entry = vault[key]
    if isinstance(entry, dict):
        entry["annotation"] = note
    else:
        vault[key] = {"value": entry, "annotation": note}

    save_vault(vault_name, vault, passphrase)
    record_event("annotate", {"vault": vault_name, "key": key})
    return vault[key]


def get_annotation(vault_name: str, key: str, passphrase: str) -> str | None:
    """Return the annotation for a key, or None if not set."""
    vault = load_vault(vault_name, passphrase)
    if key not in vault:
        raise KeyError(f"Key '{key}' not found in vault '{vault_name}'")

    entry = vault[key]
    if isinstance(entry, dict):
        return entry.get("annotation")
    return None


def clear_annotation(vault_name: str, key: str, passphrase: str) -> None:
    """Remove the annotation from a secret key."""
    vault = load_vault(vault_name, passphrase)
    if key not in vault:
        raise KeyError(f"Key '{key}' not found in vault '{vault_name}'")

    entry = vault[key]
    if isinstance(entry, dict) and "annotation" in entry:
        del entry["annotation"]
        save_vault(vault_name, vault, passphrase)
        record_event("clear_annotation", {"vault": vault_name, "key": key})


def list_annotated_keys(vault_name: str, passphrase: str) -> list[dict[str, Any]]:
    """Return all keys that have an annotation."""
    vault = load_vault(vault_name, passphrase)
    results = []
    for key, entry in vault.items():
        if isinstance(entry, dict) and "annotation" in entry:
            results.append({"key": key, "annotation": entry["annotation"]})
    return results
