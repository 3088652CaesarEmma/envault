"""Tests for envault.crypto encryption/decryption utilities."""

import pytest

from envault.crypto import encrypt, decrypt, derive_key, SALT_SIZE, KEY_SIZE


PASSPHRASE = "super-secret-passphrase"
SAMPLE_ENV = "DB_HOST=localhost\nDB_PASS=hunter2\nAPI_KEY=abc123"


class TestDeriveKey:
    def test_returns_correct_length(self):
        salt = b"\x00" * SALT_SIZE
        key = derive_key(PASSPHRASE, salt)
        assert len(key) == KEY_SIZE

    def test_deterministic_with_same_inputs(self):
        salt = b"\xde\xad" * 8
        key1 = derive_key(PASSPHRASE, salt)
        key2 = derive_key(PASSPHRASE, salt)
        assert key1 == key2

    def test_different_salt_produces_different_key(self):
        key1 = derive_key(PASSPHRASE, b"\x00" * SALT_SIZE)
        key2 = derive_key(PASSPHRASE, b"\xff" * SALT_SIZE)
        assert key1 != key2


class TestEncryptDecrypt:
    def test_roundtrip(self):
        token = encrypt(SAMPLE_ENV, PASSPHRASE)
        recovered = decrypt(token, PASSPHRASE)
        assert recovered == SAMPLE_ENV

    def test_encrypt_produces_different_tokens(self):
        """Each encryption call should use a fresh salt/nonce."""
        token1 = encrypt(SAMPLE_ENV, PASSPHRASE)
        token2 = encrypt(SAMPLE_ENV, PASSPHRASE)
        assert token1 != token2

    def test_decrypt_wrong_passphrase_raises(self):
        token = encrypt(SAMPLE_ENV, PASSPHRASE)
        with pytest.raises(ValueError, match="Decryption failed"):
            decrypt(token, "wrong-passphrase")

    def test_decrypt_corrupted_payload_raises(self):
        token = encrypt(SAMPLE_ENV, PASSPHRASE)
        corrupted = token[:-4] + "AAAA"
        with pytest.raises(ValueError):
            decrypt(corrupted, PASSPHRASE)

    def test_decrypt_invalid_base64_raises(self):
        with pytest.raises(ValueError, match="Invalid payload encoding"):
            decrypt("!!!not-base64!!!", PASSPHRASE)

    def test_decrypt_too_short_payload_raises(self):
        import base64
        short = base64.b64encode(b"tooshort").decode()
        with pytest.raises(ValueError, match="too short"):
            decrypt(short, PASSPHRASE)

    def test_empty_string_roundtrip(self):
        token = encrypt("", PASSPHRASE)
        assert decrypt(token, PASSPHRASE) == ""

    def test_unicode_content_roundtrip(self):
        content = "SECRET=caf\u00e9\u2615\U0001f511"
        token = encrypt(content, PASSPHRASE)
        assert decrypt(token, PASSPHRASE) == content
