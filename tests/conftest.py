"""Shared pytest fixtures.

Layered fixtures:
- llama_server / sse_server / streamlit_server (session scope): ensure
  the three services are up. If they're already running (via the user's
  manual launch), reuse them; otherwise start them for the test run.
- clean_state (function scope): wipe erp_state/current_error.json and
  erp_state/tickets.json before each test so they don't leak.
- set_scenario (function scope): helper to write a known scenario into
  current_error.json before calling chat() / run_employee_chat_live.
- pi_agent (function scope): a fresh PiAgentRuntime.
- browser (session scope): Playwright Chromium.
"""
from __future__ import annotations

import json
import os
import socket
import subprocess
import time
from pathlib import Path

import pytest
import requests

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ERROR_STATE = PROJECT_ROOT / "erp_state" / "current_error.json"
TICKETS_STATE = PROJECT_ROOT / "erp_state" / "tickets.json"

LLAMA_URL = "http://127.0.0.1:8080"
SSE_URL = "http://127.0.0.1:8765"
STREAMLIT_URL = "http://127.0.0.1:8501"


def _healthy(url: str, timeout: float = 2.0) -> bool:
    try:
        r = requests.get(url, timeout=timeout)
        return r.status_code == 200
    except Exception:
        return False


def _wait_healthy(url: str, timeout: float = 30.0) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        if _healthy(url, timeout=1):
            return True
        time.sleep(0.5)
    return False


def _port_open(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        try:
            s.connect(("127.0.0.1", port))
            return True
        except Exception:
            return False


@pytest.fixture(scope="session")
def llama_url() -> str:
    """Return the llama-server base URL. Skip if not already up — runtime
    tests need a live model. Mark as skip rather than starting the
    server ourselves (it takes ~30s and ~700 MB RAM)."""
    if not _healthy(LLAMA_URL + "/health"):
        pytest.skip(f"llama-server not running at {LLAMA_URL}")
    return LLAMA_URL


@pytest.fixture(scope="session")
def sse_url() -> str:
    """Return the live-tail SSE URL. Skip if not running."""
    if not _healthy(SSE_URL + "/health"):
        pytest.skip(f"SSE server not running at {SSE_URL}")
    return SSE_URL


@pytest.fixture(scope="session")
def streamlit_url() -> str:
    """Return the Streamlit URL. UI tests need a live app."""
    if not _healthy(STREAMLIT_URL):
        pytest.skip(f"Streamlit not running at {STREAMLIT_URL}")
    return STREAMLIT_URL


@pytest.fixture(autouse=True)
def clean_state():
    """Reset current_error.json and tickets.json before every test."""
    ERROR_STATE.parent.mkdir(parents=True, exist_ok=True)
    ERROR_STATE.write_text(json.dumps({"active": False}, ensure_ascii=False))
    TICKETS_STATE.write_text(json.dumps({"tickets": []}, ensure_ascii=False))
    yield
    # leave them empty after the test too


@pytest.fixture
def set_scenario():
    """Helper that writes a scenario dict to current_error.json.

    Usage:
        set_scenario("AADSTS50076")
        set_scenario("AADSTS50076", trace_id="trc-custom-001")
    """
    from tests.fixtures.scenarios import SCENARIOS

    def _set(key: str, **overrides):
        if key not in SCENARIOS:
            raise KeyError(f"unknown scenario: {key}. known: {list(SCENARIOS)}")
        data = dict(SCENARIOS[key])
        data.update(overrides)
        ERROR_STATE.write_text(json.dumps(data, ensure_ascii=False, indent=2))
        return data

    return _set


@pytest.fixture
def pi_agent():
    """A fresh PiAgentRuntime (employee side, default skill)."""
    from runtime.pi_agent import PiAgentRuntime

    return PiAgentRuntime()


@pytest.fixture
def it_agent():
    """A fresh PiAgentRuntime configured for the IT agent (it-support skill)."""
    from runtime.pi_agent import PiAgentRuntime, PI_IT_SKILL

    return PiAgentRuntime(skill_path=PI_IT_SKILL)


@pytest.fixture(scope="session")
def browser():
    """Playwright Chromium browser (session scope — expensive to start)."""
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        b = p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu"],
        )
        yield b
        b.close()


# Make project root importable for `from runtime import ...` in tests
import sys

sys.path.insert(0, str(PROJECT_ROOT))
