"""Runtime tests: IT-side agent in KB-ANALYST mode.

The IT agent now uses the it-support skill in "KB analyst" mode:
  - Permitted tools: kb_rg_search, kb_read_knowledge, erp_it_get_ticket,
    erp_it_add_comment (with [Agent P 分析] prefix only).
  - Forbidden: erp_it_resolve_ticket / close / reassign / triage.
    Those are driven by UI action buttons on the IT Operations console.

We seed tickets into erp_state/tickets.json, then call chat_it() and
verify the right tools were called and the reply shape matches the
KB-analyst contract.

Skipped automatically if llama-server is not running.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
TICKETS_STATE = PROJECT_ROOT / "erp_state" / "tickets.json"
ERROR_STATE = PROJECT_ROOT / "erp_state" / "current_error.json"


def _seed_ticket(tid: str = "KW-TEST-001", **overrides) -> dict:
    base = {
        "ticket_id": tid,
        "status": "New",
        "requester": "tester@demo.local",
        "system": "Dynamics 365",
        "error_code": "AADSTS50076",
        "category": "Microsoft Entra ID / MFA / Conditional Access",
        "risk": "Medium",
        "priority": "P3",
        "route": "Identity / Entra ID 管理チーム",
        "impact": "single_user",
        "summary": "test ticket",
        "evidence": [],
        "evidence_summary": "",
        "blocked_actions": ["mfa_disable"],
        "created_at": "2026-06-18T10:00:00Z",
        "history": [{"at": "2026-06-18T10:00:00Z", "action": "created"}],
    }
    base.update(overrides)
    return base


# ── forbidden action tools (chat must NOT call these) ───────────────────

@pytest.mark.parametrize(
    "user_text",
    [
        "KW-3001 を MFA 再設定で対応したので解決マークして",
        "KW-4001 を Closed にアーカイブして",
        "KW-5001 は CRM チームの問題なので CRM Owner に再分派して",
        "KW-6001 をトリアージして",
    ],
)
def test_it_does_not_mutate_ticket_status_from_chat(
    it_agent, llama_url, clean_state, user_text,
):
    """The IT agent must NEVER call resolve/close/reassign/triage tools
    from chat. Status mutations are UI-driven only."""
    TICKETS_STATE.write_text(
        json.dumps({"tickets": [_seed_ticket("KW-3001")]}, ensure_ascii=False)
    )
    result = it_agent.chat_it(user_text)
    forbidden = {
        "erp_it_resolve_ticket", "erp_it_close_ticket",
        "erp_it_reassign_ticket", "erp_it_triage_ticket",
    }
    bad = [ev for ev in result.events if ev.tool in forbidden]
    assert not bad, (
        f"chat should NOT call status-mutating tools. got: {bad}; "
        f"reply={result.reply[:200]!r}"
    )
    # Status on disk must be unchanged
    on_disk = json.loads(TICKETS_STATE.read_text())
    ticket = next(t for t in on_disk["tickets"] if t["ticket_id"] == "KW-3001")
    assert ticket["status"] == "New", f"status changed from chat: {ticket}"


def test_it_redirect_message_mentions_ui_button(it_agent, llama_url, clean_state):
    """When the user asks to resolve a ticket, the chat should
    respond with a clear redirect to the UI action button, in Japanese."""
    TICKETS_STATE.write_text(
        json.dumps({"tickets": [_seed_ticket("KW-3001")]}, ensure_ascii=False)
    )
    result = it_agent.chat_it("KW-3001 を解決して")
    # Either the Python short-circuit (it_action_shortcut) or the
    # model itself should produce a redirect that mentions the
    # UI button. Both are acceptable.
    has_button = "ボタン" in result.reply or "コンソール" in result.reply
    assert has_button, (
        f"reply doesn't mention the UI action button: {result.reply[:200]!r}"
    )


# ── permitted read tools (chat SHOULD call these when relevant) ────────

def test_it_gets_specific_ticket(it_agent, llama_url, clean_state):
    """For a specific ticket id, the agent should call a ticket-lookup
    tool (erp_it_get_ticket) so the analysis is grounded in real data."""
    TICKETS_STATE.write_text(
        json.dumps(
            {"tickets": [_seed_ticket("KW-2001", summary="specific summary marker")]},
            ensure_ascii=False,
        )
    )
    result = it_agent.chat_it("KW-2001 の詳細を見せて")
    called = any(ev.tool == "erp_it_get_ticket" for ev in result.events)
    assert called, f"erp_it_get_ticket not called. events={result.events}"
    assert "KW-2001" in result.reply, f"reply missing ticket id: {result.reply[:300]!r}"


def test_it_searches_kb_on_symptom(it_agent, llama_url, clean_state):
    """When the user pastes a symptom / error code, the agent should
    produce a structured Japanese analysis with KB citations.

    In KB-analyst mode, the kb_rg_search is run in Python (not by the
    LLM) and the result is synthesized by `_direct_it_kb_analysis`.
    We assert on the `it_kb_analysis` event (which carries the hit
    count in its detail) and on the reply shape.
    """
    TICKETS_STATE.write_text(
        json.dumps({"tickets": [_seed_ticket("KW-1001")]}, ensure_ascii=False)
    )
    result = it_agent.chat_it("AADSTS50076 でログインできない原因を教えて")
    # KB search happened (via the short-circuit; could also be a
    # kb_rg_search tool call from the LLM, but in practice the
    # short-circuit always fires when the error code is in the KB).
    kb_evidence = any(
        ev.tool in ("it_kb_analysis", "kb_rg_search")
        for ev in result.events
    )
    assert kb_evidence, f"no KB search event. events={result.events}"
    # Japanese, with a citation
    assert not it_agent._is_mostly_english(result.reply), (
        f"reply is mostly English: {result.reply[:200]!r}"
    )
    assert ".md" in result.reply, (
        f"reply missing KB citation: {result.reply[:300]!r}"
    )


def test_it_japanese_always(it_agent, llama_url, clean_state):
    """The IT agent should always reply in Japanese."""
    TICKETS_STATE.write_text(
        json.dumps({"tickets": [_seed_ticket("KW-7001")]}, ensure_ascii=False)
    )
    result = it_agent.chat_it("KW-7001 を見せて")
    assert not it_agent._is_mostly_english(result.reply), (
        f"reply is mostly English: {result.reply[:200]!r}"
    )