"""Secret strength scoring — rates individual secret values and vault health."""

from __future__ import annotations

import math
import re
from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class SecretScore:
    key: str
    value: str
    score: int          # 0-100
    grade: str          # A / B / C / D / F
    issues: List[str] = field(default_factory=list)


_GRADE_THRESHOLDS = [(90, "A"), (75, "B"), (55, "C"), (35, "D")]


def _grade(score: int) -> str:
    for threshold, letter in _GRADE_THRESHOLDS:
        if score >= threshold:
            return letter
    return "F"


def score_secret(key: str, value: str) -> SecretScore:
    """Score a single secret value on a 0-100 scale."""
    issues: List[str] = []
    points = 0

    length = len(value)
    if length == 0:
        return SecretScore(key=key, value=value, score=0, grade="F",
                           issues=["Value is empty"])

    # Length (up to 40 pts)
    length_pts = min(40, int(length / 32 * 40))
    if length < 8:
        issues.append("Value is very short (< 8 chars)")
    elif length < 16:
        issues.append("Value is short (< 16 chars)")
    points += length_pts

    # Entropy estimate via character-set diversity (up to 40 pts)
    has_lower = bool(re.search(r"[a-z]", value))
    has_upper = bool(re.search(r"[A-Z]", value))
    has_digit = bool(re.search(r"\d", value))
    has_symbol = bool(re.search(r"[^a-zA-Z0-9]", value))
    charset_size = (26 if has_lower else 0) + (26 if has_upper else 0) + \
                   (10 if has_digit else 0) + (32 if has_symbol else 0)
    if charset_size > 0:
        entropy = length * math.log2(charset_size)
        points += min(40, int(entropy / 4))
    if not has_upper and not has_symbol:
        issues.append("No uppercase letters or symbols")

    # Penalty: looks like a placeholder (up to -20)
    placeholder_patterns = [
        r"^(todo|fixme|placeholder|changeme|secret|password|test|example|dummy)$",
        r"^(1234|0000|aaaa)",
    ]
    for pat in placeholder_patterns:
        if re.search(pat, value, re.IGNORECASE):
            points = max(0, points - 20)
            issues.append("Value looks like a placeholder")
            break

    # Bonus: looks like a real token/key (hex, base64-ish)
    if re.fullmatch(r"[0-9a-fA-F]{32,}", value):
        points = min(100, points + 10)
    elif re.fullmatch(r"[A-Za-z0-9+/=_-]{32,}", value):
        points = min(100, points + 5)

    score = max(0, min(100, points))
    return SecretScore(key=key, value=value, score=score,
                       grade=_grade(score), issues=issues)


def score_vault(secrets: Dict[str, str]) -> Dict[str, SecretScore]:
    """Score every key in a flat secrets dict."""
    return {k: score_secret(k, v) for k, v in secrets.items()}


def vault_health(scores: Dict[str, SecretScore]) -> Dict[str, object]:
    """Summarise overall vault health from a set of scores."""
    if not scores:
        return {"average_score": 0, "grade": "F", "total_keys": 0,
                "weak_keys": [], "strong_keys": []}
    avg = sum(s.score for s in scores.values()) / len(scores)
    weak = [k for k, s in scores.items() if s.grade in ("D", "F")]
    strong = [k for k, s in scores.items() if s.grade == "A"]
    return {
        "average_score": round(avg, 1),
        "grade": _grade(int(avg)),
        "total_keys": len(scores),
        "weak_keys": weak,
        "strong_keys": strong,
    }
