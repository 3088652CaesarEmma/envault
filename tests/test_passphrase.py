"""Tests for envault.passphrase module."""

import os
import pytest
from unittest.mock import patch

import envault.passphrase as passphrase_module
from envault.passphrase import (
    get_passphrase,
    set_session_passphrase,
    clear_session_passphrase,
    prompt_new_passphrase,
    validate_passphrase_strength,
    ENVAULT_PASSPHRASE_ENV_VAR,
)


@pytest.fixture(autouse=True)
def reset_session():
    """Ensure session passphrase is cleared before each test."""
    clear_session_passphrase()
    yield
    clear_session_passphrase()


class TestGetPassphrase:
    def test_returns_env_var_if_set(self, monkeypatch):
        monkeypatch.setenv(ENVAULT_PASSPHRASE_ENV_VAR, "env-secret")
        assert get_passphrase() == "env-secret"

    def test_returns_session_passphrase_if_cached(self, monkeypatch):
        monkeypatch.delenv(ENVAULT_PASSPHRASE_ENV_VAR, raising=False)
        set_session_passphrase("cached-secret")
        assert get_passphrase() == "cached-secret"

    def test_prompts_user_when_no_cache_or_env(self, monkeypatch):
        monkeypatch.delenv(ENVAULT_PASSPHRASE_ENV_VAR, raising=False)
        with patch("getpass.getpass", return_value="prompted-secret") as mock_gp:
            result = get_passphrase()
        assert result == "prompted-secret"
        mock_gp.assert_called_once()

    def test_env_var_takes_priority_over_session(self, monkeypatch):
        monkeypatch.setenv(ENVAULT_PASSPHRASE_ENV_VAR, "env-wins")
        set_session_passphrase("session-secret")
        assert get_passphrase() == "env-wins"


class TestSetSessionPassphrase:
    def test_caches_passphrase(self):
        set_session_passphrase("my-secret")
        assert passphrase_module._session_passphrase == "my-secret"

    def test_raises_on_empty_passphrase(self):
        with pytest.raises(ValueError, match="must not be empty"):
            set_session_passphrase("")


class TestClearSessionPassphrase:
    def test_clears_cached_passphrase(self):
        set_session_passphrase("temp")
        clear_session_passphrase()
        assert passphrase_module._session_passphrase is None


class TestPromptNewPassphrase:
    def test_returns_passphrase_on_match(self):
        with patch("getpass.getpass", side_effect=["StrongPass1!", "StrongPass1!"]):
            result = prompt_new_passphrase()
        assert result == "StrongPass1!"

    def test_retries_on_mismatch_then_succeeds(self):
        side_effects = ["", "any", "SecurePass9#", "SecurePass9#"]
        with patch("getpass.getpass", side_effect=side_effects), \
             patch("builtins.print"):
            result = prompt_new_passphrase()
        assert result == "SecurePass9#"


class TestValidatePassphraseStrength:
    def test_strong_passphrase_returns_no_warnings(self):
        assert validate_passphrase_strength("Str0ng!Passphrase") == []

    def test_short_passphrase_warns(self):
        warnings = validate_passphrase_strength("Short1!")
        assert any("12 characters" in w for w in warnings)

    def test_all_alpha_warns(self):
        warnings = validate_passphrase_strength("AllAlphaPassphrase")
        assert any("non-alphabetic" in w for w in warnings)

    def test_all_lowercase_warns(self):
        warnings = validate_passphrase_strength("alllowercase1!")
        assert any("uppercase" in w for w in warnings)
