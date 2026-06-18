"""Unit tests: PiAgentRuntime._direct_basic_reply short-circuit.

These test the pure-Python interception that runs BEFORE the model is
called, so identity / capability / date / greeting questions return in
milliseconds with no model latency.
"""
from __future__ import annotations

import pytest


def _agent():
    from runtime.pi_agent import PiAgentRuntime

    return PiAgentRuntime()


# ── identity ──────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "q,lang",
    [
        ("who are you", "en"),
        ("Who are you?", "en"),
        ("what are you", "en"),
        ("你是谁", "zh"),
        ("你是谁?", "zh"),
        ("您是谁", "zh"),
        ("あなたは誰", "ja"),
        ("あなたは誰ですか", "ja"),
    ],
)
def test_identity_short_circuit(q, lang):
    """All identity questions return Agent P identity in the user's language."""
    r = _agent()
    reply = r._direct_basic_reply(q)
    assert reply is not None, f"no short-circuit for {q!r}"
    assert "Agent P" in reply, f"reply doesn't mention Agent P: {reply!r}"
    # Language should match roughly
    if lang == "en":
        assert any(c in reply.lower() for c in ("i'm", "i am", "agent p"))
    elif lang == "zh":
        # The chinese identity answer may not contain "Agent P" in Chinese, but
        # it must be a non-empty answer.
        assert len(reply) > 5
    elif lang == "ja":
        assert any(s in reply for s in ("Agent P", "エージェント"))


def test_identity_not_called_for_normal_question():
    """A non-identity question does NOT trigger the short-circuit."""
    r = _agent()
    reply = r._direct_basic_reply("今出ているエラーを確認して")
    assert reply is None


# ── capability ───────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "q",
    [
        "what can you do",
        "what can you help with",
        "你能做什么",
        "何ができますか",
    ],
)
def test_capability_short_circuit(q):
    r = _agent()
    reply = r._direct_basic_reply(q)
    assert reply is not None, f"no short-circuit for {q!r}"
    # Capability reply lists ERP/CRM/SSO errors, IT ticket creation, etc.
    assert any(
        kw in reply.lower()
        for kw in ("erp", "crm", "sso", "ticket", "知识", "エラー", "対応", "申請", "許可", "license", "power bi", "bi")
    ), f"reply doesn't list capabilities: {reply!r}"


# ── greeting ─────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "q",
    [
        "hello",
        "hi",
        "good morning",
        "你好",
        "您好",
        "こんにちは",
        "こんばんは",
    ],
)
def test_greeting_short_circuit(q):
    r = _agent()
    reply = r._direct_basic_reply(q)
    assert reply is not None
    assert "Agent P" in reply
    # Greeting should be short
    assert len(reply) < 200


# ── date / day ───────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "q",
    [
        "今天几号",
        "今天日期",
        "今天星期几",
        "今日は何日",
        "今日は何曜日",
        "what day is today",
        "what's the date today",
    ],
)
def test_date_short_circuit(q):
    r = _agent()
    reply = r._direct_basic_reply(q)
    assert reply is not None
    # The date reply should include "Asia/Tokyo" timezone marker
    assert "Asia/Tokyo" in reply
    # Should include today's date in some form (4-digit year + dash)
    import datetime
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    assert today[:4] in reply  # at least the year is there
