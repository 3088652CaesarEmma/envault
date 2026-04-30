"""Tests for envault.search and the search CLI commands."""

from unittest.mock import patch

import pytest
from click.testing import CliRunner

from envault.search import SearchResult, search_by_key, search_by_value
from envault.cli_search import search_group

PASSPHRASE = "hunter2"

VAULT_A = {
    "secrets": {
        "DB_HOST": "localhost",
        "DB_PASSWORD": {"value": "s3cr3t", "tags": ["db"]},
        "API_KEY": "abc123",
    }
}

VAULT_B = {
    "secrets": {
        "DB_HOST": "prod.example.com",
        "REDIS_URL": "redis://localhost",
    }
}


@pytest.fixture()
def patched_vaults():
    def _load(name, passphrase):
        return {"vault_a": VAULT_A, "vault_b": VAULT_B}[name]

    with patch("envault.search.list_vaults", return_value=["vault_a", "vault_b"]), \
         patch("envault.search.load_vault", side_effect=_load):
        yield


class TestSearchByKey:
    def test_glob_match_returns_results(self, patched_vaults):
        results = search_by_key("DB_*", PASSPHRASE)
        keys = {(r.vault_name, r.key) for r in results}
        assert ("vault_a", "DB_HOST") in keys
        assert ("vault_a", "DB_PASSWORD") in keys
        assert ("vault_b", "DB_HOST") in keys

    def test_glob_no_match_returns_empty(self, patched_vaults):
        results = search_by_key("MISSING_*", PASSPHRASE)
        assert results == []

    def test_regex_match(self, patched_vaults):
        results = search_by_key(r"^API", PASSPHRASE, glob=False)
        assert len(results) == 1
        assert results[0].key == "API_KEY"

    def test_tags_preserved_for_dict_entry(self, patched_vaults):
        results = search_by_key("DB_PASSWORD", PASSPHRASE)
        assert results[0].tags == ["db"]

    def test_restricts_to_named_vaults(self, patched_vaults):
        results = search_by_key("DB_HOST", PASSPHRASE, vault_names=["vault_b"])
        assert all(r.vault_name == "vault_b" for r in results)
        assert len(results) == 1

    def test_broken_vault_is_skipped(self):
        def _load(name, passphrase):
            raise RuntimeError("bad vault")

        with patch("envault.search.list_vaults", return_value=["broken"]), \
             patch("envault.search.load_vault", side_effect=_load):
            results = search_by_key("*", PASSPHRASE)
        assert results == []


class TestSearchByValue:
    def test_finds_matching_value(self, patched_vaults):
        results = search_by_value(r"localhost", PASSPHRASE)
        keys = {r.key for r in results}
        assert "DB_HOST" in keys
        assert "REDIS_URL" in keys

    def test_no_match_returns_empty(self, patched_vaults):
        results = search_by_value(r"NOPE", PASSPHRASE)
        assert results == []


@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture()
def mock_passphrase():
    with patch("envault.cli_search.get_passphrase", return_value=PASSPHRASE):
        yield


class TestSearchCLI:
    def test_key_command_prints_results(self, runner, mock_passphrase, patched_vaults):
        result = runner.invoke(search_group, ["key", "DB_*"])
        assert result.exit_code == 0
        assert "DB_HOST" in result.output

    def test_key_command_no_match_message(self, runner, mock_passphrase, patched_vaults):
        result = runner.invoke(search_group, ["key", "NOTHING"])
        assert "No matching keys found" in result.output

    def test_key_command_show_values(self, runner, mock_passphrase, patched_vaults):
        result = runner.invoke(search_group, ["key", "API_KEY", "--show-values"])
        assert "abc123" in result.output

    def test_value_command_prints_results(self, runner, mock_passphrase, patched_vaults):
        result = runner.invoke(search_group, ["value", "localhost"])
        assert result.exit_code == 0
        assert "DB_HOST" in result.output
