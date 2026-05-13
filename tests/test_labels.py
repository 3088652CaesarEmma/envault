"""Tests for envault.labels."""

from __future__ import annotations

import pytest

from envault.labels import set_label, get_label, clear_label, list_labeled_keys


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_vault(secrets: dict) -> dict:
    return {"secrets": secrets, "meta": {}}


@pytest.fixture()
def no_audit(monkeypatch):
    monkeypatch.setattr("envault.labels.record_event", lambda *a, **kw: None)


@pytest.fixture()
def patched(monkeypatch, no_audit):
    """Returns (load_store, save_store) so tests can inject vault state."""
    store: dict = {}

    def fake_load(name, pw):
        return store[name]

    def fake_save(name, data, pw):
        store[name] = data

    monkeypatch.setattr("envault.labels.load_vault", fake_load)
    monkeypatch.setattr("envault.labels.save_vault", fake_save)
    return store


# ---------------------------------------------------------------------------
# set_label
# ---------------------------------------------------------------------------

class TestSetLabel:
    def test_sets_label_on_plain_string(self, patched):
        patched["myvault"] = _make_vault({"API_KEY": "secret"})
        set_label("myvault", "API_KEY", "API Key", "pw")
        entry = patched["myvault"]["secrets"]["API_KEY"]
        assert entry["label"] == "API Key"
        assert entry["value"] == "secret"

    def test_sets_label_on_dict_value(self, patched):
        patched["myvault"] = _make_vault({"DB_URL": {"value": "postgres://", "tag": "db"}})
        set_label("myvault", "DB_URL", "Database URL", "pw")
        assert patched["myvault"]["secrets"]["DB_URL"]["label"] == "Database URL"

    def test_raises_on_missing_key(self, patched):
        patched["myvault"] = _make_vault({})
        with pytest.raises(KeyError, match="MISSING"):
            set_label("myvault", "MISSING", "oops", "pw")


# ---------------------------------------------------------------------------
# get_label
# ---------------------------------------------------------------------------

class TestGetLabel:
    def test_returns_label_when_set(self, patched):
        patched["v"] = _make_vault({"K": {"value": "x", "label": "My Key"}})
        assert get_label("v", "K", "pw") == "My Key"

    def test_returns_none_for_plain_string(self, patched):
        patched["v"] = _make_vault({"K": "plain"})
        assert get_label("v", "K", "pw") is None

    def test_returns_none_when_label_absent(self, patched):
        patched["v"] = _make_vault({"K": {"value": "x"}})
        assert get_label("v", "K", "pw") is None

    def test_raises_on_missing_key(self, patched):
        patched["v"] = _make_vault({})
        with pytest.raises(KeyError):
            get_label("v", "NOPE", "pw")


# ---------------------------------------------------------------------------
# clear_label
# ---------------------------------------------------------------------------

class TestClearLabel:
    def test_removes_label(self, patched):
        patched["v"] = _make_vault({"K": {"value": "x", "label": "Old"}})
        clear_label("v", "K", "pw")
        assert "label" not in patched["v"]["secrets"]["K"]

    def test_noop_on_plain_string(self, patched):
        patched["v"] = _make_vault({"K": "plain"})
        clear_label("v", "K", "pw")  # should not raise

    def test_raises_on_missing_key(self, patched):
        patched["v"] = _make_vault({})
        with pytest.raises(KeyError):
            clear_label("v", "GONE", "pw")


# ---------------------------------------------------------------------------
# list_labeled_keys
# ---------------------------------------------------------------------------

class TestListLabeledKeys:
    def test_returns_only_labeled(self, patched):
        patched["v"] = _make_vault({
            "A": {"value": "1", "label": "Alpha"},
            "B": "plain",
            "C": {"value": "3", "label": "Charlie"},
        })
        result = list_labeled_keys("v", "pw")
        assert result == {"A": "Alpha", "C": "Charlie"}

    def test_returns_empty_when_none_labeled(self, patched):
        patched["v"] = _make_vault({"X": "val", "Y": {"value": "v"}})
        assert list_labeled_keys("v", "pw") == {}
