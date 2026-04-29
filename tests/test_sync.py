"""Tests for envault.sync — vault <-> .env file synchronisation."""

import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path

from envault.sync import sync_env_to_vault, sync_vault_to_env


PASSPHRASE = "StrongP@ss1"
VAULT_NAME = "test-project"


@pytest.fixture
def tmp_env_file(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("DB_HOST=localhost\nDB_PORT=5432\nSECRET_KEY=abc123\n")
    return str(env_file)


@pytest.fixture
def empty_vault():
    return {"secrets": {}}


@pytest.fixture
def populated_vault():
    return {"secrets": {"DB_HOST": "prod.db", "API_KEY": "xyz"}}


class TestSyncEnvToVault:
    def test_adds_new_keys(self, tmp_env_file, empty_vault):
        with patch("envault.sync.load_vault", return_value=empty_vault), \
             patch("envault.sync.save_vault") as mock_save, \
             patch("envault.sync.get_passphrase", return_value=PASSPHRASE):
            result = sync_env_to_vault(VAULT_NAME, tmp_env_file)

        assert set(result["added"]) == {"DB_HOST", "DB_PORT", "SECRET_KEY"}
        assert result["updated"] == []
        mock_save.assert_called_once()

    def test_detects_updated_keys(self, tmp_env_file, populated_vault):
        with patch("envault.sync.load_vault", return_value=populated_vault), \
             patch("envault.sync.save_vault"), \
             patch("envault.sync.get_passphrase", return_value=PASSPHRASE):
            result = sync_env_to_vault(VAULT_NAME, tmp_env_file)

        assert "DB_HOST" in result["updated"]
        assert "DB_PORT" in result["added"]
        assert "SECRET_KEY" in result["added"]

    def test_uses_provided_passphrase(self, tmp_env_file, empty_vault):
        with patch("envault.sync.load_vault", return_value=empty_vault) as mock_load, \
             patch("envault.sync.save_vault"), \
             patch("envault.sync.get_passphrase") as mock_get:
            sync_env_to_vault(VAULT_NAME, tmp_env_file, passphrase=PASSPHRASE)

        mock_get.assert_not_called()
        mock_load.assert_called_once_with(VAULT_NAME, PASSPHRASE)


class TestSyncVaultToEnv:
    def test_writes_all_secrets_to_new_file(self, tmp_path, populated_vault):
        out_path = str(tmp_path / ".env")
        with patch("envault.sync.load_vault", return_value=populated_vault), \
             patch("envault.sync.get_passphrase", return_value=PASSPHRASE), \
             patch("envault.sync.write_env_file") as mock_write:
            result = sync_vault_to_env(VAULT_NAME, out_path)

        assert set(result["written"]) == {"DB_HOST", "API_KEY"}
        assert result["skipped"] == []
        mock_write.assert_called_once()

    def test_skips_existing_keys_without_overwrite(self, tmp_path, populated_vault):
        env_file = tmp_path / ".env"
        env_file.write_text("DB_HOST=old_value\n")
        with patch("envault.sync.load_vault", return_value=populated_vault), \
             patch("envault.sync.get_passphrase", return_value=PASSPHRASE), \
             patch("envault.sync.write_env_file"):
            result = sync_vault_to_env(VAULT_NAME, str(env_file), overwrite=False)

        assert "DB_HOST" in result["skipped"]
        assert "API_KEY" in result["written"]

    def test_overwrites_existing_keys_when_flag_set(self, tmp_path, populated_vault):
        env_file = tmp_path / ".env"
        env_file.write_text("DB_HOST=old_value\n")
        with patch("envault.sync.load_vault", return_value=populated_vault), \
             patch("envault.sync.get_passphrase", return_value=PASSPHRASE), \
             patch("envault.sync.write_env_file"):
            result = sync_vault_to_env(VAULT_NAME, str(env_file), overwrite=True)

        assert "DB_HOST" in result["written"]
        assert result["skipped"] == []
