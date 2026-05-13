"""Tests for envault/scoring.py and envault/cli_scoring.py."""

from __future__ import annotations

import pytest
from click.testing import CliRunner
from unittest.mock import patch

from envault.scoring import score_secret, score_vault, vault_health, SecretScore
from envault.cli_scoring import scoring_group


# ---------------------------------------------------------------------------
# score_secret
# ---------------------------------------------------------------------------

class TestScoreSecret:
    def test_returns_secret_score_instance(self):
        result = score_secret("MY_KEY", "SuperSecret123!")
        assert isinstance(result, SecretScore)

    def test_empty_value_scores_zero(self):
        result = score_secret("EMPTY", "")
        assert result.score == 0
        assert result.grade == "F"
        assert any("empty" in i.lower() for i in result.issues)

    def test_short_value_has_issue(self):
        result = score_secret("K", "abc")
        assert any("short" in i.lower() for i in result.issues)

    def test_placeholder_is_penalised(self):
        result = score_secret("DB_PASS", "password")
        assert any("placeholder" in i.lower() for i in result.issues)
        assert result.grade in ("D", "F", "C")

    def test_strong_hex_token_scores_high(self):
        token = "a3f1c9e2b4d07f8a" * 2   # 32-char hex
        result = score_secret("API_KEY", token)
        assert result.score >= 70

    def test_grade_a_for_very_strong_value(self):
        strong = "Tr0ub4dor&3xtraLongP@ssphrase!99"
        result = score_secret("MASTER", strong)
        assert result.grade in ("A", "B")

    def test_grade_f_for_trivial_value(self):
        result = score_secret("X", "aaa")
        assert result.grade == "F"

    def test_no_issues_for_strong_secret(self):
        strong = "Zx9#mQ2$pL8@nW5!kR3^yT6&vB4*jH1"
        result = score_secret("K", strong)
        assert result.issues == [] or result.score >= 80


# ---------------------------------------------------------------------------
# score_vault / vault_health
# ---------------------------------------------------------------------------

class TestScoreVault:
    def test_returns_dict_keyed_by_secret_keys(self):
        secrets = {"A": "hello", "B": "world"}
        scores = score_vault(secrets)
        assert set(scores.keys()) == {"A", "B"}

    def test_empty_vault_returns_empty_dict(self):
        assert score_vault({}) == {}

    def test_vault_health_empty(self):
        health = vault_health({})
        assert health["total_keys"] == 0
        assert health["grade"] == "F"

    def test_vault_health_average_score(self):
        secrets = {"K": "Tr0ub4dor&3xtraLong!99", "W": "abc"}
        scores = score_vault(secrets)
        health = vault_health(scores)
        assert 0 < health["average_score"] <= 100

    def test_weak_keys_listed(self):
        secrets = {"WEAK": "aaa", "STRONG": "Tr0ub4dor&3xtraLong!99XY"}
        scores = score_vault(secrets)
        health = vault_health(scores)
        assert "WEAK" in health["weak_keys"]


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture(autouse=True)
def mock_passphrase():
    with patch("envault.cli_scoring.get_passphrase", return_value="passphrase"):
        yield


_FAKE_VAULT = {
    "secrets": {
        "API_KEY": "a3f1c9e2b4d07f8a" * 2,
        "DB_PASS": "password",
    }
}


def test_score_key_success(runner):
    with patch("envault.cli_scoring.load_vault", return_value=_FAKE_VAULT), \
         patch("envault.cli_scoring.render_secrets",
               return_value={"API_KEY": "a3f1c9e2b4d07f8a" * 2, "DB_PASS": "password"}):
        result = runner.invoke(scoring_group, ["key", "myvault", "API_KEY"])
    assert result.exit_code == 0
    assert "Score" in result.output


def test_score_key_missing_key_exits_1(runner):
    with patch("envault.cli_scoring.load_vault", return_value=_FAKE_VAULT), \
         patch("envault.cli_scoring.render_secrets", return_value={"API_KEY": "val"}):
        result = runner.invoke(scoring_group, ["key", "myvault", "MISSING"])
    assert result.exit_code == 1


def test_score_vault_summary(runner):
    with patch("envault.cli_scoring.load_vault", return_value=_FAKE_VAULT), \
         patch("envault.cli_scoring.render_secrets",
               return_value={"API_KEY": "a3f1c9e2b4d07f8a" * 2, "DB_PASS": "password"}):
        result = runner.invoke(scoring_group, ["vault", "myvault"])
    assert result.exit_code == 0
    assert "Average score" in result.output
    assert "Total keys" in result.output


def test_score_vault_show_all(runner):
    with patch("envault.cli_scoring.load_vault", return_value=_FAKE_VAULT), \
         patch("envault.cli_scoring.render_secrets",
               return_value={"API_KEY": "a3f1c9e2b4d07f8a" * 2, "DB_PASS": "password"}):
        result = runner.invoke(scoring_group, ["vault", "myvault", "--show-all"])
    assert result.exit_code == 0
    assert "API_KEY" in result.output
    assert "DB_PASS" in result.output


def test_score_vault_load_error_exits_1(runner):
    with patch("envault.cli_scoring.load_vault", side_effect=FileNotFoundError("no vault")):
        result = runner.invoke(scoring_group, ["vault", "ghost"])
    assert result.exit_code == 1
