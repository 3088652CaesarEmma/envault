"""Tests for envault/hooks.py."""

import pytest
from envault import hooks
from envault.hooks import (
    register_hook,
    unregister_hook,
    list_hooks,
    fire_hooks,
    clear_hooks,
)


@pytest.fixture(autouse=True)
def reset_registry():
    """Ensure a clean hook registry for every test."""
    clear_hooks()
    yield
    clear_hooks()


def _noop(ctx):
    pass


def _recorder(log):
    def _fn(ctx):
        log.append(ctx)
    return _fn


class TestRegisterHook:
    def test_registers_successfully(self):
        register_hook("pre", "save", _noop)
        assert _noop in list_hooks("pre", "save")

    def test_does_not_duplicate(self):
        register_hook("pre", "save", _noop)
        register_hook("pre", "save", _noop)
        assert list_hooks("pre", "save").count(_noop) == 1

    def test_different_slots_are_independent(self):
        register_hook("pre", "save", _noop)
        assert list_hooks("post", "save") == []


class TestUnregisterHook:
    def test_returns_true_when_found(self):
        register_hook("post", "load", _noop)
        assert unregister_hook("post", "load", _noop) is True

    def test_returns_false_when_not_found(self):
        assert unregister_hook("post", "load", _noop) is False

    def test_hook_is_removed(self):
        register_hook("post", "delete", _noop)
        unregister_hook("post", "delete", _noop)
        assert _noop not in list_hooks("post", "delete")


class TestFireHooks:
    def test_calls_hook_with_context(self):
        log = []
        register_hook("pre", "export", _recorder(log))
        fire_hooks("pre", "export", {"vault": "my_vault"})
        assert log == [{"vault": "my_vault"}]

    def test_calls_multiple_hooks_in_order(self):
        order = []
        register_hook("pre", "rotate", lambda ctx: order.append(1))
        register_hook("pre", "rotate", lambda ctx: order.append(2))
        fire_hooks("pre", "rotate", {})
        assert order == [1, 2]

    def test_no_hooks_does_not_raise(self):
        fire_hooks("post", "save", {"key": "val"})  # should not raise

    def test_exception_in_hook_propagates(self):
        def _boom(ctx):
            raise RuntimeError("hook error")
        register_hook("pre", "save", _boom)
        with pytest.raises(RuntimeError, match="hook error"):
            fire_hooks("pre", "save", {})


class TestClearHooks:
    def test_clears_specific_slot(self):
        register_hook("pre", "save", _noop)
        register_hook("post", "save", _noop)
        clear_hooks("pre", "save")
        assert list_hooks("pre", "save") == []
        assert list_hooks("post", "save") == [_noop]

    def test_clears_all_when_no_args(self):
        register_hook("pre", "save", _noop)
        register_hook("post", "load", _noop)
        clear_hooks()
        assert hooks._registry == {}
