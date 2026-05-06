"""Backup and restore vault data to/from an encrypted archive."""

import json
import os
import tarfile
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from envault.crypto import encrypt, decrypt
from envault.vault import _get_vault_path, load_vault, save_vault
from envault.audit import record_event

_BACKUP_DIR = Path.home() / ".envault" / "backups"


def _get_backup_dir() -> Path:
    _BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    return _BACKUP_DIR


def create_backup(vault_names: list[str], passphrase: str, label: str | None = None) -> dict:
    """Create an encrypted backup archive containing one or more vaults."""
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    label = label or timestamp
    backup_filename = f"backup_{label}.evbak"
    backup_path = _get_backup_dir() / backup_filename

    bundle: dict[str, dict] = {}
    for name in vault_names:
        bundle[name] = load_vault(name, passphrase)

    plaintext = json.dumps(bundle)
    encrypted = encrypt(plaintext, passphrase)

    backup_path.write_text(json.dumps({
        "label": label,
        "created_at": timestamp,
        "vault_names": vault_names,
        "payload": encrypted,
    }))

    record_event("backup_created", {"label": label, "vaults": vault_names})
    return {"label": label, "path": str(backup_path), "vaults": vault_names}


def restore_backup(backup_label: str, passphrase: str, overwrite: bool = False) -> dict:
    """Restore vaults from an encrypted backup archive."""
    backup_path = _get_backup_dir() / f"backup_{backup_label}.evbak"
    if not backup_path.exists():
        raise FileNotFoundError(f"Backup not found: {backup_label}")

    raw = json.loads(backup_path.read_text())
    plaintext = decrypt(raw["payload"], passphrase)
    bundle: dict[str, dict] = json.loads(plaintext)

    restored = []
    skipped = []
    for vault_name, secrets in bundle.items():
        vault_path = _get_vault_path(vault_name)
        if vault_path.exists() and not overwrite:
            skipped.append(vault_name)
            continue
        save_vault(vault_name, secrets, passphrase)
        restored.append(vault_name)

    record_event("backup_restored", {"label": backup_label, "restored": restored, "skipped": skipped})
    return {"restored": restored, "skipped": skipped}


def list_backups() -> list[dict]:
    """List all available backup archives."""
    backups = []
    for f in sorted(_get_backup_dir().glob("backup_*.evbak")):
        try:
            raw = json.loads(f.read_text())
            backups.append({
                "label": raw["label"],
                "created_at": raw["created_at"],
                "vaults": raw["vault_names"],
                "path": str(f),
            })
        except (json.JSONDecodeError, KeyError):
            continue
    return backups


def delete_backup(label: str) -> None:
    """Delete a backup archive by label."""
    backup_path = _get_backup_dir() / f"backup_{label}.evbak"
    if not backup_path.exists():
        raise FileNotFoundError(f"Backup not found: {label}")
    backup_path.unlink()
    record_event("backup_deleted", {"label": label})
