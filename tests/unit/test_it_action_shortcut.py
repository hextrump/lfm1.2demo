"""Unit tests: PiAgentRuntime IT-side action redirect.

In KB-ANALYST mode, `_direct_it_action` no longer mutates ticket state.
It detects the operator's intent (resolve/close/reassign/triage) and
returns a redirect message pointing to the UI action button.

`comment` is the only "soft" intent that falls through (returns None)
so the LLM can choose to add a `[Agent P 分析]` note.
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


# ── intent detection still works (unchanged from old behavior) ────────

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


# ── ticket_id extraction still works (unchanged) ───────────────────────

@pytest.mark.parametrize(
    "text,expected",
    [
        ("KW-1234 を解決して", "KW-1234"),
        ("解決して KW-9267", "KW-9267"),
        ("please resolve KW-5042", "KW-5042"),
        ("KW9999", None),
        ("KW-12", None),
        ("解決して", None),
        ("", None),
    ],
)
def test_extract_it_ticket_id(text, expected):
    r = _agent()
    assert r._extract_it_ticket_id(text) == expected


# ── new behavior: status-mutating intents return a redirect ───────────

def test_direct_it_action_resolve_returns_redirect_not_mutation():
    _seed_ticket(ticket_id="KW-9267", status="Triaged")
    r = _agent()
    result = r._direct_it_action("KW-9267 を解決して")
    assert result is not None
    # Should mention the UI button (not perform the mutation)
    assert "ボタン" in result.reply or "コンソール" in result.reply, (
        f"reply should redirect to UI, got: {result.reply!r}"
    )
    # Event records the redirect
    assert any(ev.tool == "it_action_shortcut" for ev in result.events)
    # Disk state UNCHANGED
    on_disk = json.loads(TICKETS_STATE.read_text())
    target = next(t for t in on_disk["tickets"] if t["ticket_id"] == "KW-9267")
    assert target["status"] == "Triaged", f"status was mutated: {target}"


def test_direct_it_action_close_returns_redirect():
    _seed_ticket(ticket_id="KW-9267", status="Resolved")
    r = _agent()
    result = r._direct_it_action("KW-9267 をクローズして")
    assert result is not None
    assert "ボタン" in result.reply or "コンソール" in result.reply
    on_disk = json.loads(TICKETS_STATE.read_text())
    target = next(t for t in on_disk["tickets"] if t["ticket_id"] == "KW-9267")
    assert target["status"] == "Resolved", f"status was mutated: {target}"


def test_direct_it_action_reassign_returns_redirect():
    _seed_ticket(ticket_id="KW-9267", status="Triaged")
    r = _agent()
    result = r._direct_it_action("KW-9267 を 再分派 Network Team")
    assert result is not None
    assert "ボタン" in result.reply or "コンソール" in result.reply
    on_disk = json.loads(TICKETS_STATE.read_text())
    target = next(t for t in on_disk["tickets"] if t["ticket_id"] == "KW-9267")
    assert target["route"] == "Identity / Entra ID 管理チーム", (
        f"route was mutated: {target}"
    )


def test_direct_it_action_triage_returns_redirect():
    _seed_ticket(ticket_id="KW-9267", status="New")
    r = _agent()
    result = r._direct_it_action("KW-9267 をトリアージして")
    assert result is not None
    assert "ボタン" in result.reply or "コンソール" in result.reply
    on_disk = json.loads(TICKETS_STATE.read_text())
    target = next(t for t in on_disk["tickets"] if t["ticket_id"] == "KW-9267")
    assert target["status"] == "New", f"status was mutated: {target}"


def test_direct_it_action_comment_falls_through_to_llm():
    """Comments are informational, not status-mutating. The short-circuit
    returns None so the LLM can choose to add a [Agent P 分析] note
    or refuse."""
    _seed_ticket(ticket_id="KW-9267", status="Triaged")
    r = _agent()
    # "comment" is the only verb that returns None
    assert r._direct_it_action("KW-9267 にコメント: 進捗確認しました") is None
    assert r._direct_it_action("comment on KW-9267") is None


def test_direct_it_action_no_intent_returns_none():
    """Non-action messages fall through to the LLM path."""
    r = _agent()
    assert r._direct_it_action("今出ているエラーは何ですか") is None
    assert r._direct_it_action("こんにちは") is None
    assert r._direct_it_action("") is None


def test_direct_it_action_redirect_uses_japanese_verb_label():
    """The redirect message labels the action in Japanese so the
    operator can find the right UI button."""
    _seed_ticket(ticket_id="KW-9267")
    r = _agent()
    for verb_en, verb_jp in [
        ("resolve", "解決"),
        ("close", "クローズ"),
        ("reassign", "再分派"),
        ("triage", "トリアージ"),
    ]:
        result = r._direct_it_action(f"KW-9267 を{verb_jp}して")
        assert result is not None
        assert verb_jp in result.reply, (
            f"redirect for {verb_en} should mention {verb_jp!r}, got: {result.reply!r}"
        )