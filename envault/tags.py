"""Tag management for vault secrets — assign, remove, and filter by tags."""

from typing import Optional
from envault.vault import load_vault, save_vault
from envault.audit import record_event


def add_tag(vault_name: str, key: str, tag: str, passphrase: str) -> None:
    """Add a tag to a secret key in the vault."""
    vault = load_vault(vault_name, passphrase)
    if key not in vault:
        raise KeyError(f"Key '{key}' not found in vault '{vault_name}'.")

    tags: list = vault[key].get("tags", []) if isinstance(vault[key], dict) else []
    if tag not in tags:
        tags.append(tag)

    if isinstance(vault[key], dict):
        vault[key]["tags"] = tags
    else:
        vault[key] = {"value": vault[key], "tags": tags}

    save_vault(vault_name, vault, passphrase)
    record_event("tag_added", {"vault": vault_name, "key": key, "tag": tag})


def remove_tag(vault_name: str, key: str, tag: str, passphrase: str) -> None:
    """Remove a tag from a secret key in the vault."""
    vault = load_vault(vault_name, passphrase)
    if key not in vault:
        raise KeyError(f"Key '{key}' not found in vault '{vault_name}'.")

    entry = vault[key]
    if not isinstance(entry, dict) or tag not in entry.get("tags", []):
        raise ValueError(f"Tag '{tag}' not found on key '{key}'.")

    entry["tags"].remove(tag)
    save_vault(vault_name, vault, passphrase)
    record_event("tag_removed", {"vault": vault_name, "key": key, "tag": tag})


def list_tags(vault_name: str, key: str, passphrase: str) -> list[str]:
    """Return all tags for a given key."""
    vault = load_vault(vault_name, passphrase)
    if key not in vault:
        raise KeyError(f"Key '{key}' not found in vault '{vault_name}'.")
    entry = vault[key]
    if isinstance(entry, dict):
        return entry.get("tags", [])
    return []


def filter_by_tag(vault_name: str, tag: str, passphrase: str) -> dict[str, str]:
    """Return all key-value pairs in the vault that have the given tag."""
    vault = load_vault(vault_name, passphrase)
    result = {}
    for k, v in vault.items():
        if isinstance(v, dict) and tag in v.get("tags", []):
            result[k] = v.get("value", "")
    return result
