"""Support for exporting vault secrets in multiple formats (dotenv, JSON, shell)."""

import json
from typing import Dict


SUPPORTED_FORMATS = ["dotenv", "json", "shell"]


def export_as_dotenv(secrets: Dict[str, str]) -> str:
    """Render secrets as a .env file string."""
    lines = []
    for key, value in secrets.items():
        # Quote values that contain spaces or special characters
        if any(c in value for c in (" ", "#", "'", '"', "\n")):
            escaped = value.replace('"', '\\"')
            lines.append(f'{key}="{escaped}"')
        else:
            lines.append(f"{key}={value}")
    return "\n".join(lines) + ("\n" if lines else "")


def export_as_json(secrets: Dict[str, str], indent: int = 2) -> str:
    """Render secrets as a JSON object string."""
    return json.dumps(secrets, indent=indent) + "\n"


def export_as_shell(secrets: Dict[str, str]) -> str:
    """Render secrets as shell export statements."""
    lines = []
    for key, value in secrets.items():
        escaped = value.replace("'", "'\"'\"'")
        lines.append(f"export {key}='{escaped}'")
    return "\n".join(lines) + ("\n" if lines else "")


def render_secrets(secrets: Dict[str, str], fmt: str) -> str:
    """Dispatch to the correct renderer based on format name.

    Args:
        secrets: Mapping of environment variable names to values.
        fmt: One of 'dotenv', 'json', or 'shell'.

    Returns:
        Formatted string representation of the secrets.

    Raises:
        ValueError: If the format is not supported.
    """
    if fmt == "dotenv":
        return export_as_dotenv(secrets)
    elif fmt == "json":
        return export_as_json(secrets)
    elif fmt == "shell":
        return export_as_shell(secrets)
    else:
        raise ValueError(
            f"Unsupported format '{fmt}'. Choose from: {', '.join(SUPPORTED_FORMATS)}"
        )
