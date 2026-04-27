"""CLI helpers for importing/exporting .env files to/from the vault."""

from pathlib import Path
from typing import Optional

from envault.env_parser import parse_env_file, write_env_file
from envault.vault import save_vault, load_vault


def import_env(vault_name: str, env_path: str | Path, passphrase: str) -> int:
    """Import a .env file into the vault under the given vault name.

    Returns the number of variables imported.
    """
    env_path = Path(env_path)
    env_vars = parse_env_file(env_path)

    if not env_vars:
        raise ValueError(f"No variables found in {env_path}")

    save_vault(vault_name=vault_name, env_vars=env_vars, passphrase=passphrase)
    return len(env_vars)


def export_env(
    vault_name: str,
    passphrase: str,
    output_path: Optional[str | Path] = None,
) -> Dict[str, str]:
    """Export a vault's secrets to a .env file (or return them as a dict).

    If output_path is provided the file is written; otherwise the dict is returned.
    """
    env_vars = load_vault(vault_name=vault_name, passphrase=passphrase)

    if output_path is not None:
        write_env_file(Path(output_path), env_vars)

    return env_vars


def list_env_keys(vault_name: str, passphrase: str) -> list[str]:
    """Return a sorted list of variable names stored in a vault."""
    env_vars = load_vault(vault_name=vault_name, passphrase=passphrase)
    return sorted(env_vars.keys())
