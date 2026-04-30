"""Tests for envault/tags.py"""

import pytest
from unittest.mock import patch, MagicMock
from envault.tags import add_tag, remove_tag, list_tags, filter_by_tag


VAULT_NAME = "test_vault"
PASSPHRASE = "strongpassphrase"


def _make_vault(with_tags=False):
    if with_tags:
        return {"DB_URL": {"value": "postgres://", "tags": ["db", "prod"]}}
    return {"DB_URL": "postgres://", "API_KEY": "secret"}


@patch("envault.tags.record_event")
@patch("envault.tags.save_vault")
@patch("envault.tags.load_vault")
def test_add_tag_to_plain_value(mock_load, mock_save, mock_record):
    mock_load.return_value = _make_vault()
    add_tag(VAULT_NAME, "DB_URL", "db", PASSPHRASE)
    saved = mock_save.call_args[0][1]
    assert "db" in saved["DB_URL"]["tags"]
    mock_record.assert_called_once()


@patch("envault.tags.record_event")
@patch("envault.tags.save_vault")
@patch("envault.tags.load_vault")
def test_add_tag_to_dict_value(mock_load, mock_save, mock_record):
    mock_load.return_value = _make_vault(with_tags=True)
    add_tag(VAULT_NAME, "DB_URL", "staging", PASSPHRASE)
    saved = mock_save.call_args[0][1]
    assert "staging" in saved["DB_URL"]["tags"]
    assert "db" in saved["DB_URL"]["tags"]


@patch("envault.tags.load_vault")
def test_add_tag_raises_on_missing_key(mock_load):
    mock_load.return_value = {}
    with pytest.raises(KeyError, match="MISSING"):
        add_tag(VAULT_NAME, "MISSING", "tag", PASSPHRASE)


@patch("envault.tags.record_event")
@patch("envault.tags.save_vault")
@patch("envault.tags.load_vault")
def test_remove_tag_success(mock_load, mock_save, mock_record):
    mock_load.return_value = _make_vault(with_tags=True)
    remove_tag(VAULT_NAME, "DB_URL", "db", PASSPHRASE)
    saved = mock_save.call_args[0][1]
    assert "db" not in saved["DB_URL"]["tags"]


@patch("envault.tags.load_vault")
def test_remove_tag_raises_on_missing_tag(mock_load):
    mock_load.return_value = _make_vault(with_tags=True)
    with pytest.raises(ValueError, match="nonexistent"):
        remove_tag(VAULT_NAME, "DB_URL", "nonexistent", PASSPHRASE)


@patch("envault.tags.load_vault")
def test_list_tags_returns_tags(mock_load):
    mock_load.return_value = _make_vault(with_tags=True)
    tags = list_tags(VAULT_NAME, "DB_URL", PASSPHRASE)
    assert tags == ["db", "prod"]


@patch("envault.tags.load_vault")
def test_list_tags_returns_empty_for_plain_value(mock_load):
    mock_load.return_value = _make_vault()
    tags = list_tags(VAULT_NAME, "DB_URL", PASSPHRASE)
    assert tags == []


@patch("envault.tags.load_vault")
def test_filter_by_tag_returns_matching_keys(mock_load):
    mock_load.return_value = {
        "DB_URL": {"value": "postgres://", "tags": ["db", "prod"]},
        "REDIS_URL": {"value": "redis://", "tags": ["cache"]},
        "API_KEY": {"value": "secret", "tags": ["prod"]},
    }
    result = filter_by_tag(VAULT_NAME, "prod", PASSPHRASE)
    assert "DB_URL" in result
    assert "API_KEY" in result
    assert "REDIS_URL" not in result


@patch("envault.tags.load_vault")
def test_filter_by_tag_returns_empty_when_no_match(mock_load):
    mock_load.return_value = _make_vault(with_tags=True)
    result = filter_by_tag(VAULT_NAME, "nonexistent", PASSPHRASE)
    assert result == {}
