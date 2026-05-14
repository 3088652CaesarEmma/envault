"""Pre/post operation hooks for envault.

Allows registering Python callables that fire before or after
specific vault operations (e.g. 'save', 'load', 'delete').
"""

from __future__ import annotations

from typing import Callable, Dict, List, Literal, Any

HookPhase = Literal["pre", "post"]
HookEvent = Literal["save", "load", "delete", "rotate", "export"]

_registry: Dict[str, List[Callable[..., None]]] = {}


def _key(phase: HookPhase, event: HookEvent) -> str:
    return f"{phase}:{event}"


def register_hook(phase: HookPhase, event: HookEvent, fn: Callable[..., None]) -> None:
    """Register a callable to run at *phase* for *event*."""
    k = _key(phase, event)
    _registry.setdefault(k, [])
    if fn not in _registry[k]:
        _registry[k].append(fn)


def unregister_hook(phase: HookPhase, event: HookEvent, fn: Callable[..., None]) -> bool:
    """Remove a previously registered hook. Returns True if it was found."""
    k = _key(phase, event)
    hooks = _registry.get(k, [])
    if fn in hooks:
        hooks.remove(fn)
        return True
    return False


def list_hooks(phase: HookPhase, event: HookEvent) -> List[Callable[..., None]]:
    """Return all hooks registered for *phase* + *event*."""
    return list(_registry.get(_key(phase, event), []))


def fire_hooks(phase: HookPhase, event: HookEvent, context: Dict[str, Any]) -> None:
    """Invoke every hook registered for *phase* + *event*, passing *context*.

    Hooks are called in registration order. Exceptions propagate immediately.
    """
    for fn in list_hooks(phase, event):
        fn(context)


def clear_hooks(phase: HookPhase | None = None, event: HookEvent | None = None) -> None:
    """Clear hooks. If both phase and event are given, clears only that slot.
    If neither is given, clears the entire registry.
    """
    if phase is not None and event is not None:
        _registry.pop(_key(phase, event), None)
    else:
        _registry.clear()
