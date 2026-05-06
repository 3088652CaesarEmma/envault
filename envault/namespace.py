"""Namespace support for grouping vault keys under logical prefixes."""

from __future__ import annotations

from typing import Dict, Any

NAMESPACE_SEP = ":"


def add_to_namespace(vault: Dict[str, Any], key: str, namespace: str) -> Dict[str, Any]:
    """Tag a key as belonging to a namespace."""
    if key not in vault:
        raise KeyError(f"Key '{key}' not found in vault.")
    entry = vault[key]
    if isinstance(entry, str):
        entry = {"value": entry}
    entry["namespace"] = namespace
    vault[key] = entry
    return vault


def remove_from_namespace(vault: Dict[str, Any], key: str) -> Dict[str, Any]:
    """Remove the namespace tag from a key."""
    if key not in vault:
        raise KeyError(f"Key '{key}' not found in vault.")
    entry = vault[key]
    if isinstance(entry, dict):
        entry.pop("namespace", None)
        if list(entry.keys()) == ["value"]:
            vault[key] = entry["value"]
        else:
            vault[key] = entry
    return vault


def get_namespace(vault: Dict[str, Any], key: str) -> str | None:
    """Return the namespace for a key, or None if unset."""
    if key not in vault:
        raise KeyError(f"Key '{key}' not found in vault.")
    entry = vault[key]
    if isinstance(entry, dict):
        return entry.get("namespace")
    return None


def list_by_namespace(vault: Dict[str, Any], namespace: str) -> Dict[str, Any]:
    """Return all keys that belong to the given namespace."""
    result: Dict[str, Any] = {}
    for key, entry in vault.items():
        if isinstance(entry, dict) and entry.get("namespace") == namespace:
            result[key] = entry
    return result


def list_namespaces(vault: Dict[str, Any]) -> list[str]:
    """Return a sorted list of all distinct namespaces used in the vault."""
    namespaces: set[str] = set()
    for entry in vault.values():
        if isinstance(entry, dict):
            ns = entry.get("namespace")
            if ns:
                namespaces.add(ns)
    return sorted(namespaces)
