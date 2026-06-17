#!/usr/bin/env python3
"""End-to-end browser test for the Agent P demo.

Drives a real Chromium browser against the running Streamlit app at
http://127.0.0.1:8501, simulates human interaction (clicking the scenario
selector, typing a question, hitting send), and captures screenshots of
the Live Tail Console + chat at every meaningful state.

Screenshots are written to tests/screenshots/ as PNG files.

Prereqs:
  - Streamlit running on 127.0.0.1:8501
  - llama-server running on 127.0.0.1:8080
  - Live tail SSE server running on 127.0.0.1:8765
  - Playwright + Chromium installed (./.venv/bin/python -m playwright install chromium)
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright, Page, TimeoutError as PWTimeout

URL = "http://127.0.0.1:8501"
SCREENSHOT_DIR = Path(__file__).resolve().parent / "screenshots"


def shot(page: Page, name: str) -> Path:
    """Take a full-page screenshot and return its path."""
    SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
    path = SCREENSHOT_DIR / f"{name}.png"
    page.screenshot(path=str(path), full_page=True)
    print(f"  📸 {path.name}  ({path.stat().st_size // 1024} KB)")
    return path


def wait_for_streamlit_ready(page: Page, timeout_s: int = 30) -> None:
    """Wait for Streamlit to finish initial render.

    Streamlit renders a loading state with id 'stAppLoaderContainer' and
    removes it when the app is interactive.
    """
    print("  ⏳ waiting for Streamlit to be ready...")
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        try:
            visible = page.locator("#stAppLoaderContainer").is_visible(timeout=500)
        except PWTimeout:
            visible = False
        if not visible:
            # Also wait for the Employee Portal title to confirm
            try:
                page.wait_for_selector("text=Employee Portal", timeout=2000)
                return
            except PWTimeout:
                continue
        time.sleep(0.5)
    raise RuntimeError(f"Streamlit did not become ready within {timeout_s}s")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--question", default="今出ているエラーを確認して")
    parser.add_argument("--scenario", default="AADSTS50076",
                        help="Scenario key (AADSTS50076 / POWERBI_DENIED / ...)")
    parser.add_argument("--wait-llm", type=int, default=60,
                        help="Seconds to wait for LLM reply (1.2B Tool is slow)")
    args = parser.parse_args()

    SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        # Use a real (headed) browser if DISPLAY available; otherwise headless
        # is fine. WSL has a virtual display via WSLg, so try headed first.
        launch_kwargs = dict(
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu"],
        )
        browser = p.chromium.launch(**launch_kwargs)
        context = browser.new_context(
            viewport={"width": 1400, "height": 900},
            locale="ja-JP",
        )
        page = context.new_page()
        page.set_default_timeout(15000)

        print(f"→ opening {URL}")
        page.goto(URL)
        wait_for_streamlit_ready(page, timeout_s=30)
        # Give Live Tail iframe a moment to subscribe + receive the first line
        time.sleep(2)
        shot(page, "01_initial_load")
        print("  ✓ page loaded, initial screenshot saved")

        # ── 1. Select a scenario ───────────────────────────────────────────
        print(f"→ selecting scenario: {args.scenario}")
        try:
            # The selectbox label is "Inquiry scenario"
            page.locator('div[data-testid="stSelectbox"]').filter(
                has_text="Inquiry scenario"
            ).first.click()
            time.sleep(0.5)
            # Click the option in the dropdown
            page.locator(f"text={args.scenario}").first.click()
            time.sleep(1)
            shot(page, "02_scenario_selected")
            print("  ✓ scenario selected")
        except Exception as e:
            print(f"  ⚠ could not select scenario via UI ({e}); using default")
            shot(page, "02_scenario_selected_fallback")

        # ── 2. Type the question and submit ────────────────────────────────
        print(f"→ typing question: {args.question!r}")
        chat_input = page.locator('textarea[data-testid="stChatInputTextArea"]')
        chat_input.click()
        chat_input.fill(args.question)
        time.sleep(0.3)
        shot(page, "03_question_typed")
        chat_input.press("Enter")
        print("  ✓ submitted, waiting for LLM...")

        # ── 3. Wait for the response (the slow part) ───────────────────────
        # Streamlit chat shows "You: <question>" then "Agent P: <reply>".
        # Wait for the agent reply to appear.
        try:
            page.wait_for_selector(
                f'text="{args.question[:30]}"', timeout=10000
            )
        except PWTimeout:
            print("  ⚠ question text not found in chat history; continuing")
        # The reply may take 25-45s on a 1.2B model. Poll for the assistant
        # message that has substantive text (not just "...").
        deadline = time.time() + args.wait_llm
        last_shot = 0
        while time.time() < deadline:
            time.sleep(3)
            # Take a screenshot every ~10s so we can see progress
            now = time.time()
            if now - last_shot > 10:
                shot(page, f"04_during_inference_{int(now - (deadline - args.wait_llm))}s")
                last_shot = now
            # Check for completion: look for the "done" event in the live tail
            # (most reliable signal that the model has finished)
            try:
                body_text = page.locator("body").inner_text(timeout=1000)
                if "[done]" in body_text and "✓ done" in body_text:
                    print("  ✓ Live Tail shows 'done' event — inference complete")
                    break
            except (PWTimeout, Exception):
                continue
        else:
            print(f"  ⚠ LLM did not finish within {args.wait_llm}s; capturing anyway")

        # ── 4. Final screenshot ───────────────────────────────────────────
        time.sleep(2)  # let the live tail settle
        shot(page, "05_final_state")
        print("  ✓ final state captured")

        # ── 5. Diagnostics: extract what we see ───────────────────────────
        print("\n=== Diagnostics ===")
        # Find the live tail element
        lt_body = page.locator(".live-tail-body").first
        if lt_body.count() > 0:
            lt_text = lt_body.inner_text()
            line_count = len([l for l in lt_text.splitlines() if l.strip()])
            print(f"  Live Tail: {line_count} lines visible")
            print(f"  --- last 5 lines ---")
            for line in lt_text.splitlines()[-5:]:
                print(f"    {line}")
        else:
            print("  ⚠ no .live-tail-body element found")
        # Find chat messages
        chat_rows = page.locator(".chat-row").all()
        print(f"  Chat rows: {len(chat_rows)}")
        for i, row in enumerate(chat_rows[-4:]):
            text = row.inner_text()[:120].replace("\n", " | ")
            print(f"    [{i}] {text}")

        browser.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
