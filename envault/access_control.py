"""Access control: per-vault read/write permissions tied to named profiles."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional

ACCESS_FILENAME = ".envault_access.json"


def _get_access_path(vault_dir: Path) -> Path:
    return vault_dir / ACCESS_FILENAME


def _load_policy(vault_dir: Path) -> Dict[str, List[str]]:
    path = _get_access_path(vault_dir)
    if not path.exists():
        return {}
    with path.open("r") as fh:
        return json.load(fh)


def _save_policy(vault_dir: Path, policy: Dict[str, List[str]]) -> None:
    path = _get_access_path(vault_dir)
    vault_dir.mkdir(parents=True, exist_ok=True)
    with path.open("w") as fh:
        json.dump(policy, fh, indent=2)


def grant_access(vault_dir: Path, vault_name: str, profile: str, permission: str) -> None:
    """Grant *permission* ('read' or 'write') on *vault_name* to *profile*."""
    if permission not in ("read", "write"):
        raise ValueError(f"Invalid permission '{permission}'. Must be 'read' or 'write'.")
    policy = _load_policy(vault_dir)
    key = f"{vault_name}:{profile}"
    existing = set(policy.get(key, []))
    existing.add(permission)
    policy[key] = sorted(existing)
    _save_policy(vault_dir, policy)


def revoke_access(vault_dir: Path, vault_name: str, profile: str, permission: str) -> None:
    """Revoke *permission* from *profile* on *vault_name*."""
    policy = _load_policy(vault_dir)
    key = f"{vault_name}:{profile}"
    existing = set(policy.get(key, []))
    existing.discard(permission)
    if existing:
        policy[key] = sorted(existing)
    else:
        policy.pop(key, None)
    _save_policy(vault_dir, policy)


def check_access(vault_dir: Path, vault_name: str, profile: str, permission: str) -> bool:
    """Return True if *profile* holds *permission* on *vault_name*."""
    policy = _load_policy(vault_dir)
    key = f"{vault_name}:{profile}"
    return permission in policy.get(key, [])


def list_access(vault_dir: Path, vault_name: Optional[str] = None) -> Dict[str, List[str]]:
    """Return the full policy, optionally filtered to a single vault."""
    policy = _load_policy(vault_dir)
    if vault_name is None:
        return policy
    return {k: v for k, v in policy.items() if k.startswith(f"{vault_name}:")}
