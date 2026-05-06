"""Tests for envault.cli_webhooks."""

import pytest
from click.testing import CliRunner
from unittest.mock import patch

from envault.cli_webhooks import webhook_group


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture(autouse=True)
def clear_registry():
    import envault.webhooks as wh
    wh._WEBHOOK_REGISTRY.clear()
    yield
    wh._WEBHOOK_REGISTRY.clear()


@pytest.fixture(autouse=True)
def no_audit():
    with patch("envault.webhooks.record_event"):
        yield


def test_add_webhook_success(runner):
    result = runner.invoke(webhook_group, ["add", "ci", "https://example.com/hook"])
    assert result.exit_code == 0
    assert "ci" in result.output


def test_add_webhook_invalid_url(runner):
    result = runner.invoke(webhook_group, ["add", "bad", "ftp://nope.com"])
    assert result.exit_code == 1
    assert "Error" in result.output


def test_remove_webhook_success(runner):
    runner.invoke(webhook_group, ["add", "ci", "https://example.com"])
    result = runner.invoke(webhook_group, ["remove", "ci"])
    assert result.exit_code == 0
    assert "removed" in result.output


def test_remove_webhook_missing(runner):
    result = runner.invoke(webhook_group, ["remove", "ghost"])
    assert result.exit_code == 1


def test_list_empty(runner):
    result = runner.invoke(webhook_group, ["list"])
    assert result.exit_code == 0
    assert "No webhooks" in result.output


def test_list_shows_registered(runner):
    runner.invoke(webhook_group, ["add", "ci", "https://example.com"])
    result = runner.invoke(webhook_group, ["list"])
    assert "ci" in result.output
    assert "https://example.com" in result.output


def test_fire_success(runner):
    runner.invoke(webhook_group, ["add", "ci", "https://example.com"])
    with patch("envault.cli_webhooks.fire_webhook", return_value={"status": 200, "error": None}):
        result = runner.invoke(webhook_group, ["fire", "ci", "rotate", "prod"])
    assert result.exit_code == 0
    assert "200" in result.output


def test_fire_unknown_webhook(runner):
    result = runner.invoke(webhook_group, ["fire", "ghost", "event", "vault"])
    assert result.exit_code == 1
