"""mentions.py – track which vaults/keys reference a given secret key by name."""
from __future__ import annotations

from typing import Dict, List

from envault.vault import load_vault, list_vaults
from envault.audit import record_event


def find_mentions(key: str, passphrase: str) -> Dict[str, List[str]]:
    """Return a mapping of vault_name -> [matching_keys] where *key* appears.

    Matching is case-insensitive substring search on the secret key names.
    """
    results: Dict[str, List[str]] = {}
    needle = key.lower()
    for vault_name in list_vaults():
        try:
            vault = load_vault(vault_name, passphrase)
        except Exception:
            continue
        secrets: dict = vault.get("secrets", {})
        matched = [k for k in secrets if needle in k.lower()]
        if matched:
            results[vault_name] = matched
    record_event("mentions_searched", {"key": key, "vaults_matched": list(results.keys())})
    return results


def list_cross_references(passphrase: str) -> Dict[str, Dict[str, List[str]]]:
    """Build a cross-reference map: key_name -> {vault_name: [exact_key]}.

    Useful for spotting keys that exist in multiple vaults.
    """
    cross: Dict[str, Dict[str, List[str]]] = {}
    for vault_name in list_vaults():
        try:
            vault = load_vault(vault_name, passphrase)
        except Exception:
            continue
        for k in vault.get("secrets", {}):
            cross.setdefault(k, {})
            cross[k].setdefault(vault_name, [])
            cross[k][vault_name].append(k)
    return cross


def format_mentions(results: Dict[str, List[str]]) -> str:
    """Render find_mentions() results as a human-readable string."""
    if not results:
        return "No mentions found."
    lines: List[str] = []
    for vault_name, keys in sorted(results.items()):
        lines.append(f"  [{vault_name}]")
        for k in sorted(keys):
            lines.append(f"    - {k}")
    return "\n".join(lines)
