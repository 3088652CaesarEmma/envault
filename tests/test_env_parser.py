"""Tests for envault.env_parser module."""

import pytest
from pathlib import Path

from envault.env_parser import parse_env_file, write_env_file


@pytest.fixture
def env_file(tmp_path: Path) -> Path:
    """Create a temporary .env file with sample content."""
    content = (
        "# This is a comment\n"
        "DB_HOST=localhost\n"
        "DB_PORT=5432\n"
        'DB_PASSWORD="secret password"\n'
        "API_KEY='abc123'\n"
        "EMPTY_VALUE=\n"
        "\n"
        "DEBUG=true\n"
    )
    p = tmp_path / ".env"
    p.write_text(content, encoding="utf-8")
    return p


class TestParseEnvFile:
    def test_parses_simple_key_value(self, env_file: Path):
        result = parse_env_file(env_file)
        assert result["DB_HOST"] == "localhost"
        assert result["DB_PORT"] == "5432"

    def test_strips_double_quotes(self, env_file: Path):
        result = parse_env_file(env_file)
        assert result["DB_PASSWORD"] == "secret password"

    def test_strips_single_quotes(self, env_file: Path):
        result = parse_env_file(env_file)
        assert result["API_KEY"] == "abc123"

    def test_ignores_comments(self, env_file: Path):
        result = parse_env_file(env_file)
        assert not any(k.startswith("#") for k in result)

    def test_handles_empty_value(self, env_file: Path):
        result = parse_env_file(env_file)
        assert result["EMPTY_VALUE"] == ""

    def test_returns_all_valid_keys(self, env_file: Path):
        result = parse_env_file(env_file)
        assert set(result.keys()) == {"DB_HOST", "DB_PORT", "DB_PASSWORD", "API_KEY", "EMPTY_VALUE", "DEBUG"}

    def test_raises_if_file_not_found(self, tmp_path: Path):
        with pytest.raises(FileNotFoundError):
            parse_env_file(tmp_path / "nonexistent.env")


class TestWriteEnvFile:
    def test_writes_simple_key_value(self, tmp_path: Path):
        path = tmp_path / ".env"
        write_env_file(path, {"KEY": "value"})
        assert path.read_text() == "KEY=value\n"

    def test_quotes_values_with_spaces(self, tmp_path: Path):
        path = tmp_path / ".env"
        write_env_file(path, {"KEY": "hello world"})
        assert 'KEY="hello world"' in path.read_text()

    def test_roundtrip(self, tmp_path: Path):
        original = {"HOST": "localhost", "TOKEN": "abc 123", "PORT": "8080"}
        path = tmp_path / ".env"
        write_env_file(path, original)
        result = parse_env_file(path)
        assert result == original

    def test_creates_file_if_not_exists(self, tmp_path: Path):
        path = tmp_path / "new.env"
        write_env_file(path, {"X": "1"})
        assert path.exists()
