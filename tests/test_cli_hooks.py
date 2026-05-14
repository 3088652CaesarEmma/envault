"""Tests for envault/cli_hooks.py."""

import pytest
from click.testing import CliRunner
from envault.cli_hooks import hooks_group
from envault.hooks import register_hook, clear_hooks


@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture(autouse=True)
def reset():
    clear_hooks()
    yield
    clear_hooks()


def _noop(ctx):
    pass


def test_list_shows_no_hooks_when_empty(runner):
    result = runner.invoke(hooks_group, ["list"])
    assert result.exit_code == 0
    assert "No hooks registered" in result.output


def test_list_shows_registered_hook(runner):
    register_hook("pre", "save", _noop)
    result = runner.invoke(hooks_group, ["list"])
    assert result.exit_code == 0
    assert "pre:save" in result.output


def test_list_filters_by_phase(runner):
    register_hook("pre", "save", _noop)
    register_hook("post", "save", _noop)
    result = runner.invoke(hooks_group, ["list", "--phase", "pre"])
    assert "pre:save" in result.output
    assert "post:save" not in result.output


def test_list_filters_by_event(runner):
    register_hook("pre", "save", _noop)
    register_hook("pre", "load", _noop)
    result = runner.invoke(hooks_group, ["list", "--event", "save"])
    assert "pre:save" in result.output
    assert "pre:load" not in result.output


def test_clear_specific_slot(runner):
    register_hook("pre", "save", _noop)
    result = runner.invoke(
        hooks_group,
        ["clear", "--phase", "pre", "--event", "save"],
        input="y\n",
    )
    assert result.exit_code == 0
    assert "Cleared hooks for pre:save" in result.output


def test_clear_all(runner):
    register_hook("pre", "save", _noop)
    result = runner.invoke(hooks_group, ["clear"], input="y\n")
    assert result.exit_code == 0
    assert "All hooks cleared" in result.output


def test_summary_shows_counts(runner):
    register_hook("pre", "save", _noop)
    register_hook("pre", "save", lambda ctx: None)
    result = runner.invoke(hooks_group, ["summary"])
    assert result.exit_code == 0
    assert "pre:save" in result.output
    assert "2 hook(s)" in result.output


def test_summary_empty(runner):
    result = runner.invoke(hooks_group, ["summary"])
    assert "No hooks registered" in result.output
