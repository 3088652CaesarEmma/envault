"""Template support for envault: save and apply named secret templates."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List

VAULT_DIR = Path.home() / ".envault"
TEMPLATES_FILE = VAULT_DIR / "templates.json"


def _load_templates() -> Dict[str, List[str]]:
    """Load all templates from disk. Returns a dict of name -> list of keys."""
    if not TEMPLATES_FILE.exists():
        return {}
    with TEMPLATES_FILE.open("r") as fh:
        return json.load(fh)


def _save_templates(templates: Dict[str, List[str]]) -> None:
    """Persist templates to disk."""
    VAULT_DIR.mkdir(parents=True, exist_ok=True)
    with TEMPLATES_FILE.open("w") as fh:
        json.dump(templates, fh, indent=2)


def save_template(name: str, keys: List[str]) -> None:
    """Save a named template containing the given list of secret keys."""
    if not name:
        raise ValueError("Template name must not be empty.")
    if not keys:
        raise ValueError("Template must contain at least one key.")
    templates = _load_templates()
    templates[name] = list(keys)
    _save_templates(templates)


def delete_template(name: str) -> None:
    """Remove a template by name. Raises KeyError if not found."""
    templates = _load_templates()
    if name not in templates:
        raise KeyError(f"Template '{name}' does not exist.")
    del templates[name]
    _save_templates(templates)


def list_templates() -> Dict[str, List[str]]:
    """Return all saved templates."""
    return _load_templates()


def apply_template(name: str, vault_secrets: Dict[str, object]) -> Dict[str, object]:
    """Return only the secrets from vault_secrets whose keys are in the template.

    Raises KeyError if the template does not exist.
    Raises ValueError if any required key is missing from vault_secrets.
    """
    templates = _load_templates()
    if name not in templates:
        raise KeyError(f"Template '{name}' does not exist.")
    required_keys = templates[name]
    missing = [k for k in required_keys if k not in vault_secrets]
    if missing:
        raise ValueError(f"Vault is missing template keys: {missing}")
    return {k: vault_secrets[k] for k in required_keys}
