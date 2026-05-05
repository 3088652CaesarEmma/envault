"""Tests for envault.integrity."""

import pytest
from unittest.mock import patch, MagicMock

from envault.integrity import _compute_checksum, stamp_vault, verify_vault


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_vault(secrets: dict) -> dict:
    return {"name": "myvault", "secrets": secrets}


PASSPHRASE = "hunter2"
VAULT_NAME = "myvault"


@pytest.fixture()
def no_audit():
    with patch("envault.integrity.record_event"):
        yield


# ---------------------------------------------------------------------------
# _compute_checksum
# ---------------------------------------------------------------------------

class TestComputeChecksum:
    def test_returns_64_char_hex_string(self):
        result = _compute_checksum({"KEY": "value"})
        assert len(result) == 64
        assert all(c in "0123456789abcdef" for c in result)

    def test_deterministic(self):
        secrets = {"A": "1", "B": "2"}
        assert _compute_checksum(secrets) == _compute_checksum(secrets)

    def test_order_independent(self):
        a = _compute_checksum({"A": "1", "B": "2"})
        b = _compute_checksum({"B": "2", "A": "1"})
        assert a == b

    def test_different_secrets_produce_different_checksums(self):
        assert _compute_checksum({"A": "1"}) != _compute_checksum({"A": "2"})


# ---------------------------------------------------------------------------
# stamp_vault
# ---------------------------------------------------------------------------

class TestStampVault:
    def test_returns_checksum_string(self, no_audit):
        vault = _make_vault({"DB_URL": "postgres://localhost"})
        with patch("envault.integrity.load_vault", return_value=vault), \
             patch("envault.integrity.save_vault") as mock_save:
            result = stamp_vault(VAULT_NAME, PASSPHRASE)
        assert isinstance(result, str) and len(result) == 64

    def test_checksum_stored_in_vault(self, no_audit):
        vault = _make_vault({"KEY": "val"})
        saved_vault = {}
        def capture_save(name, v, pw):
            saved_vault.update(v)
        with patch("envault.integrity.load_vault", return_value=vault), \
             patch("envault.integrity.save_vault", side_effect=capture_save):
            checksum = stamp_vault(VAULT_NAME, PASSPHRASE)
        assert saved_vault["integrity_checksum"] == checksum

    def test_calls_save_vault_once(self, no_audit):
        vault = _make_vault({})
        with patch("envault.integrity.load_vault", return_value=vault), \
             patch("envault.integrity.save_vault") as mock_save:
            stamp_vault(VAULT_NAME, PASSPHRASE)
        mock_save.assert_called_once()


# ---------------------------------------------------------------------------
# verify_vault
# ---------------------------------------------------------------------------

class TestVerifyVault:
    def test_ok_when_checksum_matches(self, no_audit):
        secrets = {"X": "y"}
        checksum = _compute_checksum(secrets)
        vault = {"secrets": secrets, "integrity_checksum": checksum}
        with patch("envault.integrity.load_vault", return_value=vault):
            result = verify_vault(VAULT_NAME, PASSPHRASE)
        assert result["ok"] is True

    def test_not_ok_when_checksum_missing(self, no_audit):
        vault = {"secrets": {"KEY": "val"}}  # no stored checksum
        with patch("envault.integrity.load_vault", return_value=vault):
            result = verify_vault(VAULT_NAME, PASSPHRASE)
        assert result["ok"] is False
        assert result["stored_checksum"] is None

    def test_not_ok_when_secrets_tampered(self, no_audit):
        original = {"KEY": "original"}
        checksum = _compute_checksum(original)
        tampered = {"KEY": "tampered"}
        vault = {"secrets": tampered, "integrity_checksum": checksum}
        with patch("envault.integrity.load_vault", return_value=vault):
            result = verify_vault(VAULT_NAME, PASSPHRASE)
        assert result["ok"] is False

    def test_result_contains_vault_name(self, no_audit):
        vault = {"secrets": {}}
        with patch("envault.integrity.load_vault", return_value=vault):
            result = verify_vault(VAULT_NAME, PASSPHRASE)
        assert result["vault_name"] == VAULT_NAME

    def test_result_contains_both_checksums(self, no_audit):
        secrets = {"A": "b"}
        stored = _compute_checksum(secrets)
        vault = {"secrets": secrets, "integrity_checksum": stored}
        with patch("envault.integrity.load_vault", return_value=vault):
            result = verify_vault(VAULT_NAME, PASSPHRASE)
        assert result["stored_checksum"] == stored
        assert result["current_checksum"] == stored
