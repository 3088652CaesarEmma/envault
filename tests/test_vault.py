"""Tests for the vault save/load/list functionality."""

import json
import pytest
from pathlib import Path

from envault.vault import save_vault, load_vault, list_vaults


PASSPHRASE = "super-secret-passphrase"
SECRETS = {"API_KEY": "abc123", "DB_URL": "postgres://localhost/mydb", "DEBUG": "false"}


@pytest.fixture
def tmp_vault_dir(tmp_path):
    return tmp_path / "vaults"


class TestSaveVault:
    def test_creates_vault_file(self, tmp_vault_dir):
        path = save_vault("myproject", SECRETS, PASSPHRASE, vault_dir=tmp_vault_dir)
        assert path.exists()

    def test_vault_file_has_expected_keys(self, tmp_vault_dir):
        path = save_vault("myproject", SECRETS, PASSPHRASE, vault_dir=tmp_vault_dir)
        payload = json.loads(path.read_text())
        assert set(payload.keys()) == {"salt", "nonce", "tag", "ciphertext"}

    def test_vault_file_is_not_plaintext(self, tmp_vault_dir):
        path = save_vault("myproject", SECRETS, PASSPHRASE, vault_dir=tmp_vault_dir)
        raw = path.read_text()
        for value in SECRETS.values():
            assert value not in raw

    def test_creates_vault_dir_if_missing(self, tmp_vault_dir):
        assert not tmp_vault_dir.exists()
        save_vault("myproject", SECRETS, PASSPHRASE, vault_dir=tmp_vault_dir)
        assert tmp_vault_dir.exists()

    def test_returns_correct_path(self, tmp_vault_dir):
        path = save_vault("myproject", SECRETS, PASSPHRASE, vault_dir=tmp_vault_dir)
        assert path == tmp_vault_dir / "myproject.vault"


class TestLoadVault:
    def test_roundtrip_returns_original_secrets(self, tmp_vault_dir):
        save_vault("myproject", SECRETS, PASSPHRASE, vault_dir=tmp_vault_dir)
        loaded = load_vault("myproject", PASSPHRASE, vault_dir=tmp_vault_dir)
        assert loaded == SECRETS

    def test_raises_file_not_found_for_missing_vault(self, tmp_vault_dir):
        with pytest.raises(FileNotFoundError, match="nonexistent"):
            load_vault("nonexistent", PASSPHRASE, vault_dir=tmp_vault_dir)

    def test_raises_on_wrong_passphrase(self, tmp_vault_dir):
        save_vault("myproject", SECRETS, PASSPHRASE, vault_dir=tmp_vault_dir)
        with pytest.raises(Exception):
            load_vault("myproject", "wrong-passphrase", vault_dir=tmp_vault_dir)

    def test_empty_secrets_roundtrip(self, tmp_vault_dir):
        save_vault("empty", {}, PASSPHRASE, vault_dir=tmp_vault_dir)
        loaded = load_vault("empty", PASSPHRASE, vault_dir=tmp_vault_dir)
        assert loaded == {}


class TestListVaults:
    def test_returns_empty_list_when_dir_missing(self, tmp_vault_dir):
        assert list_vaults(vault_dir=tmp_vault_dir) == []

    def test_lists_saved_projects(self, tmp_vault_dir):
        save_vault("alpha", SECRETS, PASSPHRASE, vault_dir=tmp_vault_dir)
        save_vault("beta", SECRETS, PASSPHRASE, vault_dir=tmp_vault_dir)
        vaults = list_vaults(vault_dir=tmp_vault_dir)
        assert sorted(vaults) == ["alpha", "beta"]

    def test_ignores_non_vault_files(self, tmp_vault_dir):
        tmp_vault_dir.mkdir(parents=True)
        (tmp_vault_dir / "notes.txt").write_text("not a vault")
        save_vault("real", SECRETS, PASSPHRASE, vault_dir=tmp_vault_dir)
        vaults = list_vaults(vault_dir=tmp_vault_dir)
        assert vaults == ["real"]
