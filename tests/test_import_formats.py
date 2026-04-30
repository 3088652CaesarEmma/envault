"""Tests for envault.import_formats."""

import pytest

from envault.import_formats import (
    import_from_dotenv,
    import_from_json,
    import_from_shell,
    parse_secrets,
)


class TestImportFromDotenv:
    def test_simple_key_value(self):
        assert import_from_dotenv("FOO=bar") == {"FOO": "bar"}

    def test_double_quoted_value(self):
        assert import_from_dotenv('KEY="hello world"') == {"KEY": "hello world"}

    def test_single_quoted_value(self):
        assert import_from_dotenv("KEY='hello'") == {"KEY": "hello"}

    def test_ignores_blank_lines(self):
        result = import_from_dotenv("\nFOO=1\n\nBAR=2\n")
        assert result == {"FOO": "1", "BAR": "2"}

    def test_ignores_full_line_comments(self):
        result = import_from_dotenv("# comment\nFOO=bar")
        assert "FOO" in result
        assert len(result) == 1

    def test_strips_inline_comment(self):
        result = import_from_dotenv("FOO=bar # this is a comment")
        assert result["FOO"] == "bar"

    def test_ignores_line_without_equals(self):
        result = import_from_dotenv("NOEQUALS\nFOO=bar")
        assert result == {"FOO": "bar"}

    def test_multiple_equals_in_value(self):
        result = import_from_dotenv("TOKEN=abc=def=ghi")
        assert result["TOKEN"] == "abc=def=ghi"


class TestImportFromJson:
    def test_flat_object(self):
        result = import_from_json('{"A": "1", "B": "2"}')
        assert result == {"A": "1", "B": "2"}

    def test_numeric_values_coerced_to_string(self):
        result = import_from_json('{"PORT": 8080}')
        assert result["PORT"] == "8080"

    def test_raises_on_invalid_json(self):
        with pytest.raises(ValueError, match="Invalid JSON"):
            import_from_json("not json")

    def test_raises_on_non_object_root(self):
        with pytest.raises(ValueError, match="root must be an object"):
            import_from_json('["a", "b"]')

    def test_raises_on_nested_dict(self):
        with pytest.raises(ValueError, match="Nested objects"):
            import_from_json('{"NESTED": {"a": 1}}')


class TestImportFromShell:
    def test_export_prefix_stripped(self):
        result = import_from_shell("export FOO=bar")
        assert result == {"FOO": "bar"}

    def test_no_export_prefix(self):
        result = import_from_shell("FOO=bar")
        assert result == {"FOO": "bar"}

    def test_double_quoted_value(self):
        result = import_from_shell('export KEY="hello world"')
        assert result["KEY"] == "hello world"

    def test_ignores_comments(self):
        result = import_from_shell("# comment\nexport FOO=1")
        assert result == {"FOO": "1"}


class TestParseSecrets:
    def test_dispatches_dotenv(self):
        result = parse_secrets("X=1", "dotenv")
        assert result == {"X": "1"}

    def test_dispatches_json(self):
        result = parse_secrets('{"X": "1"}', "json")
        assert result == {"X": "1"}

    def test_dispatches_shell(self):
        result = parse_secrets("export X=1", "shell")
        assert result == {"X": "1"}

    def test_raises_on_unknown_format(self):
        with pytest.raises(ValueError, match="Unknown format"):
            parse_secrets("X=1", "yaml")
