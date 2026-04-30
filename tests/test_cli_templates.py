"""Tests for envault/cli_templates.py"""

from __future__ import annotations

import pytest
from click.testing import CliRunner
from unittest.mock import patch, MagicMock

from envault.cli_templates import template_group


@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture(autouse=True)
def mock_passphrase():
    with patch("envault.cli_templates.get_passphrase", return_value="s3cret"):
        yield


# ---------------------------------------------------------------------------
# save
# ---------------------------------------------------------------------------

def test_save_template_success(runner):
    with patch("envault.cli_templates.save_template") as mock_save:
        result = runner.invoke(template_group, ["save", "django", "SECRET_KEY", "DB_URL"])
    assert result.exit_code == 0
    assert "django" in result.output
    mock_save.assert_called_once_with("django", ["SECRET_KEY", "DB_URL"])


def test_save_template_error(runner):
    with patch("envault.cli_templates.save_template", side_effect=ValueError("empty")):
        result = runner.invoke(template_group, ["save", "", "KEY"])
    assert result.exit_code != 0


# ---------------------------------------------------------------------------
# delete
# ---------------------------------------------------------------------------

def test_delete_template_success(runner):
    with patch("envault.cli_templates.delete_template") as mock_del:
        result = runner.invoke(template_group, ["delete", "django"])
    assert result.exit_code == 0
    assert "deleted" in result.output
    mock_del.assert_called_once_with("django")


def test_delete_template_not_found(runner):
    with patch("envault.cli_templates.delete_template", side_effect=KeyError("'ghost' does not exist.")):
        result = runner.invoke(template_group, ["delete", "ghost"])
    assert result.exit_code != 0


# ---------------------------------------------------------------------------
# list
# ---------------------------------------------------------------------------

def test_list_templates_shows_entries(runner):
    with patch("envault.cli_templates.list_templates", return_value={"t1": ["A"], "t2": ["B", "C"]}):
        result = runner.invoke(template_group, ["list"])
    assert "t1" in result.output
    assert "t2" in result.output


def test_list_templates_empty(runner):
    with patch("envault.cli_templates.list_templates", return_value={}):
        result = runner.invoke(template_group, ["list"])
    assert "No templates" in result.output


# ---------------------------------------------------------------------------
# apply
# ---------------------------------------------------------------------------

def test_apply_template_success(runner):
    fake_vault = {"secrets": {"SECRET_KEY": "abc", "DB": "pg://"}}
    with patch("envault.cli_templates.load_vault", return_value=fake_vault), \
         patch("envault.cli_templates.apply_template", return_value={"SECRET_KEY": "abc"}), \
         patch("envault.cli_templates.render_secrets", return_value="SECRET_KEY=abc\n") as mock_render:
        result = runner.invoke(template_group, ["apply", "django", "myproject"])
    assert result.exit_code == 0
    assert "SECRET_KEY" in result.output


def test_apply_template_missing_keys(runner):
    fake_vault = {"secrets": {}}
    with patch("envault.cli_templates.load_vault", return_value=fake_vault), \
         patch("envault.cli_templates.apply_template", side_effect=ValueError("missing template keys: ['X']")):
        result = runner.invoke(template_group, ["apply", "django", "myproject"])
    assert result.exit_code != 0
    assert "Error" in result.output
