"""Unit tests: PiAgentRuntime IT-side action short-circuits.

Mirrors test_direct_reply.py — tests the pure-Python interception in
chat_it() that detects resolve/close/reassign/triage/comment intents and
calls the Python mutator directly, bypassing the 1.2B model.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from tests.conftest import TICKETS_STATE  # noqa: E402


def _agent():
    from runtime.pi_agent import PiAgentRuntime

    return PiAgentRuntime()


def _seed_ticket(**overrides) -> dict:
    base = {
        "ticket_id": "KW-TEST-001",
        "status": "Triaged",
        "requester": "tester@demo.local",
        "system": "Dynamics 365",
        "category": "Microsoft Entra ID / MFA",
        "priority": "P3",
        "route": "Identity / Entra ID 管理チーム",
        "impact": "single_user",
        "summary": "test ticket",
        "trace_id": "trc-test-001",
        "evidence": [],
        "blocked_actions": [],
        "created_at": "2026-06-18T10:00:00+0900",
        "history": [{"at": "2026-06-18T10:00:00+0900", "action": "created"}],
    }
    base.update(overrides)
    TICKETS_STATE.write_text(
        json.dumps({"tickets": [base]}, ensure_ascii=False, indent=2)
    )
    return base


def _set_session_tickets(tickets: list[dict]) -> None:
    import streamlit as st
    st.session_state["tickets"] = list(tickets)


# ── intent detection ────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "text,expected",
    [
        ("解決して", "resolve"),
        ("解決してください", "resolve"),
        ("resolve", "resolve"),
        ("Resolved にして", "resolve"),
        ("クローズして", "close"),
        ("閉じる", "close"),
        ("close", "close"),
        ("再分派", "reassign"),
        ("担当変更", "reassign"),
        ("reassign", "reassign"),
        ("トリアージして", "triage"),
        ("triage", "triage"),
        ("コメント", "comment"),
        ("comment", "comment"),
        ("评论", "comment"),
        # Negative — not an action verb
        ("今出ているエラーは何ですか", None),
        ("最近のチケットを見せて", None),
        ("こんにちは", None),
        ("", None),
    ],
)
def test_user_wants_it_action(text, expected):
    r = _agent()
    assert r._user_wants_it_action(text) == expected


# ── ticket_id extraction ────────────────────────────────────────────────


@pytest.mark.parametrize(
    "text,expected",
    [
        ("KW-1234 を解決して", "KW-1234"),
        ("解決して KW-9267", "KW-9267"),
        ("please resolve KW-5042", "KW-5042"),
        ("KW9999", None),  # missing dash
        ("KW-12", None),  # too short
        ("解決して", None),
        ("", None),
    ],
)
def test_extract_it_ticket_id(text, expected):
    r = _agent()
    assert r._extract_it_ticket_id(text) == expected


# ── full short-circuit flow ────────────────────────────────────────────


def test_direct_it_action_resolve_with_explicit_ticket_id():
    _seed_ticket(ticket_id="KW-9267", status="Triaged")
    _set_session_tickets([json.loads(TICKETS_STATE.read_text())["tickets"][0]])

    r = _agent()
    result = r._direct_it_action("KW-9267 を解決して")

    assert result is not None
    assert "KW-9267" in result.reply
    assert "解決" in result.reply
    # Disk should be updated
    disk = json.loads(TICKETS_STATE.read_text())
    target = next(t for t in disk["tickets"] if t["ticket_id"] == "KW-9267")
    assert target["status"] == "Resolved"
    # History shape preserved
    last = target["history"][-1]
    assert last["action"] == "resolved"


def test_direct_it_action_resolve_uses_selected_ticket_fallback():
    """If no KW-#### in text, fall back to st.session_state.selected_it_ticket."""
    _seed_ticket(ticket_id="KW-5042", status="Triaged")
    _set_session_tickets([json.loads(TICKETS_STATE.read_text())["tickets"][0]])

    import streamlit as st
    st.session_state["selected_it_ticket"] = "KW-5042"

    r = _agent()
    result = r._direct_it_action("解決して")

    assert result is not None
    assert "KW-5042" in result.reply
    disk = json.loads(TICKETS_STATE.read_text())
    target = next(t for t in disk["tickets"] if t["ticket_id"] == "KW-5042")
    assert target["status"] == "Resolved"


