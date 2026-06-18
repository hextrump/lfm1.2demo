"""Unit tests: language detection + scenario-specific recommendations."""
from __future__ import annotations

import pytest


def _agent():
    from runtime.pi_agent import PiAgentRuntime

    return PiAgentRuntime()


# ── language detection ────────────────────────────────────────────────


@pytest.mark.parametrize(
    "text,expected",
    [
        # < 30 alpha chars: function returns False regardless of language
        ("This is English.", False),  # 13 letters, short
        ("短い英文", False),  # very short
        ("日本語です", False),
        ("", False),
        ("1234567890", False),  # no alpha chars
    ],
)
def test_is_mostly_english_short(text, expected):
    r = _agent()
    # Short text (< 30 alpha chars) ALWAYS returns False — the heuristic
    # needs enough text to make a statistically meaningful judgment.
    assert r._is_mostly_english(text) is expected


def test_is_mostly_english_long_english():
    """40+ ASCII letters → True (mostly English)."""
    r = _agent()
    text = "This is a long English sentence with many words. " * 5
    assert r._is_mostly_english(text) is True


def test_is_mostly_english_long_japanese():
    """40+ Japanese letters → False (mostly Japanese)."""
    r = _agent()
    text = "これは日本語のテキストです。" * 10
    assert r._is_mostly_english(text) is False


def test_is_mostly_english_long_japanese():
    r = _agent()
    text = "これは日本語のテキストです。" * 10  # 30+ chars, all Japanese
    assert r._is_mostly_english(text) is False


def test_is_mostly_english_long_english():
    r = _agent()
    text = "This is a long English sentence with many words. " * 5
    assert r._is_mostly_english(text) is True


def test_is_mostly_english_mixed_above_threshold():
    r = _agent()
    # ~60% English — should be flagged as mostly English
    text = "English words here and there. " * 5 + "日本語のテキストが少しだけあります。"
    assert r._is_mostly_english(text) is True


# ── scenario recommendations ──────────────────────────────────────────


@pytest.mark.parametrize(
    "code,symptom,expected_keyword",
    [
        ("AADSTS50076", "login_failed", "MFA"),
        ("AADSTS50105", "app_assignment_missing", "割り当て"),
        ("LICENSE_MISSING", "license_missing", "ライセンス"),
        ("CA_BLOCK", "conditional_access_block", "Conditional Access"),
        ("PBI_ACCESS_DENIED", "report_permission_denied", "BI"),
        ("", "menu_missing", "ロール"),
    ],
)
def test_scenario_recommendations(code, symptom, expected_keyword):
    r = _agent()
    recs = r._scenario_recommendations(code, symptom)
    assert len(recs) > 0, f"no recommendations for {code}/{symptom}"
    assert any(expected_keyword in line for line in recs), (
        f"expected keyword {expected_keyword!r} in recommendations: {recs}"
    )


def test_scenario_recommendations_empty_for_unknown():
    r = _agent()
    assert r._scenario_recommendations("UNKNOWN_CODE", "weird_symptom") == []


# ── reply already structured check ──────────────────────────────────


def test_already_structured_for_pure_english():
    r = _agent()
    english_reply = "This is a long English reply. " * 20
    assert r._reply_already_structured(english_reply) is False


def test_already_structured_for_clean_japanese_with_sections():
    r = _agent()
    reply = (
        "問題を確認しました。\n\n"
        "**追加でお聞きしたいこと:**\n\n"
        "1. 部署名\n"
        "2. 役職\n\n"
        "**推奨される次のステップ:**\n\n"
        "- ログを確認する"
    )
    assert r._reply_already_structured(reply) is True


def test_already_structured_rejects_long_rambling():
    r = _agent()
    # Even if it has the right keywords, a 1000+ char reply is rambling.
    long_reply = "質問: " + ("abcd " * 200) + "推奨: something"
    assert r._reply_already_structured(long_reply) is False
