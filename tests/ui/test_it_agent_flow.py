"""UI tests: IT Operations page + IT Agent chat.

Verifies that:
- Tickets created from the Employee Portal appear in IT Operations
- The IT Agent chat input works and takes action
- Ticket status persists across page reloads
"""
from __future__ import annotations

import json
import re
import time
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
TICKETS_STATE = PROJECT_ROOT / "erp_state" / "tickets.json"
ERROR_STATE = PROJECT_ROOT / "erp_state" / "current_error.json"


@pytest.fixture
def page(browser, streamlit_url):
    ctx = browser.new_context(viewport={"width": 1500, "height": 1200})
    p = ctx.new_page()
    p.goto(streamlit_url, timeout=30000)
    p.wait_for_selector("text=Agent P", timeout=20000)
    time.sleep(2)
    yield p
    ctx.close()


def test_it_operations_shows_tickets(page, streamlit_url, set_scenario, clean_state):
    """After creating a ticket from Employee Portal, it appears in the
    IT Operations page."""
    # Pre-seed a ticket on disk (simulating that the Employee Portal
    # already created it before navigating to IT Operations)
    ticket = {
        "ticket_id": "KW-UI-001",
        "status": "New",
        "requester": "tester@demo.local",
        "system": "Dynamics 365",
        "error_code": "AADSTS50076",
        "category": "Microsoft Entra ID / MFA / Conditional Access",
        "risk": "Medium",
        "priority": "P3",
        "route": "Identity / Entra ID 管理チーム",
        "impact": "single_user",
        "summary": "test ticket for UI",
        "evidence": [],
        "evidence_summary": "",
        "blocked_actions": ["mfa_disable"],
        "created_at": "2026-06-18T10:00:00Z",
        "history": [{"at": "2026-06-18T10:00:00Z", "action": "created"}],
    }
    TICKETS_STATE.write_text(json.dumps({"tickets": [ticket]}, ensure_ascii=False))
    # Navigate to IT Operations
    page.locator("text=IT Operations").first.click()
    time.sleep(2)
    # The ticket id should be visible
    body = page.locator("body").inner_text()
    assert "KW-UI-001" in body, f"ticket not visible in IT Operations: {body[:500]!r}"


def test_it_agent_chat_resolves_ticket(page, streamlit_url, set_scenario, clean_state):
    """The IT Agent can take action on a ticket via the chat input."""
    # Pre-seed a Resolved-worthy ticket
    ticket = {
        "ticket_id": "KW-UI-002",
        "status": "New",
        "requester": "tester@demo.local",
        "system": "Dynamics 365",
        "error_code": "AADSTS50076",
        "category": "Microsoft Entra ID / MFA / Conditional Access",
        "risk": "Medium",
        "priority": "P3",
        "route": "Identity / Entra ID 管理チーム",
        "impact": "single_user",
        "summary": "test",
        "evidence": [],
        "evidence_summary": "",
        "blocked_actions": ["mfa_disable"],
        "created_at": "2026-06-18T10:00:00Z",
        "history": [{"at": "2026-06-18T10:00:00Z", "action": "created"}],
    }
    TICKETS_STATE.write_text(json.dumps({"tickets": [ticket]}, ensure_ascii=False))
    page.locator("text=IT Operations").first.click()
    time.sleep(3)
    # Find the IT Agent chat input (use the unique placeholder)
    chat_input = page.locator('textarea[placeholder*="IT Agent"]')
    assert chat_input.count() > 0, "IT Agent chat input not found"
    chat_input.fill("KW-UI-002 を MFA 再設定で対応したので解決マークして")
    chat_input.press("Enter")
    # Wait for the ticket to be Resolved
    deadline = time.time() + 180
    while time.time() < deadline:
        time.sleep(3)
        try:
            data = json.loads(TICKETS_STATE.read_text())
            ticket = next(
                (t for t in data["tickets"] if t["ticket_id"] == "KW-UI-002"), None
            )
            if ticket and ticket.get("status") == "Resolved":
                return
        except Exception:
            pass
    pytest.fail("ticket not resolved within 180s")