def test_direct_it_action_close():
    _seed_ticket(ticket_id="KW-9267", status="Resolved")
    _set_session_tickets([json.loads(TICKETS_STATE.read_text())["tickets"][0]])

    r = _agent()
    result = r._direct_it_action("KW-9267 をクローズして")

    assert result is not None
    disk = json.loads(TICKETS_STATE.read_text())
    target = next(t for t in disk["tickets"] if t["ticket_id"] == "KW-9267")
    assert target["status"] == "Closed"


def test_direct_it_action_reassign_extracts_route():
    _seed_ticket(ticket_id="KW-9267", status="Triaged")
    _set_session_tickets([json.loads(TICKETS_STATE.read_text())["tickets"][0]])

    r = _agent()
    # Verb pattern + new route after it
    result = r._direct_it_action("KW-9267 を 再分派 Network Team")

    assert result is not None
    disk = json.loads(TICKETS_STATE.read_text())
    target = next(t for t in disk["tickets"] if t["ticket_id"] == "KW-9267")
    assert target["route"] == "Network Team"
    last = target["history"][-1]
    assert last["action"] == "reassigned"
    assert last["to"] == "Network Team"


def test_direct_it_action_triage():
    _seed_ticket(ticket_id="KW-9267", status="New")
    _set_session_tickets([json.loads(TICKETS_STATE.read_text())["tickets"][0]])

    r = _agent()
    result = r._direct_it_action("KW-9267 をトリアージして")

    assert result is not None
    disk = json.loads(TICKETS_STATE.read_text())
    target = next(t for t in disk["tickets"] if t["ticket_id"] == "KW-9267")
    assert target["status"] == "Triaged"


def test_direct_it_action_comment():
    _seed_ticket(ticket_id="KW-9267", status="Triaged")
    _set_session_tickets([json.loads(TICKETS_STATE.read_text())["tickets"][0]])

    r = _agent()
    result = r._direct_it_action("KW-9267 にコメント: 進捗確認しました")

    assert result is not None
    disk = json.loads(TICKETS_STATE.read_text())
    target = next(t for t in disk["tickets"] if t["ticket_id"] == "KW-9267")
    assert len(target["comments"]) == 1
    assert "進捗確認" in target["comments"][0]["comment"]
    assert target["history"][-1]["action"] == "comment"


def test_direct_it_action_no_intent_returns_none():
    """Non-action messages fall through to the LLM path."""
    r = _agent()
    assert r._direct_it_action("今出ているエラーは何ですか") is None
    assert r._direct_it_action("こんにちは") is None
    assert r._direct_it_action("") is None


def test_direct_it_action_no_ticket_id_returns_help_message():
    """Action verb without any ticket id (and no selected_ticket fallback)
    returns a clear Japanese help message instead of guessing."""
    # Make sure session state has no selected ticket
    import streamlit as st
    st.session_state.pop("selected_it_ticket", None)
    st.session_state["tickets"] = []

    r = _agent()
    result = r._direct_it_action("解決して")

    assert result is not None
    assert "チケットID" in result.reply
    assert "KW-####" in result.reply


def test_direct_it_action_rejects_close_on_already_closed():
    """Close on a Closed ticket returns the mutator's error message."""
    _seed_ticket(ticket_id="KW-9267", status="Closed")
    _set_session_tickets([json.loads(TICKETS_STATE.read_text())["tickets"][0]])

    r = _agent()
    result = r._direct_it_action("KW-9267 をクローズして")

    assert result is not None
    # The shortcut should NOT pretend success — surface the mutator error
    assert "失敗" in result.reply or "できません" in result.reply


def test_direct_it_action_events_record_correctly():
    """The PiAgentResult.events list records the action for the audit log."""
    _seed_ticket(ticket_id="KW-9267", status="Triaged")
    _set_session_tickets([json.loads(TICKETS_STATE.read_text())["tickets"][0]])

    r = _agent()
    result = r._direct_it_action("KW-9267 を解決して")

    assert result is not None
    assert len(result.events) == 1
    ev = result.events[0]
    assert ev.tool == "erp_it_resolve_ticket"
    assert ev.status == "ok"