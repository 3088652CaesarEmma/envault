"""Tests for envault.webhooks."""

import pytest
from unittest.mock import patch, MagicMock
import urllib.error

import envault.webhooks as wh


@pytest.fixture(autouse=True)
def clear_registry():
    wh._WEBHOOK_REGISTRY.clear()
    yield
    wh._WEBHOOK_REGISTRY.clear()


@pytest.fixture(autouse=True)
def no_audit():
    with patch("envault.webhooks.record_event"):
        yield


class TestRegisterWebhook:
    def test_registers_successfully(self):
        result = wh.register_webhook("ci", "https://example.com/hook")
        assert result["name"] == "ci"
        assert result["url"] == "https://example.com/hook"

    def test_appears_in_registry(self):
        wh.register_webhook("ci", "https://example.com/hook")
        assert "ci" in wh._WEBHOOK_REGISTRY

    def test_raises_on_invalid_url(self):
        with pytest.raises(ValueError, match="Invalid webhook URL"):
            wh.register_webhook("bad", "ftp://nope.com")

    def test_overwrites_existing_name(self):
        wh.register_webhook("ci", "https://first.com")
        wh.register_webhook("ci", "https://second.com")
        assert wh._WEBHOOK_REGISTRY["ci"] == "https://second.com"


class TestUnregisterWebhook:
    def test_removes_existing(self):
        wh.register_webhook("ci", "https://example.com")
        wh.unregister_webhook("ci")
        assert "ci" not in wh._WEBHOOK_REGISTRY

    def test_raises_on_missing(self):
        with pytest.raises(KeyError):
            wh.unregister_webhook("ghost")


class TestListWebhooks:
    def test_empty_when_none(self):
        assert wh.list_webhooks() == []

    def test_returns_all_registered(self):
        wh.register_webhook("a", "https://a.com")
        wh.register_webhook("b", "https://b.com")
        names = [h["name"] for h in wh.list_webhooks()]
        assert sorted(names) == ["a", "b"]


class TestFireWebhook:
    def _mock_response(self, status=200):
        resp = MagicMock()
        resp.status = status
        resp.__enter__ = lambda s: s
        resp.__exit__ = MagicMock(return_value=False)
        return resp

    def test_fires_successfully(self):
        wh.register_webhook("ci", "https://example.com/hook")
        with patch("urllib.request.urlopen", return_value=self._mock_response(200)):
            result = wh.fire_webhook("ci", "vault_created", "myapp")
        assert result["status"] == 200
        assert result["error"] is None

    def test_raises_on_unknown_webhook(self):
        with pytest.raises(KeyError):
            wh.fire_webhook("ghost", "event", "vault")

    def test_returns_error_on_url_error(self):
        wh.register_webhook("ci", "https://example.com/hook")
        with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("timeout")):
            result = wh.fire_webhook("ci", "vault_created", "myapp")
        assert result["status"] is None
        assert "timeout" in result["error"]

    def test_fire_all_calls_each(self):
        wh.register_webhook("a", "https://a.com")
        wh.register_webhook("b", "https://b.com")
        with patch("envault.webhooks.fire_webhook", return_value={"status": 200, "error": None}) as mock_fire:
            results = wh.fire_all("rotate", "prod")
        assert mock_fire.call_count == 2
        assert len(results) == 2
