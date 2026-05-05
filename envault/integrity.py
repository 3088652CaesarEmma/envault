"""Vault integrity checking — verify that vault contents have not been tampered with."""

import hashlib
import json
from typing import Optional

from envault.vault import load_vault, save_vault
from envault.audit import record_event


def _compute_checksum(secrets: dict) -> str:
    """Return a SHA-256 hex digest of the canonical JSON representation of secrets."""
    canonical = json.dumps(secrets, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode()).hexdigest()


def stamp_vault(vault_name: str, passphrase: str) -> str:
    """Compute and store an integrity checksum for the vault.

    Returns the checksum that was stored.
    """
    vault = load_vault(vault_name, passphrase)
    secrets = vault.get("secrets", {})
    checksum = _compute_checksum(secrets)
    vault["integrity_checksum"] = checksum
    save_vault(vault_name, vault, passphrase)
    record_event("integrity_stamp", vault_name, {"checksum": checksum})
    return checksum


def verify_vault(vault_name: str, passphrase: str) -> dict:
    """Verify the stored checksum against the current vault secrets.

    Returns a result dict with keys:
        - ``ok`` (bool): True if the vault is intact.
        - ``stored_checksum`` (str | None): The checksum recorded at stamp time.
        - ``current_checksum`` (str): The checksum of the current secrets.
        - ``vault_name`` (str): The vault that was checked.
    """
    vault = load_vault(vault_name, passphrase)
    secrets = vault.get("secrets", {})
    current = _compute_checksum(secrets)
    stored: Optional[str] = vault.get("integrity_checksum")

    ok = stored is not None and stored == current
    record_event(
        "integrity_verify",
        vault_name,
        {"ok": ok, "stored": stored, "current": current},
    )
    return {
        "ok": ok,
        "stored_checksum": stored,
        "current_checksum": current,
        "vault_name": vault_name,
    }
