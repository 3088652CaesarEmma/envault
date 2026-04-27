"""Parser for .env files — reads and writes key-value pairs."""

from pathlib import Path
from typing import Dict


def parse_env_file(path: str | Path) -> Dict[str, str]:
    """Parse a .env file and return a dict of key-value pairs.

    Supports:
    - KEY=VALUE
    - KEY="VALUE WITH SPACES"
    - KEY='VALUE WITH SPACES'
    - Lines starting with # are treated as comments
    - Empty lines are skipped
    """
    env_vars: Dict[str, str] = {}
    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(f".env file not found: {path}")

    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()

            if not line or line.startswith("#"):
                continue

            if "=" not in line:
                continue

            key, _, value = line.partition("=")
            key = key.strip()

            if not key:
                continue

            value = value.strip()

            # Strip surrounding quotes
            if len(value) >= 2 and value[0] in ('"', "'") and value[0] == value[-1]:
                value = value[1:-1]

            env_vars[key] = value

    return env_vars


def write_env_file(path: str | Path, env_vars: Dict[str, str]) -> None:
    """Write a dict of key-value pairs to a .env file.

    Values containing spaces or special characters are quoted.
    """
    path = Path(path)
    lines = []

    for key, value in env_vars.items():
        if any(c in value for c in (" ", "\t", "#", "'", '"', "=")):
            # Escape internal double quotes and wrap in double quotes
            escaped = value.replace('"', '\\"')
            lines.append(f'{key}="{escaped}"')
        else:
            lines.append(f"{key}={value}")

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
        if lines:
            f.write("\n")
