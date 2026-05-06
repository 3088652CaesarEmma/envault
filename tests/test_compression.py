"""Tests for envault/compression.py."""

import pytest
from envault.compression import (
    compress_payload,
    decompress_payload,
    is_compressed,
    wrap_compressed,
    unwrap_compressed,
    compress_secrets,
    decompress_secrets,
    COMPRESSION_MARKER,
)


class TestCompressDecompressPayload:
    def test_roundtrip_simple_dict(self):
        data = {"value": "hello", "tag": "prod"}
        assert decompress_payload(compress_payload(data)) == data

    def test_roundtrip_nested_dict(self):
        data = {"value": "secret", "expires_at": "2025-01-01", "tags": ["a", "b"]}
        assert decompress_payload(compress_payload(data)) == data

    def test_compressed_output_is_string(self):
        blob = compress_payload({"k": "v"})
        assert isinstance(blob, str)

    def test_compressed_output_is_not_plaintext(self):
        data = {"value": "supersecret"}
        blob = compress_payload(data)
        assert "supersecret" not in blob


class TestIsCompressed:
    def test_returns_true_for_marker_dict(self):
        value = {"type": COMPRESSION_MARKER, "data": "abc123"}
        assert is_compressed(value) is True

    def test_returns_false_for_plain_string(self):
        assert is_compressed("hello") is False

    def test_returns_false_for_plain_dict(self):
        assert is_compressed({"value": "x", "tag": "prod"}) is False

    def test_returns_false_for_dict_missing_type(self):
        assert is_compressed({"data": "blob"}) is False


class TestWrapUnwrap:
    def test_wrap_produces_marker_dict(self):
        wrapped = wrap_compressed("blobdata")
        assert wrapped["type"] == COMPRESSION_MARKER
        assert wrapped["data"] == "blobdata"

    def test_unwrap_extracts_blob(self):
        wrapped = wrap_compressed("blobdata")
        assert unwrap_compressed(wrapped) == "blobdata"

    def test_unwrap_raises_on_non_compressed(self):
        with pytest.raises(ValueError, match="not a compressed payload"):
            unwrap_compressed({"value": "plain"})


class TestCompressDecompressSecrets:
    def test_plain_strings_are_unchanged(self):
        secrets = {"API_KEY": "abc123", "DB_PASS": "hunter2"}
        result = compress_secrets(secrets)
        assert result == secrets

    def test_dict_values_are_compressed(self):
        secrets = {"API_KEY": {"value": "abc", "tags": ["prod"]}}
        result = compress_secrets(secrets)
        assert is_compressed(result["API_KEY"])

    def test_already_compressed_values_are_not_double_compressed(self):
        blob = compress_payload({"value": "x"})
        wrapped = wrap_compressed(blob)
        secrets = {"KEY": wrapped}
        result = compress_secrets(secrets)
        assert result["KEY"] == wrapped

    def test_roundtrip_mixed_secrets(self):
        original = {
            "PLAIN": "simple",
            "RICH": {"value": "complex", "expires_at": "2025-06-01"},
        }
        compressed = compress_secrets(original)
        restored = decompress_secrets(compressed)
        assert restored == original

    def test_decompress_leaves_plain_strings_unchanged(self):
        secrets = {"TOKEN": "mytoken"}
        assert decompress_secrets(secrets) == secrets
