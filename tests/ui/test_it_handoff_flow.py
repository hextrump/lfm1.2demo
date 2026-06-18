"""UI tests: full Employee → IT Operations handoff + every IT-side control.

Drives the actual flow in a real headless Chromium browser:
- (a) Employee creates a ticket via Report issue + chat → IT Operations sees it.
- (b)-(e) Inline Triage / Close (two-click) / Apply-status-change expander /
        Add-comment expander drive the code-level mutators in app.py.
- (f)-(g) IT chat input shortcuts via runtime/pi_agent.py chat_it() short-circuit.
- (h) Audit Log page records the manual_triage event.

Mirror patterns from test_it_agent_flow.py (page fixture, IT chat selector,
disk polling) and test_chat_flow.py (Employee sign-in + chat).

Tests marked @pytest.mark.slow require llama-server on :8080. The other
six tests are fast and deterministic via the code-level mutators.
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
TICKETS_STATE = PROJECT_ROOT / "erp_state" / "tickets.json"
ERROR_STATE = PROJECT_ROOT / "erp_state" / "current_error.json"
SCREENSHOTS = PROJECT_ROOT / "tests" / "screenshots"


# ── Fixtures ────────────────────────────────────────────────────────────


@pytest.fixture
def page(browser, streamlit_url):
    """Streamlit Chromium page — same shape as the inline fixture in
    test_it_agent_flow.py:22-30 and test_chat_flow.py:17-26."""
    ctx = browser.new_context(viewport={"width": 1500, "height": 1200})
    p = ctx.new_page()
    p.goto(streamlit_url, timeout=30000)
    p.wait_for_selector("text=Agent P", timeout=20000)
    time.sleep(2)
    yield p
    ctx.close()


# ── Helpers ─────────────────────────────────────────────────────────────


def _seed_ticket(ticket_id: str, status: str = "New", **overrides) -> dict:
    """Write one ticket to tickets.json with sensible defaults for IT-side
    tests. Returns the ticket dict so callers can assert on it later."""
    ticket = {
        "ticket_id": ticket_id,
        "status": status,
        "requester": "tester@demo.local",
        "system": "Dynamics 365",
        "error_code": "AADSTS50076",
        "category": "Microsoft Entra ID / MFA / Conditional Access",
        "risk": "Medium",
        "priority": "P3",
        "route": "Identity / Entra ID 管理チーム",
        "impact": "single_user",
        "summary": "seeded ticket for handoff test",
        "evidence": [],
        "evidence_summary": "",
        "blocked_actions": ["mfa_disable"],
        "created_at": "2026-06-18T10:00:00+0900",
        "history": [{"at": "2026-06-18T10:00:00+0900", "action": "created"}],
    }
    ticket.update(overrides)
    TICKETS_STATE.write_text(
        json.dumps({"tickets": [ticket]}, ensure_ascii=False, indent=2)
    )
    return ticket


def seed_and_open_it(page, ticket_id: str, status: str = "New", **overrides):
    """Seed a ticket on disk, click the IT Operations sidebar entry, and
    wait for the ticket id to appear. Returns the seeded ticket dict."""
    ticket = _seed_ticket(ticket_id, status=status, **overrides)
    page.locator("text=IT Operations").first.click()
    page.wait_for_selector(f"text={ticket_id}", timeout=10000)
    time.sleep(1)  # let the selectbox + buttons mount
    return ticket


def _wait_disk_status(ticket_id: str, expected: str, timeout: float = 30.0):
    """Poll tickets.json until the ticket hits the expected status (or
    timeout). Returns the final ticket dict on success; pytest.fail on
    timeout with the last-seen state in the message."""
    deadline = time.time() + timeout
    last = None
    while time.time() < deadline:
        time.sleep(2)
        try:
            data = json.loads(TICKETS_STATE.read_text())
            t = next(
                (x for x in data["tickets"] if x.get("ticket_id") == ticket_id),
                None,
            )
            if t and t.get("status") == expected:
                return t
            last = t
        except Exception:
            pass
    pytest.fail(
        f"ticket {ticket_id} did not reach status={expected!r} within {timeout}s; "
        f"last={last!r}"
    )


def _screenshot(page, name: str) -> None:
    """Best-effort screenshot. Never fails the test."""
    try:
        SCREENSHOTS.mkdir(parents=True, exist_ok=True)
        page.screenshot(path=str(SCREENSHOTS / f"test_it_handoff_{name}.png"))
    except Exception:
        pass


# ── Tests ───────────────────────────────────────────────────────────────


@pytest.mark.slow
def test_employee_creates_ticket_then_visible_in_it(
    page, streamlit_url, set_scenario, clean_state
):
    """(a) Full Employee → IT handoff: set scenario, sign in, report
    issue, chat to create the ticket, switch to IT Operations, see it."""
    set_scenario("AADSTS50076")
    # Pick scenario from the Inquiry selectbox
    page.locator('div[data-testid="stSelectbox"]').filter(
        has_text="Inquiry scenario"
    ).first.click()
    time.sleep(1)
    page.locator('text="SSO / MFA login failure"').first.click()
    time.sleep(1)
    # Sign in (writes active_error to disk + audit)
    page.locator('button:has-text("Sign in")').first.click()
    time.sleep(2)
    # Report issue (sets active_error state in session)
    page.locator('button:has-text("Report issue")').first.click()
    time.sleep(2)
    # Chat to trigger ticket creation
    chat = page.locator('textarea[data-testid="stChatInputTextArea"]')
    chat.fill("このエラーをチケット起票して")
    chat.press("Enter")
    # Poll for a new ticket to appear (the LLM will call
    # erp_create_ticket_from_current_error)
    deadline = time.time() + 180
    new_id = None
    while time.time() < deadline and new_id is None:
        time.sleep(3)
        try:
            data = json.loads(TICKETS_STATE.read_text())
            ts = data.get("tickets", [])
            if ts:
                new_id = ts[0]["ticket_id"]
        except Exception:
            pass
    _screenshot(page, "a_employee_create")
    assert new_id is not None, "no ticket created within 180s"
    # Switch to IT Operations and assert the ticket id is visible
    page.locator("text=IT Operations").first.click()
    page.wait_for_selector(f"text={new_id}", timeout=15000)
    body = page.locator("body").inner_text()
    assert new_id in body, f"ticket {new_id} not visible in IT Operations body"


def test_inline_triage_button(page, streamlit_url, clean_state):
    """(b) Pre-seed a New ticket → IT Operations → click Triage →
    assert status flips to Triaged on disk and in the UI."""
    seed_and_open_it(page, "KW-IT-001", status="New")
    page.locator('button:has-text("Triage")').first.click()
    t = _wait_disk_status("KW-IT-001", "Triaged", timeout=30)
    _screenshot(page, "b_triage")
    assert t["history"][-1]["action"] == "triaged"
    body = page.locator("body").inner_text()
    assert "Triaged" in body


def test_inline_close_two_click(page, streamlit_url, clean_state):
    """(c) Pre-seed Resolved → click Close → click Confirm close →
    assert status flips to Closed."""
    seed_and_open_it(page, "KW-IT-002", status="Resolved")
    page.locator('button:has-text("Close")').first.click()
    # Wait for the warning + confirm button to appear
    page.wait_for_selector('button:has-text("Confirm close")', timeout=5000)
    page.locator('button:has-text("Confirm close")').first.click()
    t = _wait_disk_status("KW-IT-002", "Closed", timeout=30)
    _screenshot(page, "c_close")
    assert t["history"][-1]["action"] == "closed"


def test_apply_status_change_resolve_with_note(
    page, streamlit_url, clean_state
):
    """(d) Pre-seed Triaged → open Apply-status expander → Resolve →
    type note → Apply → assert Resolved with resolution_note set."""
    seed_and_open_it(page, "KW-IT-003", status="Triaged")
    # Open the expander
    page.locator(
        'details summary:has-text("Apply status change (with note)")'
    ).first.click()
    time.sleep(1)
    # Action selectbox defaults to "Resolve"; just fill the note + Apply
    note = "MFA再登録で対応完了"
    page.locator(
        'textarea[placeholder*="解決内容を入力"]'
    ).first.fill(note)
    page.locator('button:has-text("Apply")').first.click()
    t = _wait_disk_status("KW-IT-003", "Resolved", timeout=30)
    _screenshot(page, "d_apply_resolve")
    assert t.get("resolution_note") == note
    assert t["history"][-1]["action"] == "resolved"


def test_add_comment_expander(page, streamlit_url, clean_state):
    """(e) Pre-seed Triaged → open Add comment expander → type →
    Post → assert comment + history."""
    seed_and_open_it(page, "KW-IT-004", status="Triaged")
    page.locator(
        'details summary:has-text("Add comment")'
    ).first.click()
    time.sleep(1)
    comment_text = "ユーザに折り返し連絡済み"
    page.locator(
        'textarea[placeholder*="コメントを入力"]'
    ).first.fill(comment_text)
    page.locator('button:has-text("Post comment")').first.click()
    # Poll for the comment to land on disk
    deadline = time.time() + 20
    last = None
    while time.time() < deadline:
        time.sleep(2)
        try:
            data = json.loads(TICKETS_STATE.read_text())
            t = next(
                (x for x in data["tickets"] if x["ticket_id"] == "KW-IT-004"),
                None,
            )
            if t and t.get("comments"):
                last = t
                if t["comments"][-1]["comment"] == comment_text:
                    break
        except Exception:
            pass
    _screenshot(page, "e_comment")
    assert last is not None and last["comments"][-1]["comment"] == comment_text
    assert last["history"][-1]["action"] == "comment"


@pytest.mark.slow
def test_chat_shortcut_resolve(page, streamlit_url, clean_state):
    """(f) Pre-seed Triaged → IT Operations → type 'KW-IT-005 を解決して'
    in IT chat → assert Resolved. Mirrors test_it_agent_flow.py:65-107
    which proves the chat shortcut path works."""
    seed_and_open_it(page, "KW-IT-005", status="Triaged")
    chat = page.locator('textarea[placeholder*="IT Agent"]')
    chat.fill("KW-IT-005 を解決して")
    chat.press("Enter")
    t = _wait_disk_status("KW-IT-005", "Resolved", timeout=180)
    _screenshot(page, "f_chat_resolve")
    assert t["history"][-1]["action"] == "resolved"
    # The IT chat panel should have an assistant bubble mentioning the id
    body = page.locator("body").inner_text()
    assert "KW-IT-005" in body


def test_chat_shortcut_missing_ticket_id(page, streamlit_url, clean_state):
    """(g) No seeded tickets → click IT Operations → type '解決して' →
    assert reply asks for a ticket id."""
    # clean_state guarantees tickets.json = []
    page.locator("text=IT Operations").first.click()
    # Wait for the "No tickets yet" info to render
    page.wait_for_selector(
        'text="No tickets yet. Create one from Employee Portal."',
        timeout=10000,
    )
    chat = page.locator('textarea[placeholder*="IT Agent"]')
    chat.fill("解決して")
    chat.press("Enter")
    # The shortcut returns a help message immediately (no LLM call).
    # Wait for the assistant bubble.
    deadline = time.time() + 30
    reply_text = ""
    while time.time() < deadline:
        time.sleep(2)
        try:
            bubbles = page.locator('.stChatMessage [data-testid="stMarkdownContainer"]')
            if bubbles.count() > 0:
                # Take the last bubble's text
                reply_text = bubbles.last.inner_text()
                if reply_text:
                    break
        except Exception:
            pass
    _screenshot(page, "g_chat_missing")
    assert "チケットID" in reply_text, f"reply did not mention ticket id: {reply_text!r}"
    assert "KW-####" in reply_text, f"reply did not mention KW-####: {reply_text!r}"


def test_audit_log_records_manual_triage(page, streamlit_url, clean_state):
    """(h) Pre-seed New → click Triage → navigate to Audit Log →
    assert row with agent='IT Operations Agent' + action='manual_triage'
    + ticket id is visible in the audit dataframe."""
    seed_and_open_it(page, "KW-IT-006", status="New")
    page.locator('button:has-text("Triage")').first.click()
    _wait_disk_status("KW-IT-006", "Triaged", timeout=30)
    # Wait for the rerun to complete + add_audit to land in session_state
    time.sleep(2)
    # Navigate to Audit Log via the sidebar menu
    page.locator("text=Audit Log").first.click()
    # Give the page time to rerender and load the dataframe
    time.sleep(3)
    # The audit log is rendered as an st.dataframe which uses a glide data-grid.
    # The cells have data-testid="glide-cell-{col}-{row}".
    cells = page.locator('[data-testid^="glide-cell"]').all()
    cell_texts = [c.inner_text() for c in cells]
    df_text = "\n".join(cell_texts)
    _screenshot(page, "h_audit")
    assert "IT Operations Agent" in df_text, (
        f"audit row missing 'IT Operations Agent'; df_text:\n{df_text!r}"
    )
    assert "manual_triage" in df_text, (
        f"audit row missing 'manual_triage'; df_text:\n{df_text!r}"
    )
    assert "KW-IT-006" in df_text, (
        f"audit row missing ticket id; df_text:\n{df_text!r}"
    )