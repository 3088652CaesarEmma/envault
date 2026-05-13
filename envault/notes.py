"""Per-key notes: attach, retrieve, clear, and list freeform text notes on secrets."""

from __future__ import annotations

from envault.vault import load_vault, save_vault
from envault.audit import record_event


def set_note(vault_name: str, key: str, note: str, passphrase: str) -> None:
    """Attach a freeform text note to *key* in *vault_name*."""
    vault = load_vault(vault_name, passphrase)
    if key not in vault:
        raise KeyError(f"Key '{key}' not found in vault '{vault_name}'.")

    entry = vault[key]
    if isinstance(entry, dict):
        entry["note"] = note
    else:
        vault[key] = {"value": entry, "note": note}

    save_vault(vault_name, vault, passphrase)
    record_event("note_set", {"vault": vault_name, "key": key})


def get_note(vault_name: str, key: str, passphrase: str) -> str | None:
    """Return the note attached to *key*, or *None* if absent."""
    vault = load_vault(vault_name, passphrase)
    if key not in vault:
        raise KeyError(f"Key '{key}' not found in vault '{vault_name}'.")

    entry = vault[key]
    if isinstance(entry, dict):
        return entry.get("note")
    return None


def clear_note(vault_name: str, key: str, passphrase: str) -> None:
    """Remove the note from *key* if one exists."""
    vault = load_vault(vault_name, passphrase)
    if key not in vault:
        raise KeyError(f"Key '{key}' not found in vault '{vault_name}'.")

    entry = vault[key]
    if isinstance(entry, dict) and "note" in entry:
        del entry["note"]
        save_vault(vault_name, vault, passphrase)
        record_event("note_cleared", {"vault": vault_name, "key": key})


def list_noted_keys(vault_name: str, passphrase: str) -> list[dict]:
    """Return a list of dicts with *key* and *note* for every key that has a note."""
    vault = load_vault(vault_name, passphrase)
    results = []
    for key, entry in vault.items():
        if isinstance(entry, dict) and entry.get("note"):
            results.append({"key": key, "note": entry["note"]})
    return results
