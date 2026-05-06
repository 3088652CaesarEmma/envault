"""Dependency tracking between vault keys.

Allows users to declare that one key depends on another,
so that rotation or deletion warnings can surface related keys.
"""

from __future__ import annotations

from typing import Dict, List

from envault.vault import load_vault, save_vault

_DEP_META_KEY = "__dependencies__"


def _get_deps(vault: dict) -> Dict[str, List[str]]:
    """Return the dependency map stored in the vault metadata."""
    return vault.get(_DEP_META_KEY, {})


def add_dependency(vault_name: str, key: str, depends_on: str, passphrase: str) -> None:
    """Record that *key* depends on *depends_on* inside *vault_name*.

    Raises KeyError if either key is not present in the vault.
    """
    vault = load_vault(vault_name, passphrase)
    secrets: dict = vault.get("secrets", {})

    if key not in secrets:
        raise KeyError(f"Key '{key}' not found in vault '{vault_name}'.")
    if depends_on not in secrets:
        raise KeyError(f"Key '{depends_on}' not found in vault '{vault_name}'.")

    deps: Dict[str, List[str]] = _get_deps(vault)
    deps.setdefault(key, [])
    if depends_on not in deps[key]:
        deps[key].append(depends_on)
    vault[_DEP_META_KEY] = deps
    save_vault(vault_name, vault, passphrase)


def remove_dependency(vault_name: str, key: str, depends_on: str, passphrase: str) -> None:
    """Remove a previously recorded dependency.

    Raises KeyError if the dependency does not exist.
    """
    vault = load_vault(vault_name, passphrase)
    deps: Dict[str, List[str]] = _get_deps(vault)

    if key not in deps or depends_on not in deps[key]:
        raise KeyError(
            f"No dependency from '{key}' to '{depends_on}' in vault '{vault_name}'."
        )

    deps[key].remove(depends_on)
    if not deps[key]:
        del deps[key]
    vault[_DEP_META_KEY] = deps
    save_vault(vault_name, vault, passphrase)


def get_dependencies(vault_name: str, key: str, passphrase: str) -> List[str]:
    """Return keys that *key* directly depends on."""
    vault = load_vault(vault_name, passphrase)
    return list(_get_deps(vault).get(key, []))


def get_dependents(vault_name: str, key: str, passphrase: str) -> List[str]:
    """Return keys that directly depend on *key*."""
    vault = load_vault(vault_name, passphrase)
    deps = _get_deps(vault)
    return [k for k, deps_list in deps.items() if key in deps_list]
