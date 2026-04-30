"""Search secrets across vaults by key name or value pattern."""

from __future__ import annotations

import fnmatch
import re
from dataclasses import dataclass, field
from typing import List, Optional

from envault.vault import list_vaults, load_vault


@dataclass
class SearchResult:
    vault_name: str
    key: str
    value: str
    tags: List[str] = field(default_factory=list)


def search_by_key(
    pattern: str,
    passphrase: str,
    vault_names: Optional[List[str]] = None,
    glob: bool = True,
) -> List[SearchResult]:
    """Search for keys matching *pattern* across one or more vaults.

    Args:
        pattern: Key name pattern (glob by default, regex if glob=False).
        passphrase: Master passphrase used to decrypt vaults.
        vault_names: Restrict search to these vault names; None means all vaults.
        glob: When True treat pattern as a glob expression, else as regex.

    Returns:
        List of :class:`SearchResult` objects for every matching key.
    """
    results: List[SearchResult] = []
    targets = vault_names if vault_names is not None else list_vaults()

    for name in targets:
        try:
            vault = load_vault(name, passphrase)
        except Exception:
            continue
        secrets: dict = vault.get("secrets", {})
        for key, entry in secrets.items():
            match = (
                fnmatch.fnmatch(key, pattern)
                if glob
                else bool(re.search(pattern, key))
            )
            if not match:
                continue
            if isinstance(entry, dict):
                value = entry.get("value", "")
                tags = entry.get("tags", [])
            else:
                value = str(entry)
                tags = []
            results.append(SearchResult(vault_name=name, key=key, value=value, tags=tags))

    return results


def search_by_value(
    pattern: str,
    passphrase: str,
    vault_names: Optional[List[str]] = None,
) -> List[SearchResult]:
    """Search for secrets whose *value* contains the given regex pattern.

    Args:
        pattern: Regex pattern matched against secret values.
        passphrase: Master passphrase used to decrypt vaults.
        vault_names: Restrict search to these vault names; None means all vaults.

    Returns:
        List of :class:`SearchResult` objects for every matching secret.
    """
    results: List[SearchResult] = []
    targets = vault_names if vault_names is not None else list_vaults()
    compiled = re.compile(pattern)

    for name in targets:
        try:
            vault = load_vault(name, passphrase)
        except Exception:
            continue
        secrets: dict = vault.get("secrets", {})
        for key, entry in secrets.items():
            if isinstance(entry, dict):
                value = entry.get("value", "")
                tags = entry.get("tags", [])
            else:
                value = str(entry)
                tags = []
            if compiled.search(value):
                results.append(SearchResult(vault_name=name, key=key, value=value, tags=tags))

    return results
