"""Tests for envault.mentions."""
from __future__ import annotations

from unittest.mock import patch, MagicMock

import pytest

from envault.mentions import find_mentions, list_cross_references, format_mentions


VAULT_A = {"secrets": {"DATABASE_URL": "postgres://...", "DATABASE_PASS": "s3cr3t"}}
VAULT_B = {"secrets": {"DATABASE_URL": "mysql://...", "API_KEY": "abc123"}}
VAULT_C = {"secrets": {"REDIS_URL": "redis://localhost"}}


@pytest.fixture()
def patched(monkeypatch):
    monkeypatch.setattr("envault.mentions.list_vaults", lambda: ["alpha", "beta", "gamma"])
    monkeypatch.setattr("envault.mentions.record_event", lambda *a, **kw: None)

    def _load(name, _pw):
        return {"alpha": VAULT_A, "beta": VAULT_B, "gamma": VAULT_C}[name]

    monkeypatch.setattr("envault.mentions.load_vault", _load)


class TestFindMentions:
    def test_finds_key_in_multiple_vaults(self, patched):
        results = find_mentions("DATABASE", "pw")
        assert "alpha" in results
        assert "beta" in results
        assert "gamma" not in results

    def test_case_insensitive(self, patched):
        results = find_mentions("database_url", "pw")
        assert "alpha" in results
        assert "DATABASE_URL" in results["alpha"]

    def test_no_match_returns_empty(self, patched):
        results = find_mentions("NONEXISTENT", "pw")
        assert results == {}

    def test_exact_key_only_in_one_vault(self, patched):
        results = find_mentions("API_KEY", "pw")
        assert list(results.keys()) == ["beta"]

    def test_skips_vault_that_raises(self, monkeypatch):
        monkeypatch.setattr("envault.mentions.list_vaults", lambda: ["broken", "ok"])
        monkeypatch.setattr("envault.mentions.record_event", lambda *a, **kw: None)

        def _load(name, _pw):
            if name == "broken":
                raise ValueError("bad passphrase")
            return {"secrets": {"API_KEY": "x"}}

        monkeypatch.setattr("envault.mentions.load_vault", _load)
        results = find_mentions("API_KEY", "pw")
        assert "ok" in results
        assert "broken" not in results


class TestListCrossReferences:
    def test_key_in_two_vaults(self, patched):
        cross = list_cross_references("pw")
        assert "DATABASE_URL" in cross
        assert len(cross["DATABASE_URL"]) == 2

    def test_key_in_one_vault_still_present(self, patched):
        cross = list_cross_references("pw")
        assert "API_KEY" in cross
        assert list(cross["API_KEY"].keys()) == ["beta"]

    def test_returns_dict(self, patched):
        cross = list_cross_references("pw")
        assert isinstance(cross, dict)


class TestFormatMentions:
    def test_empty_returns_no_mentions(self):
        assert format_mentions({}) == "No mentions found."

    def test_single_vault(self):
        out = format_mentions({"myvault": ["KEY_A", "KEY_B"]})
        assert "[myvault]" in out
        assert "KEY_A" in out
        assert "KEY_B" in out

    def test_multiple_vaults_sorted(self):
        out = format_mentions({"z_vault": ["Z"], "a_vault": ["A"]})
        assert out.index("a_vault") < out.index("z_vault")
