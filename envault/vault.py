"""Vault module for reading, writing, and managing encrypted .env vault files."""

import json
import os
from pathlib import Path

from envault.crypto import derive_key, encrypt, decrypt

DEFAULT_VAULT_DIR = Path.home() / ".envault"
VAULT_EXTENSION = ".vault"


def _get_vault_path(project_name: str, vault_dir: Path = DEFAULT_VAULT_DIR) -> Path:
    """Return the full path for a named vault file."""
    return vault_dir / f"{project_name}{VAULT_EXTENSION}"


def save_vault(
    project_name: str,
    secrets: dict,
    passphrase: str,
    vault_dir: Path = DEFAULT_VAULT_DIR,
) -> Path:
    """Encrypt and persist secrets for a given project.

    Args:
        project_name: Identifier for the project vault.
        secrets: Dictionary of key/value secret pairs.
        passphrase: Master passphrase used to derive the encryption key.
        vault_dir: Directory where vault files are stored.

    Returns:
        Path to the written vault file.
    """
    vault_dir = Path(vault_dir)
    vault_dir.mkdir(parents=True, exist_ok=True)

    plaintext = json.dumps(secrets).encode()
    salt = os.urandom(16)
    key = derive_key(passphrase, salt)
    ciphertext, nonce, tag = encrypt(key, plaintext)

    payload = {
        "salt": salt.hex(),
        "nonce": nonce.hex(),
        "tag": tag.hex(),
        "ciphertext": ciphertext.hex(),
    }

    vault_path = _get_vault_path(project_name, vault_dir)
    vault_path.write_text(json.dumps(payload, indent=2))
    return vault_path


def load_vault(
    project_name: str,
    passphrase: str,
    vault_dir: Path = DEFAULT_VAULT_DIR,
) -> dict:
    """Decrypt and return secrets for a given project.

    Args:
        project_name: Identifier for the project vault.
        passphrase: Master passphrase used to derive the decryption key.
        vault_dir: Directory where vault files are stored.

    Returns:
        Dictionary of decrypted key/value secret pairs.

    Raises:
        FileNotFoundError: If the vault file does not exist.
        ValueError: If decryption fails (wrong passphrase or corrupted file).
    """
    vault_path = _get_vault_path(project_name, vault_dir)

    if not vault_path.exists():
        raise FileNotFoundError(f"No vault found for project '{project_name}' at {vault_path}")

    payload = json.loads(vault_path.read_text())

    salt = bytes.fromhex(payload["salt"])
    nonce = bytes.fromhex(payload["nonce"])
    tag = bytes.fromhex(payload["tag"])
    ciphertext = bytes.fromhex(payload["ciphertext"])

    key = derive_key(passphrase, salt)
    plaintext = decrypt(key, ciphertext, nonce, tag)
    return json.loads(plaintext.decode())


def list_vaults(vault_dir: Path = DEFAULT_VAULT_DIR) -> list:
    """Return a list of project names that have stored vaults."""
    vault_dir = Path(vault_dir)
    if not vault_dir.exists():
        return []
    return [
        p.stem
        for p in vault_dir.iterdir()
        if p.is_file() and p.suffix == VAULT_EXTENSION
    ]
