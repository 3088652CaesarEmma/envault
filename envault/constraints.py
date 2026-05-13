"""Constraints — attach validation rules to secret keys."""
from __future__ import annotations

import re
from typing import Any

from envault.vault import load_vault, save_vault
from envault.audit import record_event


class ConstraintViolationError(ValueError):
    """Raised when a secret value fails a constraint check."""


# ── internal helpers ──────────────────────────────────────────────────────────

def _to_dict(value: Any) -> dict:
    """Normalise a plain string value to a dict wrapper."""
    if isinstance(value, dict):
        return value
    return {"value": value}


# ── public API ────────────────────────────────────────────────────────────────

def set_constraint(
    vault_name: str,
    key: str,
    passphrase: str,
    *,
    pattern: str | None = None,
    min_length: int | None = None,
    max_length: int | None = None,
    required: bool | None = None,
) -> dict:
    """Attach one or more constraint rules to *key* in *vault_name*."""
    vault = load_vault(vault_name, passphrase)
    if key not in vault:
        raise KeyError(f"Key '{key}' not found in vault '{vault_name}'")

    entry = _to_dict(vault[key])
    constraints = entry.get("constraints", {})

    if pattern is not None:
        constraints["pattern"] = pattern
    if min_length is not None:
        constraints["min_length"] = min_length
    if max_length is not None:
        constraints["max_length"] = max_length
    if required is not None:
        constraints["required"] = required

    entry["constraints"] = constraints
    vault[key] = entry
    save_vault(vault_name, vault, passphrase)
    record_event("set_constraint", {"vault": vault_name, "key": key, "constraints": constraints})
    return constraints


def get_constraint(vault_name: str, key: str, passphrase: str) -> dict:
    """Return the constraints dict for *key*, or {} if none are set."""
    vault = load_vault(vault_name, passphrase)
    if key not in vault:
        raise KeyError(f"Key '{key}' not found in vault '{vault_name}'")
    entry = vault[key]
    if isinstance(entry, dict):
        return entry.get("constraints", {})
    return {}


def clear_constraint(vault_name: str, key: str, passphrase: str) -> None:
    """Remove all constraints from *key*."""
    vault = load_vault(vault_name, passphrase)
    if key not in vault:
        raise KeyError(f"Key '{key}' not found in vault '{vault_name}'")
    if isinstance(vault[key], dict):
        vault[key].pop("constraints", None)
    save_vault(vault_name, vault, passphrase)
    record_event("clear_constraint", {"vault": vault_name, "key": key})


def validate_key(
    vault_name: str, key: str, passphrase: str, *, strict: bool = True
) -> list[str]:
    """Validate *key*'s current value against its constraints.

    Returns a list of violation messages (empty means valid).
    Raises :class:`ConstraintViolationError` when *strict* is True and
    violations exist.
    """
    vault = load_vault(vault_name, passphrase)
    if key not in vault:
        raise KeyError(f"Key '{key}' not found in vault '{vault_name}'")

    entry = vault[key]
    value: str = entry.get("value", "") if isinstance(entry, dict) else entry
    constraints: dict = entry.get("constraints", {}) if isinstance(entry, dict) else {}

    violations: list[str] = []

    if constraints.get("required") and not value:
        violations.append(f"'{key}' is marked required but has an empty value")

    min_len = constraints.get("min_length")
    if min_len is not None and len(value) < min_len:
        violations.append(f"'{key}' value length {len(value)} is below minimum {min_len}")

    max_len = constraints.get("max_length")
    if max_len is not None and len(value) > max_len:
        violations.append(f"'{key}' value length {len(value)} exceeds maximum {max_len}")

    pattern = constraints.get("pattern")
    if pattern and not re.fullmatch(pattern, value):
        violations.append(f"'{key}' value does not match pattern '{pattern}'")

    if strict and violations:
        raise ConstraintViolationError("; ".join(violations))

    return violations
