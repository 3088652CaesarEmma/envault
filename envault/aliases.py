"""Key aliasing — map friendly names to vault keys."""

from __future__ import annotations

from typing import Dict, List, Optional

from envault.vault import load_vault, save_vault
from envault.audit import record_event

_ALIAS_META_KEY = "__aliases__"


def _get_aliases(vault: dict) -> Dict[str, str]:
    """Return the alias map stored inside a vault dict."""
    meta = vault.get(_ALIAS_META_KEY, {})
    if not isinstance(meta, dict):
        return {}
    return meta


def set_alias(vault_name: str, alias: str, target_key: str, passphrase: str) -> None:
    """Create or overwrite *alias* pointing to *target_key*."""
    vault = load_vault(vault_name, passphrase)
    if target_key not in vault:
        raise KeyError(f"Target key '{target_key}' not found in vault '{vault_name}'.")
    aliases = _get_aliases(vault)
    aliases[alias] = target_key
    vault[_ALIAS_META_KEY] = aliases
    save_vault(vault_name, vault, passphrase)
    record_event("alias_set", {"vault": vault_name, "alias": alias, "target": target_key})


def remove_alias(vault_name: str, alias: str, passphrase: str) -> None:
    """Delete *alias* from the vault."""
    vault = load_vault(vault_name, passphrase)
    aliases = _get_aliases(vault)
    if alias not in aliases:
        raise KeyError(f"Alias '{alias}' not found in vault '{vault_name}'.")
    del aliases[alias]
    vault[_ALIAS_META_KEY] = aliases
    save_vault(vault_name, vault, passphrase)
    record_event("alias_removed", {"vault": vault_name, "alias": alias})


def resolve_alias(vault: dict, alias: str) -> Optional[str]:
    """Return the target key for *alias*, or ``None`` if not found."""
    return _get_aliases(vault).get(alias)


def list_aliases(vault: dict) -> List[Dict[str, str]]:
    """Return all aliases as a list of ``{alias, target}`` dicts."""
    return [
        {"alias": a, "target": t}
        for a, t in sorted(_get_aliases(vault).items())
    ]
