"""Environment profiles (dev/staging/prod) for vault keys."""

from __future__ import annotations

from typing import Dict, List, Optional

from envault.vault import load_vault, save_vault
from envault.audit import record_event

VALID_ENVS = {"dev", "staging", "prod", "test"}


def _to_dict(value) -> dict:
    if isinstance(value, dict):
        return value
    return {"value": value}


def set_environment(vault_name: str, key: str, env: str, passphrase: str) -> dict:
    """Tag a secret key with an environment profile."""
    if env not in VALID_ENVS:
        raise ValueError(f"Invalid environment '{env}'. Must be one of: {sorted(VALID_ENVS)}")

    vault = load_vault(vault_name, passphrase)
    if key not in vault["secrets"]:
        raise KeyError(f"Key '{key}' not found in vault '{vault_name}'")

    entry = _to_dict(vault["secrets"][key])
    entry["environment"] = env
    vault["secrets"][key] = entry
    save_vault(vault_name, vault, passphrase)
    record_event(vault_name, "set_environment", {"key": key, "environment": env})
    return entry


def get_environment(vault_name: str, key: str, passphrase: str) -> Optional[str]:
    """Return the environment tag for a key, or None."""
    vault = load_vault(vault_name, passphrase)
    if key not in vault["secrets"]:
        raise KeyError(f"Key '{key}' not found in vault '{vault_name}'")
    entry = vault["secrets"][key]
    if isinstance(entry, dict):
        return entry.get("environment")
    return None


def clear_environment(vault_name: str, key: str, passphrase: str) -> None:
    """Remove the environment tag from a key."""
    vault = load_vault(vault_name, passphrase)
    if key not in vault["secrets"]:
        raise KeyError(f"Key '{key}' not found in vault '{vault_name}'")
    entry = vault["secrets"][key]
    if isinstance(entry, dict) and "environment" in entry:
        del entry["environment"]
        vault["secrets"][key] = entry
        save_vault(vault_name, vault, passphrase)
        record_event(vault_name, "clear_environment", {"key": key})


def list_by_environment(vault_name: str, env: str, passphrase: str) -> List[str]:
    """Return all keys tagged with a given environment."""
    if env not in VALID_ENVS:
        raise ValueError(f"Invalid environment '{env}'.")
    vault = load_vault(vault_name, passphrase)
    results = []
    for key, value in vault["secrets"].items():
        if isinstance(value, dict) and value.get("environment") == env:
            results.append(key)
    return sorted(results)
