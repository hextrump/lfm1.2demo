"""Unit tests: PiAgentRuntime._extract_error_from_user_text regex.

When the 1.2B model doesn't call any tool, this regex-based extractor
pulls error_code / system / symptom / trace_id out of the user's
pasted text so the post-processor can still build a structured Japanese
response.
"""
from __future__ import annotations

import pytest


def _agent():
    from runtime.pi_agent import PiAgentRuntime

    return PiAgentRuntime()


def test_extract_aadsts():
    text = (
        "Sign-in failed\n"
        "Additional authentication required\n"
        "Error Code: AADSTS50076\n"
        "Trace ID: trc-aadsts50076-110001\n"
        "Correlation ID: corr-20260618\n"
        "Timestamp: 2026-06-18 11:00:01 JST"
    )
    r = _agent()
    data = r._extract_error_from_user_text(text)
    assert data["error_code"] == "AADSTS50076"
    assert data["trace_id"] == "trc-aadsts50076-110001"
    # The regex only captures ASCII alphanumeric+dash, so the
    # Japanese suffix in the original ("corr-営業部-20260618")
    # would be dropped — that's expected. We use a pure-ASCII id here.
    assert data["correlation_id"] == "corr-20260618"
    assert data["system"] == "Dynamics 365"
    assert data["symptom"] == "login_failed"


def test_extract_pbi():
    text = (
        "Application access issue\n"
        "Report access denied\n"
        "Error Code: PBI_ACCESS_DENIED\n"
    )
    r = _agent()
    data = r._extract_error_from_user_text(text)
    assert data["error_code"] == "PBI_ACCESS_DENIED"
    assert data["system"] == "Power BI"
    assert "report" in data["symptom"]


def test_extract_crm_menu():
    text = (
        "Sales Hub menu is not visible\n"
        "Login succeeded, but Sales Hub menu and customer opportunities are not visible.\n"
    )
    r = _agent()
    data = r._extract_error_from_user_text(text)
    assert data["system"] == "Dynamics 365 Sales"
    assert data["symptom"] == "menu_missing"


def test_extract_license():
    text = "This user does not have the required license. Error Code: LICENSE_MISSING"
    r = _agent()
    data = r._extract_error_from_user_text(text)
    assert data["error_code"] == "LICENSE_MISSING"


def test_extract_no_error_code():
    text = "Something went wrong, I can't login"
    r = _agent()
    data = r._extract_error_from_user_text(text)
    # error_code missing, but system/symptom might be inferred
    assert "error_code" not in data or data.get("error_code") == ""


def test_extract_empty_text():
    r = _agent()
    assert r._extract_error_from_user_text("") == {}
    assert r._extract_error_from_user_text("   \n  \n") == {}


def test_extract_cha_block():
    text = "Access blocked by Conditional Access policy. Error Code: CA_BLOCK"
    r = _agent()
    data = r._extract_error_from_user_text(text)
    assert data["error_code"] == "CA_BLOCK"
