"""Passphrase rotation: re-encrypts all vault secrets under a new passphrase."""

from typing import Optional
from envault.vault import _get_vault_path, save_vault, load_vault, list_vaults
from envault.crypto import derive_key, encrypt, decrypt
from envault.audit import record_event
import base64
import json


def rotate_vault_passphrase(
    vault_name: str,
    old_passphrase: str,
    new_passphrase: str,
    vault_dir: Optional[str] = None,
) -> dict:
    """Re-encrypt all secrets in a vault under a new passphrase.

    Returns a summary dict with keys: vault, rotated_keys, skipped_keys.
    Raises ValueError on decryption failure (wrong old passphrase).
    """
    vault_data = load_vault(vault_name, old_passphrase, vault_dir=vault_dir)

    secrets = vault_data.get("secrets", {})
    rotated_keys = []
    skipped_keys = []

    new_secrets = {}
    for key, value in secrets.items():
        if value is None:
            skipped_keys.append(key)
            new_secrets[key] = value
        else:
            new_secrets[key] = value  # already plaintext from load_vault
            rotated_keys.append(key)

    save_vault(vault_name, new_secrets, new_passphrase, vault_dir=vault_dir)

    record_event(
        "rotate_passphrase",
        {"vault": vault_name, "rotated_keys": len(rotated_keys)},
    )

    return {
        "vault": vault_name,
        "rotated_keys": rotated_keys,
        "skipped_keys": skipped_keys,
    }


def rotate_all_vaults(
    old_passphrase: str,
    new_passphrase: str,
    vault_dir: Optional[str] = None,
) -> list:
    """Rotate passphrase for every vault in the vault directory.

    Returns a list of summary dicts (one per vault).
    Skips vaults that fail decryption and records them with an error entry.
    """
    vaults = list_vaults(vault_dir=vault_dir)
    results = []
    for vault_name in vaults:
        try:
            summary = rotate_vault_passphrase(
                vault_name, old_passphrase, new_passphrase, vault_dir=vault_dir
            )
            results.append(summary)
        except Exception as exc:
            results.append({"vault": vault_name, "error": str(exc)})
    return results
