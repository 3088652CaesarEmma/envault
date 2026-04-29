"""Audit log for tracking vault access and modifications."""

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

AUDIT_LOG_FILENAME = "audit.log"


def _get_audit_log_path(vault_dir: Optional[str] = None) -> Path:
    base = Path(vault_dir) if vault_dir else Path.home() / ".envault"
    return base / AUDIT_LOG_FILENAME


def record_event(
    action: str,
    vault_name: str,
    details: Optional[str] = None,
    vault_dir: Optional[str] = None,
) -> None:
    """Append an audit event to the log file."""
    log_path = _get_audit_log_path(vault_dir)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "action": action,
        "vault": vault_name,
        "details": details,
    }

    with open(log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


def read_events(
    vault_name: Optional[str] = None,
    limit: int = 50,
    vault_dir: Optional[str] = None,
) -> list[dict]:
    """Read audit events, optionally filtered by vault name."""
    log_path = _get_audit_log_path(vault_dir)

    if not log_path.exists():
        return []

    events = []
    with open(log_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
                if vault_name is None or entry.get("vault") == vault_name:
                    events.append(entry)
            except json.JSONDecodeError:
                continue

    return events[-limit:]


def clear_audit_log(vault_dir: Optional[str] = None) -> None:
    """Delete the audit log file."""
    log_path = _get_audit_log_path(vault_dir)
    if log_path.exists():
        os.remove(log_path)
