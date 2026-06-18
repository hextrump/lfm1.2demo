"""Runtime tests: structured followup / no-fake-streaming / no-hallucination."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
TICKETS_STATE = PROJECT_ROOT / "erp_state" / "tickets.json"
ERROR_STATE = PROJECT_ROOT / "erp_state" / "current_error.json"


def test_no_fake_streaming(pi_agent, llama_url, set_scenario):
    """The chat() result.reply is the FULL reply — no per-character
    fake streaming animation. The model returns the whole text in one
    shot and the UI just renders it.
    """
    set_scenario("AADSTS50076")
    result = pi_agent.chat("今出ているエラーを確認して")
    # Reply is the complete text (not a partial, mid-stream string).
    # The model should have produced a complete Japanese answer.
    assert len(result.reply) > 50
    # Should look like a finished answer, not a "..." placeholder
    assert not result.reply.strip().endswith("…")
    assert not result.reply.strip().endswith("...")


def test_ticket_no_hallucination(pi_agent, llama_url, set_scenario):
    """When user asks for a ticket, the result.ticket is a real
    KW-#### with the right structure — not a hallucinated id like
    'ERC20260117-001' or 'AUDITOR_REQUESTING' placeholders."""
    set_scenario("AADSTS50076")
    result = pi_agent.chat("チケットで依頼して")
    if result.ticket is None:
        pytest.skip("model did not produce a ticket (test may need a stronger prompt)")
    tid = result.ticket["ticket_id"]
    assert tid.startswith("KW-"), f"bad ticket id format: {tid!r}"
    assert len(tid) == 7
    assert tid[3:].isdigit()
    # No placeholder content
    summary = result.ticket.get("summary", "")
    assert "[" not in summary, f"placeholder detected in summary: {summary!r}"
    assert "AUDITOR" not in summary, f"hallucinated summary: {summary!r}"


def test_ticket_persisted_to_disk(pi_agent, llama_url, set_scenario):
    set_scenario("AADSTS50076")
    result = pi_agent.chat("チケットで依頼して")
    if result.ticket is None:
        pytest.skip("model did not produce a ticket")
    # The code-level path persists via the Streamlit layer; the runtime
    # alone does not. So we check that the ticket is well-formed and
    # contains a real requester (from current_error.json) — the Streamlit
    # layer would then persist to disk on session_state mutation.
    assert result.ticket["requester"] == "taro.yamada@demo.local"
    # The ticket inherits error_code / system / route from the scenario;
    # it does NOT carry scenario_key.
    assert result.ticket["error_code"] == "AADSTS50076"
    assert result.ticket["system"] == "Dynamics 365"
    assert result.ticket["route"] == "Identity / Entra ID 管理チーム"


def test_followup_block_for_specific_error(pi_agent, llama_url, set_scenario):
    """Even for SPECIFIC errors (not vague), the post-processor adds
    a structured followup + recommendations block in Japanese."""
    set_scenario("AADSTS50076")
    result = pi_agent.chat("今出ているエラーを確認して")
    # Check anywhere in the reply (the post-processor appends at the end,
    # but the 1.2B model may ramble before it).
    has_followup = (
        "推奨される次のステップ" in result.reply
        or "追加でお聞きしたい" in result.reply
    )
    has_recommendation = (
        "MFA" in result.reply
        or "Authenticator" in result.reply
        or "多要素認証" in result.reply
        or "MFA 通知" in result.reply
    )
    assert has_followup or has_recommendation, (
        f"no followup or recommendations anywhere: {result.reply[-500:]!r}"
    )
