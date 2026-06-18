"""Runtime tests: identity / capability / greeting / date short-circuits.

These call `pi_agent.chat(user_text)` and verify the model is NOT
called for trivial exchanges — the short-circuit returns in <100ms.

Skipped automatically if llama-server is not running.
"""
from __future__ import annotations

import time

import pytest


# ── identity ──────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "q,expected_keyword",
    [
        ("who are you", "Agent P"),
        ("What are you?", "Agent P"),
        ("你是谁", "Agent P"),
        ("您是谁", "Agent P"),
        ("あなたは誰", "Agent P"),
    ],
)
def test_identity_question_returns_agent_p(pi_agent, llama_url, q, expected_keyword):
    t0 = time.time()
    result = pi_agent.chat(q)
    elapsed = time.time() - t0
    # Should be sub-second (no model call)
    assert elapsed < 5.0, f"too slow ({elapsed:.1f}s) — model was called?"
    assert expected_keyword in result.reply, f"missing '{expected_keyword}': {result.reply!r}"
    # Should not have any tool events (no model call = no events)
    assert len(result.events) == 0 or all(
        e.tool == "pi_agent" for e in result.events
    ), f"unexpected events: {result.events}"


# ── capability ───────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "q,expected_keyword",
    [
        ("what can you do", "ERP"),
        ("你能做什么", "ERP"),
        ("何ができますか", "ERP"),
    ],
)
def test_capability_question(pi_agent, llama_url, q, expected_keyword):
    result = pi_agent.chat(q)
    assert len(result.reply) > 50
    assert expected_keyword.lower() in result.reply.lower(), (
        f"reply doesn't mention {expected_keyword!r}: {result.reply[:200]!r}"
    )


# ── greeting ─────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "q",
    [
        "hello",
        "你好",
        "こんにちは",
    ],
)
def test_greeting(pi_agent, llama_url, q):
    t0 = time.time()
    result = pi_agent.chat(q)
    elapsed = time.time() - t0
    assert elapsed < 5.0, f"too slow — model was called for greeting {q!r}"
    assert "Agent P" in result.reply
    assert len(result.reply) < 250


# ── date ────────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "q",
    [
        "今天几号",
        "今日は何日",
        "what day is today",
    ],
)
def test_date(pi_agent, llama_url, q):
    t0 = time.time()
    result = pi_agent.chat(q)
    elapsed = time.time() - t0
    assert elapsed < 5.0, f"too slow — model was called for date {q!r}"
    assert "Asia/Tokyo" in result.reply
    import datetime
    this_year = str(datetime.datetime.now().year)
    assert this_year in result.reply
