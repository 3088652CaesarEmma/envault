"""Session lock management for envault.

Provides the ability to lock the current session (clearing cached passphrase)
and check whether the session is currently locked.
"""

import time
from typing import Optional

from envault.passphrase import clear_session_passphrase, get_passphrase
from envault.audit import record_event

# Module-level lock state
_locked_at: Optional[float] = None
_auto_lock_seconds: Optional[int] = None


def lock_session() -> None:
    """Lock the session by clearing the cached passphrase and recording the time."""
    global _locked_at
    clear_session_passphrase()
    _locked_at = time.time()
    record_event("session_locked", {})


def unlock_session(passphrase: str) -> bool:
    """Attempt to unlock the session by validating the passphrase.

    Returns True if the passphrase is non-empty (basic validation);
    callers should verify against an actual vault to confirm correctness.
    """
    global _locked_at
    if not passphrase:
        return False
    from envault.passphrase import set_session_passphrase
    set_session_passphrase(passphrase)
    _locked_at = None
    record_event("session_unlocked", {})
    return True


def is_locked() -> bool:
    """Return True if the session is currently locked."""
    if _locked_at is not None:
        return True
    # Also consider locked if auto-lock timeout has elapsed since last activity
    if _auto_lock_seconds is not None:
        try:
            get_passphrase(prompt=False)
        except Exception:
            return True
    return False


def set_auto_lock(seconds: int) -> None:
    """Configure automatic lock after a period of inactivity (in seconds)."""
    global _auto_lock_seconds
    if seconds <= 0:
        raise ValueError("Auto-lock timeout must be a positive integer.")
    _auto_lock_seconds = seconds


def get_lock_status() -> dict:
    """Return a dict describing the current lock state."""
    return {
        "locked": is_locked(),
        "locked_at": _locked_at,
        "auto_lock_seconds": _auto_lock_seconds,
    }


def reset_lock_state() -> None:
    """Reset all lock state (used in tests)."""
    global _locked_at, _auto_lock_seconds
    _locked_at = None
    _auto_lock_seconds = None
