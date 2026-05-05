"""Vault sharing: export an encrypted share bundle and import it."""

from __future__ import annotations

import json
import os
import secrets
from typing import Any

from envault.crypto import derive_key, encrypt, decrypt
from envault.vault import load_vault, save_vault
from envault.audit import record_event

_SHARE_VERSION = 1


def export_share(vault_name: str, passphrase: str, share_passphrase: str) -> dict[str, Any]:
    """Return a JSON-serialisable share bundle for *vault_name*.

    The bundle is re-encrypted with *share_passphrase* so it can be handed
    to another user without revealing the master passphrase.
    """
    secrets_map = load_vault(vault_name, passphrase)

    salt = secrets.token_hex(16)
    key = derive_key(share_passphrase, salt)
    payload = json.dumps(secrets_map)
    ciphertext = encrypt(key, payload)

    bundle = {
        "version": _SHARE_VERSION,
        "vault": vault_name,
        "salt": salt,
        "ciphertext": ciphertext,
    }

    record_event("share_export", {"vault": vault_name})
    return bundle


def import_share(
    bundle: dict[str, Any],
    share_passphrase: str,
    target_vault: str,
    target_passphrase: str,
    merge: bool = False,
) -> dict[str, Any]:
    """Decrypt *bundle* and save its contents into *target_vault*.

    If *merge* is True, existing keys in the target vault are preserved and
    only new / updated keys from the bundle are written.  If False the target
    vault is completely replaced.

    Returns the final secrets map that was saved.
    """
    if bundle.get("version") != _SHARE_VERSION:
        raise ValueError(f"Unsupported share bundle version: {bundle.get('version')}")

    salt = bundle["salt"]
    ciphertext = bundle["ciphertext"]

    key = derive_key(share_passphrase, salt)
    plaintext = decrypt(key, ciphertext)
    incoming: dict[str, Any] = json.loads(plaintext)

    if merge:
        try:
            existing = load_vault(target_vault, target_passphrase)
        except FileNotFoundError:
            existing = {}
        existing.update(incoming)
        final = existing
    else:
        final = incoming

    save_vault(target_vault, final, target_passphrase)
    record_event("share_import", {"vault": target_vault, "merge": merge})
    return final
