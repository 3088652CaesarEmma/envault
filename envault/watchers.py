"""File-system watchers: monitor .env files for changes and sync to vault."""

from __future__ import annotations

import os
import time
from dataclasses import dataclass, field
from typing import Dict, Optional

from envault.audit import record_event

# In-memory registry: vault_name -> WatchEntry
_WATCHERS: Dict[str, "WatchEntry"] = {}


@dataclass
class WatchEntry:
    vault_name: str
    env_path: str
    last_mtime: float = 0.0
    hit_count: int = 0
    enabled: bool = True
    added_at: str = field(default_factory=lambda: _now_iso())


def _now_iso() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()


def add_watcher(vault_name: str, env_path: str) -> WatchEntry:
    """Register a watcher for *env_path* linked to *vault_name*."""
    abs_path = os.path.abspath(env_path)
    mtime = os.path.getmtime(abs_path) if os.path.exists(abs_path) else 0.0
    entry = WatchEntry(vault_name=vault_name, env_path=abs_path, last_mtime=mtime)
    _WATCHERS[vault_name] = entry
    record_event("watcher_added", {"vault": vault_name, "path": abs_path})
    return entry


def remove_watcher(vault_name: str) -> None:
    """Unregister the watcher for *vault_name*. Raises KeyError if absent."""
    if vault_name not in _WATCHERS:
        raise KeyError(f"No watcher registered for vault '{vault_name}'")
    _WATCHERS.pop(vault_name)
    record_event("watcher_removed", {"vault": vault_name})


def list_watchers() -> list[WatchEntry]:
    """Return all registered watcher entries."""
    return list(_WATCHERS.values())


def get_watcher(vault_name: str) -> Optional[WatchEntry]:
    return _WATCHERS.get(vault_name)


def poll_once(vault_name: str, passphrase: str) -> bool:
    """Check whether the watched file has changed; sync if so.

    Returns True when a sync was triggered, False otherwise.
    """
    from envault.sync import sync_env_to_vault

    entry = _WATCHERS.get(vault_name)
    if entry is None or not entry.enabled:
        return False
    if not os.path.exists(entry.env_path):
        return False

    current_mtime = os.path.getmtime(entry.env_path)
    if current_mtime <= entry.last_mtime:
        return False

    sync_env_to_vault(entry.env_path, vault_name, passphrase)
    entry.last_mtime = current_mtime
    entry.hit_count += 1
    record_event("watcher_sync", {"vault": vault_name, "path": entry.env_path})
    return True
