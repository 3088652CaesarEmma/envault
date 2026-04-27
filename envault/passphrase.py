"""Passphrase management utilities for envault."""

import os
import getpass
from typing import Optional

ENVAULT_PASSPHRASE_ENV_VAR = "ENVAULT_PASSPHRASE"
_session_passphrase: Optional[str] = None


def get_passphrase(prompt: str = "Enter master passphrase: ") -> str:
    """Retrieve passphrase from env var, session cache, or prompt user."""
    env_passphrase = os.environ.get(ENVAULT_PASSPHRASE_ENV_VAR)
    if env_passphrase:
        return env_passphrase

    global _session_passphrase
    if _session_passphrase is not None:
        return _session_passphrase

    return getpass.getpass(prompt)


def set_session_passphrase(passphrase: str) -> None:
    """Cache passphrase for the duration of the current session."""
    global _session_passphrase
    if not passphrase:
        raise ValueError("Passphrase must not be empty.")
    _session_passphrase = passphrase


def clear_session_passphrase() -> None:
    """Clear any cached session passphrase."""
    global _session_passphrase
    _session_passphrase = None


def prompt_new_passphrase() -> str:
    """Prompt user to enter and confirm a new passphrase."""
    while True:
        passphrase = getpass.getpass("Enter new master passphrase: ")
        if not passphrase:
            print("Passphrase must not be empty. Please try again.")
            continue
        confirm = getpass.getpass("Confirm master passphrase: ")
        if passphrase != confirm:
            print("Passphrases do not match. Please try again.")
            continue
        return passphrase


def validate_passphrase_strength(passphrase: str) -> list[str]:
    """Return a list of warnings if passphrase is weak. Empty list means OK."""
    warnings = []
    if len(passphrase) < 12:
        warnings.append("Passphrase should be at least 12 characters long.")
    if passphrase.isalpha():
        warnings.append("Passphrase should contain non-alphabetic characters.")
    if passphrase.islower() or passphrase.isupper():
        warnings.append("Passphrase should mix uppercase and lowercase letters.")
    return warnings
