"""Tests for envault.constraints."""
from __future__ import annotations

import pytest

from envault.constraints import (
    ConstraintViolationError,
    clear_constraint,
    get_constraint,
    set_constraint,
    validate_key,
)


# ── fixtures ──────────────────────────────────────────────────────────────────

PHRASE = "test-passphrase"


@pytest.fixture()
def _make_vault(tmp_path, monkeypatch):
    """Return a factory that builds a minimal in-memory vault."""
    import envault.constraints as mod

    def factory(secrets: dict):
        vault = dict(secrets)

        def fake_load(name, pw):
            return dict(vault)

        def fake_save(name, data, pw):
            vault.clear()
            vault.update(data)

        monkeypatch.setattr(mod, "load_vault", fake_load)
        monkeypatch.setattr(mod, "save_vault", fake_save)
        monkeypatch.setattr(mod, "record_event", lambda *a, **kw: None)
        return vault

    return factory


# ── set_constraint ────────────────────────────────────────────────────────────

class TestSetConstraint:
    def test_stores_pattern(self, _make_vault):
        _make_vault({"API_KEY": "abc123"})
        result = set_constraint("v", "API_KEY", PHRASE, pattern=r"[a-z0-9]+")
        assert result["pattern"] == r"[a-z0-9]+"

    def test_stores_min_and_max_length(self, _make_vault):
        _make_vault({"TOKEN": "hello"})
        result = set_constraint("v", "TOKEN", PHRASE, min_length=4, max_length=20)
        assert result["min_length"] == 4
        assert result["max_length"] == 20

    def test_stores_required_flag(self, _make_vault):
        _make_vault({"SECRET": "val"})
        result = set_constraint("v", "SECRET", PHRASE, required=True)
        assert result["required"] is True

    def test_raises_on_missing_key(self, _make_vault):
        _make_vault({})
        with pytest.raises(KeyError, match="'MISSING'"):
            set_constraint("v", "MISSING", PHRASE, pattern=".*")

    def test_preserves_existing_value_on_dict_entry(self, _make_vault):
        _make_vault({"KEY": {"value": "hello", "tags": ["prod"]}})
        set_constraint("v", "KEY", PHRASE, min_length=1)
        # get_constraint should reflect the new rule
        c = get_constraint("v", "KEY", PHRASE)
        assert c["min_length"] == 1


# ── get_constraint ────────────────────────────────────────────────────────────

class TestGetConstraint:
    def test_returns_empty_dict_for_plain_string(self, _make_vault):
        _make_vault({"K": "plain"})
        assert get_constraint("v", "K", PHRASE) == {}

    def test_returns_empty_dict_when_no_constraints_key(self, _make_vault):
        _make_vault({"K": {"value": "x"}})
        assert get_constraint("v", "K", PHRASE) == {}

    def test_raises_on_missing_key(self, _make_vault):
        _make_vault({})
        with pytest.raises(KeyError):
            get_constraint("v", "NOPE", PHRASE)


# ── clear_constraint ──────────────────────────────────────────────────────────

class TestClearConstraint:
    def test_removes_constraints(self, _make_vault):
        vault = _make_vault({"K": {"value": "x", "constraints": {"min_length": 1}}})
        clear_constraint("v", "K", PHRASE)
        assert "constraints" not in vault.get("K", {})

    def test_noop_on_plain_string(self, _make_vault):
        _make_vault({"K": "plain"})
        clear_constraint("v", "K", PHRASE)  # should not raise


# ── validate_key ─────────────────────────────────────────────────────────────

class TestValidateKey:
    def test_no_violations_on_unconstrained_key(self, _make_vault):
        _make_vault({"K": "anything"})
        assert validate_key("v", "K", PHRASE, strict=False) == []

    def test_detects_min_length_violation(self, _make_vault):
        _make_vault({"K": {"value": "ab", "constraints": {"min_length": 5}}})
        violations = validate_key("v", "K", PHRASE, strict=False)
        assert any("minimum" in v for v in violations)

    def test_detects_max_length_violation(self, _make_vault):
        _make_vault({"K": {"value": "toolongvalue", "constraints": {"max_length": 4}}})
        violations = validate_key("v", "K", PHRASE, strict=False)
        assert any("exceeds" in v for v in violations)

    def test_detects_pattern_violation(self, _make_vault):
        _make_vault({"K": {"value": "UPPER", "constraints": {"pattern": r"[a-z]+"}}})
        violations = validate_key("v", "K", PHRASE, strict=False)
        assert any("pattern" in v for v in violations)

    def test_detects_required_violation(self, _make_vault):
        _make_vault({"K": {"value": "", "constraints": {"required": True}}})
        violations = validate_key("v", "K", PHRASE, strict=False)
        assert any("required" in v for v in violations)

    def test_strict_raises_on_violation(self, _make_vault):
        _make_vault({"K": {"value": "x", "constraints": {"min_length": 10}}})
        with pytest.raises(ConstraintViolationError):
            validate_key("v", "K", PHRASE, strict=True)

    def test_passes_when_all_constraints_satisfied(self, _make_vault):
        _make_vault({
            "K": {"value": "hello123", "constraints": {
                "min_length": 5, "max_length": 20,
                "pattern": r"[a-z0-9]+", "required": True,
            }}
        })
        assert validate_key("v", "K", PHRASE, strict=True) == []
