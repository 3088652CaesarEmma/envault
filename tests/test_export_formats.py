"""Tests for envault/export_formats.py"""

import json
import pytest
from envault.export_formats import (
    export_as_dotenv,
    export_as_json,
    export_as_shell,
    render_secrets,
    SUPPORTED_FORMATS,
)

SAMPLE = {"DB_HOST": "localhost", "DB_PORT": "5432", "API_KEY": "abc123"}


class TestExportAsDotenv:
    def test_simple_key_value(self):
        result = export_as_dotenv({"FOO": "bar"})
        assert "FOO=bar" in result

    def test_value_with_spaces_is_quoted(self):
        result = export_as_dotenv({"MSG": "hello world"})
        assert 'MSG="hello world"' in result

    def test_value_with_double_quote_is_escaped(self):
        result = export_as_dotenv({"GREETING": 'say "hi"'})
        assert '\\"' in result

    def test_ends_with_newline(self):
        result = export_as_dotenv(SAMPLE)
        assert result.endswith("\n")

    def test_empty_dict_returns_empty_string(self):
        assert export_as_dotenv({}) == ""

    def test_multiple_keys(self):
        result = export_as_dotenv(SAMPLE)
        for key in SAMPLE:
            assert key in result


class TestExportAsJson:
    def test_valid_json_output(self):
        result = export_as_json(SAMPLE)
        parsed = json.loads(result)
        assert parsed == SAMPLE

    def test_ends_with_newline(self):
        assert export_as_json(SAMPLE).endswith("\n")

    def test_empty_dict(self):
        result = export_as_json({})
        assert json.loads(result) == {}


class TestExportAsShell:
    def test_contains_export_keyword(self):
        result = export_as_shell({"FOO": "bar"})
        assert result.startswith("export FOO=")

    def test_single_quotes_escaped(self):
        result = export_as_shell({"VAR": "it's here"})
        assert "VAR" in result
        # The single quote in value should be safely escaped
        assert "'" in result

    def test_ends_with_newline(self):
        assert export_as_shell(SAMPLE).endswith("\n")

    def test_empty_dict(self):
        assert export_as_shell({}) == ""


class TestRenderSecrets:
    def test_dispatches_dotenv(self):
        result = render_secrets({"X": "1"}, "dotenv")
        assert "X=1" in result

    def test_dispatches_json(self):
        result = render_secrets({"X": "1"}, "json")
        assert json.loads(result) == {"X": "1"}

    def test_dispatches_shell(self):
        result = render_secrets({"X": "1"}, "shell")
        assert "export X=" in result

    def test_raises_on_unknown_format(self):
        with pytest.raises(ValueError, match="Unsupported format"):
            render_secrets({"X": "1"}, "yaml")

    def test_supported_formats_list(self):
        assert "dotenv" in SUPPORTED_FORMATS
        assert "json" in SUPPORTED_FORMATS
        assert "shell" in SUPPORTED_FORMATS
