"""UI tests: page loads, chat input, sign-in flow, IT operations.

Uses Playwright + Chromium. Skipped if Streamlit is not running.
"""
from __future__ import annotations

import re
import time
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCREENSHOTS = PROJECT_ROOT / "tests" / "screenshots"


@pytest.fixture
def page(browser, streamlit_url):
    ctx = browser.new_context(viewport={"width": 1500, "height": 1200})
    p = ctx.new_page()
    p.goto(streamlit_url, timeout=30000)
    # Wait for Streamlit to fully render
    p.wait_for_selector("text=Agent P", timeout=20000)
    time.sleep(2)
    yield p
    ctx.close()


def test_page_loads_with_live_tail(page):
    """The initial page renders with the Live Tail Console visible."""
    # Live Tail iframe should be present
    iframes = page.locator("iframe").all()
    has_live_tail = False
    for f in iframes:
        try:
            if f.content_frame and f.content_frame.locator(".live-tail").count() > 0:
                has_live_tail = True
                break
        except Exception:
            pass
    assert has_live_tail, "Live Tail Console not rendered"


def test_signin_and_chat_flow(page, streamlit_url, set_scenario):
    """End-to-end: select scenario → sign in → ask → wait for reply."""
    set_scenario("AADSTS50076")
    # Select scenario
    page.locator('div[data-testid="stSelectbox"]').filter(
        has_text="Inquiry scenario"
    ).first.click()
    time.sleep(0.5)
    page.locator("text=SSO / MFA login failure").first.click()
    time.sleep(1)
    # Sign in
    page.locator('button:has-text("Sign in")').first.click()
    time.sleep(2)
    # Submit a question
    page.locator('textarea[data-testid="stChatInputTextArea"]').fill(
        "今出ているエラーを確認して"
    )
    page.locator('textarea[data-testid="stChatInputTextArea"]').press("Enter")
    # Wait for the reply (1.2B is slow, allow up to 2 min)
    deadline = time.time() + 120
    replied = False
    while time.time() < deadline:
        time.sleep(3)
        try:
            t = page.locator(".chat-text").last.inner_text(timeout=500)
            if t and t != "…" and len(t) > 50:
                replied = True
                break
        except Exception:
            pass
    assert replied, f"no reply within 120s. last text: {t!r}"
    # The reply must mention AADSTS50076
    assert "AADSTS50076" in t, f"reply missing error code: {t[:200]!r}"


def test_no_fake_streaming(page, streamlit_url, set_scenario):
    """The chat bubble shows '…' during inference, then the full reply
    in one shot. We verify the bubble text is either '…' (loading) or
    a complete Japanese answer (not partial characters)."""
    set_scenario("AADSTS50076")
    page.locator('div[data-testid="stSelectbox"]').filter(
        has_text="Inquiry scenario"
    ).first.click()
    time.sleep(0.5)
    page.locator("text=SSO / MFA login failure").first.click()
    time.sleep(1)
    page.locator('button:has-text("Sign in")').first.click()
    time.sleep(2)
    page.locator('textarea[data-testid="stChatInputTextArea"]').fill(
        "今出ているエラーを確認して"
    )
    page.locator('textarea[data-testid="stChatInputTextArea"]').press("Enter")
    # Wait for the reply
    deadline = time.time() + 120
    while time.time() < deadline:
        time.sleep(3)
        try:
            t = page.locator(".chat-text").last.inner_text(timeout=500)
            if t and t != "…" and len(t) > 50:
                # Reply is complete. It should end with a normal character
                # (Japanese period, English period, etc.), not "..."
                assert not t.rstrip().endswith("…"), (
                    f"reply ends with placeholder: {t[-50:]!r}"
                )
                return
        except Exception:
            pass
    pytest.fail("no reply within 120s")


def test_live_tail_shows_events(page, streamlit_url, set_scenario):
    """While the model is running, the Live Tail should show events."""
    set_scenario("AADSTS50076")
    page.locator('div[data-testid="stSelectbox"]').filter(
        has_text="Inquiry scenario"
    ).first.click()
    time.sleep(0.5)
    page.locator("text=SSO / MFA login failure").first.click()
    time.sleep(1)
    page.locator('button:has-text("Sign in")').first.click()
    time.sleep(2)
    page.locator('textarea[data-testid="stChatInputTextArea"]').fill(
        "今出ているエラーを確認して"
    )
    page.locator('textarea[data-testid="stChatInputTextArea"]').press("Enter")
    # Wait for at least one event to appear in Live Tail
    deadline = time.time() + 90
    while time.time() < deadline:
        time.sleep(3)
        for f in page.frames:
            if f != page.main_frame and f.locator(".live-tail").count() > 0:
                try:
                    body = f.locator("#lt-body").inner_text()
                    if "turn" in body or "model" in body or "server" in body:
                        return
                except Exception:
                    pass
    pytest.fail("Live Tail did not show events within 90s")
