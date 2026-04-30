"""Parsers for importing secrets from various formats into a vault."""

from __future__ import annotations

import json
from typing import Dict


def import_from_dotenv(text: str) -> Dict[str, str]:
    """Parse a .env-style string and return a dict of key/value pairs.

    Supports:
    - KEY=VALUE
    - KEY="VALUE"
    - KEY='VALUE'
    - Inline comments after a '#'
    - Blank lines and full-line comments are ignored.
    """
    result: Dict[str, str] = {}
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if "=" not in stripped:
            continue
        key, _, raw_value = stripped.partition("=")
        key = key.strip()
        # Remove inline comment (only outside quotes — simple heuristic)
        value = raw_value.strip()
        if value.startswith('"') and '"' in value[1:]:
            end = value.index('"', 1)
            value = value[1:end]
        elif value.startswith("'") and "'" in value[1:]:
            end = value.index("'", 1)
            value = value[1:end]
        else:
            # Strip inline comment
            if " #" in value:
                value = value[: value.index(" #")].strip()
        if key:
            result[key] = value
    return result


def import_from_json(text: str) -> Dict[str, str]:
    """Parse a flat JSON object and return a dict of key/value pairs.

    All values are coerced to strings.
    Raises ValueError for non-object JSON or nested values.
    """
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError("JSON root must be an object (dict).")
    result: Dict[str, str] = {}
    for k, v in data.items():
        if isinstance(v, dict):
            raise ValueError(f"Nested objects are not supported (key: {k!r}).")
        result[str(k)] = str(v) if not isinstance(v, str) else v
    return result


def import_from_shell(text: str) -> Dict[str, str]:
    """Parse a shell export script (export KEY=VALUE) and return key/value pairs."""
    result: Dict[str, str] = {}
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("export "):
            stripped = stripped[len("export "):].strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, _, raw_value = stripped.partition("=")
        key = key.strip()
        value = raw_value.strip()
        if (value.startswith('"') and value.endswith('"')) or (
            value.startswith("'") and value.endswith("'")
        ):
            value = value[1:-1]
        if key:
            result[key] = value
    return result


FORMAT_PARSERS = {
    "dotenv": import_from_dotenv,
    "json": import_from_json,
    "shell": import_from_shell,
}


def parse_secrets(text: str, fmt: str) -> Dict[str, str]:
    """Dispatch to the correct parser based on *fmt*."""
    if fmt not in FORMAT_PARSERS:
        raise ValueError(f"Unknown format {fmt!r}. Choose from: {list(FORMAT_PARSERS)}.")
    return FORMAT_PARSERS[fmt](text)
