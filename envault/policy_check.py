"""Policy enforcement: validate vault operations against access control rules."""

from typing import Optional
from envault.access_control import check_access


class PolicyViolationError(Exception):
    """Raised when an operation is denied by the access policy."""


def require_permission(
    vault_name: str,
    user: str,
    permission: str,
    *,
    strict: bool = True,
) -> bool:
    """
    Check whether *user* holds *permission* on *vault_name*.

    Parameters
    ----------
    vault_name:
        The name of the vault being accessed.
    user:
        The identity (e.g. username or role) requesting access.
    permission:
        One of ``'read'``, ``'write'``, or ``'admin'``.
    strict:
        When ``True`` (default) raise :class:`PolicyViolationError` if access
        is denied.  When ``False`` simply return ``False``.

    Returns
    -------
    bool
        ``True`` if access is granted.

    Raises
    ------
    PolicyViolationError
        If *strict* is ``True`` and access is denied.
    """
    granted = check_access(vault_name, user, permission)
    if not granted and strict:
        raise PolicyViolationError(
            f"User '{user}' does not have '{permission}' permission on vault '{vault_name}'."
        )
    return granted


def assert_admin(vault_name: str, user: str) -> None:
    """Convenience wrapper that asserts *user* is an admin of *vault_name*."""
    require_permission(vault_name, user, "admin", strict=True)


def can_read(vault_name: str, user: str) -> bool:
    """Return ``True`` if *user* may read *vault_name* (non-strict)."""
    return require_permission(vault_name, user, "read", strict=False)


def can_write(vault_name: str, user: str) -> bool:
    """Return ``True`` if *user* may write to *vault_name* (non-strict)."""
    return require_permission(vault_name, user, "write", strict=False)
