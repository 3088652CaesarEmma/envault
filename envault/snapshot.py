"""Snapshot support: capture and restore vault state at a point in time."""

import json
import time
from pathlib import Path
from typing import Optional

from envault.vault import load_vault, save_vault, _get_vault_path
from envault.audit import record_event

_SNAPSHOT_DIR = Path.home() / ".envault" / "snapshots"


def _get_snapshot_path(vault_name: str, label: str) -> Path:
    directory = _SNAPSHOT_DIR / vault_name
    directory.mkdir(parents=True, exist_ok=True)
    return directory / f"{label}.json"


def create_snapshot(vault_name: str, passphrase: str, label: Optional[str] = None) -> str:
    """Capture current vault secrets into a named snapshot. Returns the label used."""
    secrets = load_vault(vault_name, passphrase)
    if label is None:
        label = str(int(time.time()))

    snapshot_path = _get_snapshot_path(vault_name, label)
    snapshot_data = {
        "vault": vault_name,
        "label": label,
        "created_at": time.time(),
        "secrets": secrets,
    }
    snapshot_path.write_text(json.dumps(snapshot_data, indent=2))
    record_event("snapshot_created", {"vault": vault_name, "label": label})
    return label


def restore_snapshot(vault_name: str, label: str, passphrase: str) -> dict:
    """Restore vault secrets from a snapshot. Returns the restored secrets dict."""
    snapshot_path = _get_snapshot_path(vault_name, label)
    if not snapshot_path.exists():
        raise FileNotFoundError(f"Snapshot '{label}' not found for vault '{vault_name}'.")

    snapshot_data = json.loads(snapshot_path.read_text())
    secrets = snapshot_data["secrets"]
    save_vault(vault_name, secrets, passphrase)
    record_event("snapshot_restored", {"vault": vault_name, "label": label})
    return secrets


def list_snapshots(vault_name: str) -> list[dict]:
    """Return metadata for all snapshots of a vault, sorted oldest-first."""
    directory = _SNAPSHOT_DIR / vault_name
    if not directory.exists():
        return []

    results = []
    for path in sorted(directory.glob("*.json")):
        try:
            data = json.loads(path.read_text())
            results.append({
                "label": data.get("label", path.stem),
                "created_at": data.get("created_at"),
                "key_count": len(data.get("secrets", {})),
            })
        except (json.JSONDecodeError, KeyError):
            continue
    return results


def delete_snapshot(vault_name: str, label: str) -> None:
    """Delete a specific snapshot file."""
    snapshot_path = _get_snapshot_path(vault_name, label)
    if not snapshot_path.exists():
        raise FileNotFoundError(f"Snapshot '{label}' not found for vault '{vault_name}'.")
    snapshot_path.unlink()
    record_event("snapshot_deleted", {"vault": vault_name, "label": label})
