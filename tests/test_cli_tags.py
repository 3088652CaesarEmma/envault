"""Tests for envault/cli_tags.py"""

import pytest
from click.testing import CliRunner
from unittest.mock import patch
from envault.cli_tags import tags_group


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture(autouse=True)
def mock_passphrase():
    with patch("envault.cli_tags.get_passphrase", return_value="strongpass"):
        yield


@patch("envault.cli_tags.add_tag")
def test_add_tag_success(mock_add, runner):
    result = runner.invoke(tags_group, ["add", "myvault", "DB_URL", "prod"])
    assert result.exit_code == 0
    assert "added" in result.output
    mock_add.assert_called_once_with("myvault", "DB_URL", "prod", "strongpass")


@patch("envault.cli_tags.add_tag", side_effect=KeyError("DB_URL"))
def test_add_tag_missing_key(mock_add, runner):
    result = runner.invoke(tags_group, ["add", "myvault", "DB_URL", "prod"])
    assert result.exit_code == 1
    assert "Error" in result.output


@patch("envault.cli_tags.remove_tag")
def test_remove_tag_success(mock_remove, runner):
    result = runner.invoke(tags_group, ["remove", "myvault", "DB_URL", "prod"])
    assert result.exit_code == 0
    assert "removed" in result.output


@patch("envault.cli_tags.remove_tag", side_effect=ValueError("Tag 'x' not found"))
def test_remove_tag_not_found(mock_remove, runner):
    result = runner.invoke(tags_group, ["remove", "myvault", "DB_URL", "x"])
    assert result.exit_code == 1
    assert "Error" in result.output


@patch("envault.cli_tags.list_tags", return_value=["db", "prod"])
def test_list_tags_success(mock_list, runner):
    result = runner.invoke(tags_group, ["list", "myvault", "DB_URL"])
    assert result.exit_code == 0
    assert "db" in result.output
    assert "prod" in result.output


@patch("envault.cli_tags.list_tags", return_value=[])
def test_list_tags_empty(mock_list, runner):
    result = runner.invoke(tags_group, ["list", "myvault", "DB_URL"])
    assert result.exit_code == 0
    assert "No tags found" in result.output


@patch("envault.cli_tags.filter_by_tag", return_value={"DB_URL": "postgres://", "API_KEY": "secret"})
def test_filter_by_tag_success(mock_filter, runner):
    result = runner.invoke(tags_group, ["filter", "myvault", "prod"])
    assert result.exit_code == 0
    assert "DB_URL" in result.output
    assert "API_KEY" in result.output


@patch("envault.cli_tags.filter_by_tag", return_value={})
def test_filter_by_tag_no_matches(mock_filter, runner):
    result = runner.invoke(tags_group, ["filter", "myvault", "ghost"])
    assert result.exit_code == 0
    assert "No keys found" in result.output
