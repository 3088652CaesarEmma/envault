"""Secret grouping: organize vault keys into named groups."""

from __future__ import annotations

from typing import Dict, List

from envault.audit import record_event
from envault.vault import load_vault, save_vault

_GROUPS_KEY = "__groups__"


def _get_groups(vault: dict) -> Dict[str, List[str]]:
    meta = vault.get(_GROUPS_KEY, {})
    if not isinstance(meta, dict):
        return {}
    return meta


def _set_groups(vault: dict, groups: Dict[str, List[str]]) -> None:
    vault[_GROUPS_KEY] = groups


def add_to_group(vault_name: str, group: str, key: str, passphrase: str) -> None:
    """Add *key* to *group* in the named vault."""
    vault = load_vault(vault_name, passphrase)
    if key not in vault:
        raise KeyError(f"Key '{key}' not found in vault '{vault_name}'.")
    groups = _get_groups(vault)
    members = groups.setdefault(group, [])
    if key not in members:
        members.append(key)
    _set_groups(vault, groups)
    save_vault(vault_name, vault, passphrase)
    record_event("group_add", {"vault": vault_name, "group": group, "key": key})


def remove_from_group(vault_name: str, group: str, key: str, passphrase: str) -> None:
    """Remove *key* from *group*."""
    vault = load_vault(vault_name, passphrase)
    groups = _get_groups(vault)
    if group not in groups or key not in groups[group]:
        raise KeyError(f"Key '{key}' is not in group '{group}'.")
    groups[group].remove(key)
    if not groups[group]:
        del groups[group]
    _set_groups(vault, groups)
    save_vault(vault_name, vault, passphrase)
    record_event("group_remove", {"vault": vault_name, "group": group, "key": key})


def list_groups(vault_name: str, passphrase: str) -> Dict[str, List[str]]:
    """Return all groups and their members for the named vault."""
    vault = load_vault(vault_name, passphrase)
    return dict(_get_groups(vault))


def get_group_members(vault_name: str, group: str, passphrase: str) -> List[str]:
    """Return the members of *group*, or raise KeyError if group absent."""
    vault = load_vault(vault_name, passphrase)
    groups = _get_groups(vault)
    if group not in groups:
        raise KeyError(f"Group '{group}' does not exist in vault '{vault_name}'.")
    return list(groups[group])


def delete_group(vault_name: str, group: str, passphrase: str) -> None:
    """Delete an entire group (keys are not deleted from the vault)."""
    vault = load_vault(vault_name, passphrase)
    groups = _get_groups(vault)
    if group not in groups:
        raise KeyError(f"Group '{group}' does not exist in vault '{vault_name}'.")
    del groups[group]
    _set_groups(vault, groups)
    save_vault(vault_name, vault, passphrase)
    record_event("group_delete", {"vault": vault_name, "group": group})
