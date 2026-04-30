"""Diff utilities for comparing vault secrets against .env files."""

from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class DiffEntry:
    key: str
    status: str  # 'added', 'removed', 'modified', 'unchanged'
    vault_value: Optional[str] = None
    env_value: Optional[str] = None


def diff_vault_vs_env(
    vault_secrets: Dict[str, str],
    env_secrets: Dict[str, str],
) -> List[DiffEntry]:
    """Compare vault secrets against env file secrets and return diff entries."""
    all_keys = set(vault_secrets.keys()) | set(env_secrets.keys())
    entries: List[DiffEntry] = []

    for key in sorted(all_keys):
        in_vault = key in vault_secrets
        in_env = key in env_secrets

        if in_vault and not in_env:
            entries.append(DiffEntry(
                key=key,
                status="removed",
                vault_value=vault_secrets[key],
                env_value=None,
            ))
        elif in_env and not in_vault:
            entries.append(DiffEntry(
                key=key,
                status="added",
                vault_value=None,
                env_value=env_secrets[key],
            ))
        elif vault_secrets[key] != env_secrets[key]:
            entries.append(DiffEntry(
                key=key,
                status="modified",
                vault_value=vault_secrets[key],
                env_value=env_secrets[key],
            ))
        else:
            entries.append(DiffEntry(
                key=key,
                status="unchanged",
                vault_value=vault_secrets[key],
                env_value=env_secrets[key],
            ))

    return entries


def format_diff(entries: List[DiffEntry], show_values: bool = False) -> str:
    """Format diff entries as a human-readable string."""
    symbols = {
        "added": "+ ",
        "removed": "- ",
        "modified": "~ ",
        "unchanged": "  ",
    }
    lines = []
    for entry in entries:
        symbol = symbols[entry.status]
        if show_values and entry.status == "modified":
            lines.append(f"{symbol}{entry.key}  (vault: {entry.vault_value!r} -> env: {entry.env_value!r})")
        else:
            lines.append(f"{symbol}{entry.key}")
    return "\n".join(lines)
