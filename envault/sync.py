"""Sync vault data across a project directory by reading/writing .env files."""

import os
from pathlib import Path
from typing import Optional

from envault.vault import load_vault, save_vault
from envault.env_parser import parse_env_file, write_env_file
from envault.crypto import encrypt, decrypt
from envault.passphrase import get_passphrase


def sync_env_to_vault(vault_name: str, env_path: str, passphrase: Optional[str] = None) -> dict:
    """Read a .env file and merge its contents into the named vault.

    Returns a dict with keys 'added' and 'updated' listing changed keys.
    """
    passphrase = passphrase or get_passphrase()
    env_vars = parse_env_file(env_path)

    vault_data = load_vault(vault_name, passphrase)
    secrets = vault_data.get("secrets", {})

    added = []
    updated = []

    for key, value in env_vars.items():
        if key in secrets:
            if secrets[key] != value:
                secrets[key] = value
                updated.append(key)
        else:
            secrets[key] = value
            added.append(key)

    vault_data["secrets"] = secrets
    save_vault(vault_name, vault_data, passphrase)

    return {"added": added, "updated": updated}


def sync_vault_to_env(vault_name: str, env_path: str, passphrase: Optional[str] = None, overwrite: bool = False) -> dict:
    """Write vault secrets into a .env file.

    If the file exists and overwrite=False, only missing keys are added.
    Returns a dict with keys 'written' and 'skipped' listing affected keys.
    """
    passphrase = passphrase or get_passphrase()
    vault_data = load_vault(vault_name, passphrase)
    secrets = vault_data.get("secrets", {})

    existing: dict = {}
    if Path(env_path).exists() and not overwrite:
        existing = parse_env_file(env_path)

    written = []
    skipped = []
    merged = dict(existing)

    for key, value in secrets.items():
        if key in existing and not overwrite:
            skipped.append(key)
        else:
            merged[key] = value
            written.append(key)

    write_env_file(env_path, merged)
    return {"written": written, "skipped": skipped}
