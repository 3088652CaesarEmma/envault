"""Webhook notifications for vault events."""

import json
import urllib.request
import urllib.error
from datetime import datetime, timezone
from typing import Optional

from envault.audit import record_event

_WEBHOOK_REGISTRY: dict[str, str] = {}


def register_webhook(name: str, url: str) -> dict:
    """Register a named webhook URL."""
    if not url.startswith(("http://", "https://")):
        raise ValueError(f"Invalid webhook URL: {url!r}")
    _WEBHOOK_REGISTRY[name] = url
    record_event("webhook_registered", {"name": name, "url": url})
    return {"name": name, "url": url}


def unregister_webhook(name: str) -> None:
    """Remove a registered webhook by name."""
    if name not in _WEBHOOK_REGISTRY:
        raise KeyError(f"Webhook {name!r} not found")
    del _WEBHOOK_REGISTRY[name]
    record_event("webhook_unregistered", {"name": name})


def list_webhooks() -> list[dict]:
    """Return all registered webhooks."""
    return [{"name": k, "url": v} for k, v in _WEBHOOK_REGISTRY.items()]


def _build_payload(event: str, vault: str, extra: Optional[dict] = None) -> dict:
    payload = {
        "event": event,
        "vault": vault,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    if extra:
        payload.update(extra)
    return payload


def fire_webhook(name: str, event: str, vault: str, extra: Optional[dict] = None) -> dict:
    """Send a webhook notification. Returns a result dict."""
    if name not in _WEBHOOK_REGISTRY:
        raise KeyError(f"Webhook {name!r} not found")
    url = _WEBHOOK_REGISTRY[name]
    payload = _build_payload(event, vault, extra)
    body = json.dumps(payload).encode()
    req = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            status = resp.status
    except urllib.error.HTTPError as exc:
        status = exc.code
    except urllib.error.URLError as exc:
        record_event("webhook_error", {"name": name, "reason": str(exc)})
        return {"name": name, "url": url, "status": None, "error": str(exc)}
    record_event("webhook_fired", {"name": name, "event": event, "vault": vault, "status": status})
    return {"name": name, "url": url, "status": status, "error": None}


def fire_all(event: str, vault: str, extra: Optional[dict] = None) -> list[dict]:
    """Fire all registered webhooks for a given event."""
    return [fire_webhook(name, event, vault, extra) for name in list(_WEBHOOK_REGISTRY)]
