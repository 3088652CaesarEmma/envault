"""Track a history of passphrase-change and import events per vault."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any

_HISTORY_DIR_ENV = "ENVAULT_HISTORY_DIR"
_DEFAULT_HISTORY_DIR = Path.home() / ".envault" / "history"


def _get_history_path(vault_name: str) -> Path:
    base = Path(os.environ.get(_HISTORY_DIR_ENV, _DEFAULT_HISTORY_DIR))
    base.mkdir(parents=True, exist_ok=True)
    return base / f"{vault_name}.jsonl"


def record_history_event(
    vault_name: str,
    event_type: str,
    metadata: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """Append a history event for *vault_name* and return the recorded entry."""
    entry: Dict[str, Any] = {
        "vault": vault_name,
        "event": event_type,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    if metadata:
        entry["metadata"] = metadata

    path = _get_history_path(vault_name)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry) + "\n")

    return entry


def read_history(vault_name: str) -> List[Dict[str, Any]]:
    """Return all history entries for *vault_name*, oldest first."""
    path = _get_history_path(vault_name)
    if not path.exists():
        return []
    entries: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                entries.append(json.loads(line))
    return entries


def clear_history(vault_name: str) -> None:
    """Delete the history log for *vault_name*."""
    path = _get_history_path(vault_name)
    if path.exists():
        path.unlink()
