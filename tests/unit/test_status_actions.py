"""Unit tests: IT Operations inline status action mutators.

Covers the 5 new ticket mutators in app.py (triage_ticket, resolve_ticket,
close_ticket, reassign_ticket, add_comment_to_ticket).

These tests use the real streamlit module — the warning
"missing ScriptRunContext" is expected when importing app.py outside a
running Streamlit script. The mutators themselves only touch
st.session_state.tickets and TICKETS_DISK_PATH, neither of which needs a
live script context.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

# Import app.py — emits "missing ScriptRunContext" warnings which are safe
import app  # noqa: E402

from tests.conftest import TICKETS_STATE  # noqa: E402


# ── Helpers ────────────────────────────────────────────────────────────


def _seed_ticket(**overrides) -> dict:
    """Write a single ticket to TICKETS_STATE and return the dict."""
    base = {
        "ticket_id": "KW-TEST-001",
        "status": "New",
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


def _read_ticket(ticket_id: str) -> dict | None:
    data = json.loads(TICKETS_STATE.read_text())
    return next(
        (t for t in data.get("tickets", []) if t.get("ticket_id") == ticket_id),
        None,
    )


def _set_session_tickets(tickets: list[dict]) -> None:
    import streamlit as st

    st.session_state["tickets"] = list(tickets)


# ── Tests ─────────────────────────────────────────────────────────────


def test_triage_new_ticket_changes_status_to_triaged():
    _seed_ticket(status="New")
    _set_session_tickets([_read_ticket("KW-TEST-001")])

    ok, msg, new_t = app.triage_ticket("KW-TEST-001", notes="manual")

    assert ok is True, msg
    assert new_t["status"] == "Triaged"
    assert new_t["triage_notes"] == "manual"
    assert new_t["triaged_at"]
    # Disk and session state agree
    disk = _read_ticket("KW-TEST-001")
    assert disk["status"] == "Triaged"
    import streamlit as st

    assert st.session_state["tickets"][0]["status"] == "Triaged"


def test_triage_rejects_non_new_status():
    _seed_ticket(status="Triaged")
    _set_session_tickets([_read_ticket("KW-TEST-001")])

    ok, msg, new_t = app.triage_ticket("KW-TEST-001", notes="again")

    assert ok is False
    assert "New" in msg
    assert new_t is None
    # Status unchanged on disk
    assert _read_ticket("KW-TEST-001")["status"] == "Triaged"


def test_resolve_writes_resolution_note_and_history():
    _seed_ticket(status="New")
    _set_session_tickets([_read_ticket("KW-TEST-001")])

    ok, msg, new_t = app.resolve_ticket("KW-TEST-001", "再ログインで回復")

    assert ok is True, msg
    disk = _read_ticket("KW-TEST-001")
    assert disk["status"] == "Resolved"
    assert disk["resolution_note"] == "再ログインで回復"
    assert disk["resolved_at"]
    # History shape byte-for-byte matches TS tool
    last = disk["history"][-1]
    assert set(last.keys()) == {"at", "action", "note"}
    assert last["action"] == "resolved"
    assert last["note"] == "再ログインで回復"


def test_resolve_rejects_empty_note():
    _seed_ticket(status="New")
    _set_session_tickets([_read_ticket("KW-TEST-001")])

    ok, msg, new_t = app.resolve_ticket("KW-TEST-001", "   ")

    assert ok is False
    assert "解決内容" in msg
    assert new_t is None
    assert _read_ticket("KW-TEST-001")["status"] == "New"


def test_resolve_rejects_closed_ticket():
    _seed_ticket(status="Closed")
    _set_session_tickets([_read_ticket("KW-TEST-001")])

    ok, msg, _ = app.resolve_ticket("KW-TEST-001", "note")

    assert ok is False
    assert "Closed" in msg


def test_close_writes_close_note():
    _seed_ticket(status="Resolved")
    _set_session_tickets([_read_ticket("KW-TEST-001")])

    ok, msg, new_t = app.close_ticket("KW-TEST-001", close_note="verified")

    assert ok is True, msg
    disk = _read_ticket("KW-TEST-001")
    assert disk["status"] == "Closed"
    assert disk["close_note"] == "verified"
    assert disk["closed_at"]
    last = disk["history"][-1]
    assert last["action"] == "closed"
    assert last["note"] == "verified"


def test_reassign_changes_route_and_writes_history_with_to_field():
    _seed_ticket(status="Triaged")
    _set_session_tickets([_read_ticket("KW-TEST-001")])

    ok, msg, new_t = app.reassign_ticket(
        "KW-TEST-001", "Network Team", reason="escalated"
    )

    assert ok is True, msg
    disk = _read_ticket("KW-TEST-001")
    assert disk["route"] == "Network Team"
    assert disk["reassign_reason"] == "escalated"
    last = disk["history"][-1]
    assert set(last.keys()) == {"at", "action", "to", "note"}
    assert last["action"] == "reassigned"
    assert last["to"] == "Network Team"
    assert last["note"] == "escalated"


def test_reassign_rejects_empty_route():
    _seed_ticket(status="Triaged")
    _set_session_tickets([_read_ticket("KW-TEST-001")])

    ok, msg, _ = app.reassign_ticket("KW-TEST-001", "", reason="x")

    assert ok is False
    assert "new_route" in msg or "担当" in msg


def test_add_comment_appends_to_comments_and_history():
    _seed_ticket(status="New")
    _set_session_tickets([_read_ticket("KW-TEST-001")])

    ok, msg, new_t = app.add_comment_to_ticket(
        "KW-TEST-001", "follow-up scheduled"
    )

    assert ok is True, msg
    disk = _read_ticket("KW-TEST-001")
    assert len(disk["comments"]) == 1
    c = disk["comments"][0]
    assert c["comment"] == "follow-up scheduled"
    assert c["author"] == "IT Operations Agent P (manual)"
    assert c["at"]
    last = disk["history"][-1]
    assert last["action"] == "comment"
    assert last["note"] == "follow-up scheduled"


def test_add_comment_rejects_empty():
    _seed_ticket(status="New")
    _set_session_tickets([_read_ticket("KW-TEST-001")])

    ok, msg, _ = app.add_comment_to_ticket("KW-TEST-001", "  ")

    assert ok is False
    assert "コメント" in msg


def test_mutator_refreshes_session_state_in_place():
    """_sync_session_state_ticket must update in place (no reorder)."""
    # Write both tickets to disk in a single shot
    TICKETS_STATE.write_text(json.dumps({
        "tickets": [
            {**_seed_ticket(ticket_id="KW-A", status="New"), "_from_helper": True},
            {**_seed_ticket(ticket_id="KW-B", status="Triaged"), "_from_helper": True},
        ][0:1]  # need to write both — workaround below
    }, ensure_ascii=False, indent=2))
    # Cleaner: just write both directly
    a = {
        "ticket_id": "KW-A", "status": "New",
        "requester": "tester@demo.local", "system": "X",
        "category": "Y", "priority": "P3", "route": "R",
        "impact": "single_user", "summary": "s", "trace_id": "t",
        "evidence": [], "blocked_actions": [],
        "created_at": "2026-06-18T10:00:00+0900",
        "history": [{"at": "2026-06-18T10:00:00+0900", "action": "created"}],
    }
    b = {**a, "ticket_id": "KW-B", "status": "Triaged"}
    TICKETS_STATE.write_text(json.dumps({"tickets": [a, b]}, ensure_ascii=False, indent=2))
    _set_session_tickets([a, b])

    # Triage KW-A (status is New) — should succeed and update in place.
    ok, _, _ = app.triage_ticket("KW-A", notes="mutator test")
    assert ok

    import streamlit as st

    # Order preserved: KW-A still index 0, KW-B still index 1.
    assert st.session_state["tickets"][0]["ticket_id"] == "KW-A"
    assert st.session_state["tickets"][0]["status"] == "Triaged"
    assert st.session_state["tickets"][1]["ticket_id"] == "KW-B"
    assert st.session_state["tickets"][1]["status"] == "Triaged"


def test_unknown_ticket_returns_error():
    TICKETS_STATE.write_text(json.dumps({"tickets": []}))
    _set_session_tickets([])

    ok, msg, new_t = app.triage_ticket("KW-MISSING")

    assert ok is False
    assert "見つかりません" in msg
    assert new_t is None