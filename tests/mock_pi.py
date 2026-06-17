"""Mock Pi runtime for offline testing of the Python agent layer.

This lets us exercise the tool-profile routing, retry logic, and fallback
behavior without needing the real `pi` binary or an LFM server. It simulates
the JSON event stream that Pi would emit in `--mode json`.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from runtime import PiAgentRuntime  # noqa: E402
from runtime.pi_agent import (  # noqa: E402
    PiAgentEvent,
    PiAgentResult,
    ERP_INTENT_PATTERNS,
    TICKET_INTENT_PATTERNS,
)


class MockPi:
    """Test double that injects deterministic tool calls instead of running the LFM.

    Each chat() invocation returns a PiAgentResult containing a planned sequence
    of tool execution events based on the tool profile the runtime picks. The
    caller can flip `mode` between "ok", "silent", and "wrong" to exercise
    different code paths.
    """

    def __init__(self, mode: str = "ok") -> None:
        self.mode = mode
        self.last_command: list[str] | None = None

    def run(self, command: list[str], cwd: Path, env: dict, timeout: int) -> dict:
        self.last_command = command
        tool_profile = self._profile_from_command(command)
        events, final_reply, ticket, evidence = self._plan_response(tool_profile)
        return {
            "stdout": "\n".join(json.dumps(ev) for ev in events + [{"type": "agent_end", "messages": [{"role": "assistant", "content": [{"type": "text", "text": final_reply}]}]}]),
            "stderr": "",
            "returncode": 0,
        }

    def _profile_from_command(self, command: list[str]) -> str:
        if "--no-tools" in command:
            return "none"
        for i, arg in enumerate(command):
            if arg == "--tools" and i + 1 < len(command):
                tools = command[i + 1].split(",")
                if "erp_create_ticket_from_current_error" in tools and len(tools) == 1:
                    return "erp_ticket"
                if "erp_analyze_pasted_error_with_kb" in tools and len(tools) == 1:
                    return "erp_analysis"
                if "erp_get_current_error" in tools:
                    return "erp_current_error"
        return "all"

    def _plan_response(self, profile: str) -> tuple[list[dict], str, dict | None, list[dict]]:
        if self.mode == "silent":
            return [], "了解しました。", None, []
        if self.mode == "wrong":
            return [
                {"type": "tool_execution_start", "toolName": "read", "args": {"path": "/tmp"}},
                {"type": "tool_execution_end", "toolName": "read", "isError": False, "result": {"content": [{"text": "{}"}]}},
            ], "ファイルを読みました。", None, []
        if profile == "none":
            return [], "こんにちは。直接回答します。", None, []
        if profile == "erp_analysis":
            return [
                {
                    "type": "tool_execution_start",
                    "toolName": "erp_analyze_pasted_error_with_kb",
                    "args": {"user_message": "pasted"},
                },
                {
                    "type": "tool_execution_end",
                    "toolName": "erp_analyze_pasted_error_with_kb",
                    "isError": False,
                    "result": {
                        "content": [{"text": json.dumps({
                            "scenario_key": "AADSTS50076",
                            "category": "Microsoft Entra ID / MFA / Conditional Access",
                            "system": "Dynamics 365",
                            "error_code": "AADSTS50076",
                            "route": "Identity / Entra ID 管理チーム",
                            "priority": "P3",
                            "evidence": [{"path": "knowledge/sso/entra-id-login-errors.md", "line": 12, "snippet": "AADSTS50076"}],
                        })}],
                        "details": {
                            "scenario_key": "AADSTS50076",
                            "category": "Microsoft Entra ID / MFA / Conditional Access",
                            "system": "Dynamics 365",
                            "error_code": "AADSTS50076",
                            "route": "Identity / Entra ID 管理チーム",
                            "priority": "P3",
                            "evidence": [{"path": "knowledge/sso/entra-id-login-errors.md", "line": 12, "snippet": "AADSTS50076"}],
                        },
                    },
                },
            ], "エラーを分析しました。担当は Identity / Entra ID 管理チームです。", None, [{"path": "knowledge/sso/entra-id-login-errors.md", "line": 12, "snippet": "AADSTS50076"}]
        if profile == "erp_current_error":
            return [
                {"type": "tool_execution_start", "toolName": "erp_get_current_error", "args": {}},
                {
                    "type": "tool_execution_end",
                    "toolName": "erp_get_current_error",
                    "isError": False,
                    "result": {
                        "content": [{"text": json.dumps({"active": True, "scenario_key": "AADSTS50076", "system": "Dynamics 365", "error_code": "AADSTS50076", "error_text": "MFA required"}) }],
                        "details": {"active": True, "scenario_key": "AADSTS50076", "system": "Dynamics 365", "error_code": "AADSTS50076", "error_text": "MFA required"},
                    },
                },
            ], "現在のエラーは AADSTS50076 / Dynamics 365 です。", None, []
        if profile == "erp_ticket":
            return [
                {"type": "tool_execution_start", "toolName": "erp_create_ticket_from_current_error", "args": {"user_message": "pasted"}},
                {
                    "type": "tool_execution_end",
                    "toolName": "erp_create_ticket_from_current_error",
                    "isError": False,
                    "result": {
                        "content": [{"text": json.dumps({"ticket_id": "KW-1234", "route": "Identity / Entra ID 管理チーム", "priority": "P3", "system": "Dynamics 365", "error_code": "AADSTS50076", "category": "Microsoft Entra ID / MFA / Conditional Access", "impact": "single_user", "summary": "MFA required", "evidence": [], "blocked_actions": ["password_reset"]}) }],
                        "details": {"ticket_id": "KW-1234", "route": "Identity / Entra ID 管理チーム", "priority": "P3", "system": "Dynamics 365", "error_code": "AADSTS50076", "category": "Microsoft Entra ID / MFA / Conditional Access", "impact": "single_user", "summary": "MFA required", "evidence": [], "blocked_actions": ["password_reset"]},
                    },
                },
            ], "チケット KW-1234 を作成しました。", {
                "ticket_id": "KW-1234",
                "route": "Identity / Entra ID 管理チーム",
                "priority": "P3",
                "system": "Dynamics 365",
                "error_code": "AADSTS50076",
                "category": "Microsoft Entra ID / MFA / Conditional Access",
                "impact": "single_user",
                "summary": "MFA required",
                "evidence": [],
                "blocked_actions": ["password_reset"],
            }, []
        return [], "fallback", None, []


def patch_subprocess(mock: MockPi) -> None:
    """Monkey-patch subprocess.run in the runtime.pi_agent module."""
    import subprocess
    from runtime import pi_agent

    def fake_run(command, *args, **kwargs):
        result = mock.run(command, kwargs.get("cwd") or Path("."), kwargs.get("env") or {}, kwargs.get("timeout") or 0)
        class R:
            def __init__(self, d):
                self.stdout = d["stdout"]
                self.stderr = d["stderr"]
                self.returncode = d["returncode"]
        return R(result)

    pi_agent.subprocess.run = fake_run
    pi_agent.PiAgentRuntime.chat.__wrapped__ = None  # noop
    # Make available() return True for the mock
    original_init = pi_agent.PiAgentRuntime.__init__

    def patched_init(self, *a, **k):
        original_init(self, *a, **k)
        # Override the path checks for the test
        self._mock_skip_check = True

    pi_agent.PiAgentRuntime.__init__ = patched_init
    original_available = pi_agent.PiAgentRuntime.available

    def patched_available(self):
        return True

    pi_agent.PiAgentRuntime.available = patched_available


def main() -> int:
    mock = MockPi(mode="ok")
    patch_subprocess(mock)
    runtime = PiAgentRuntime()
    cases = [
        "こんにちは",
        "こんにちは今日は何の日",
        "Dynamics 365 に入れません。AADSTS50076",
        "今出ているエラーを確認して",
        "まだ解決しないのでITに連絡してチケットを作成してください",
    ]
    for prompt in cases:
        result = runtime.chat(prompt)
        tools = [e.tool for e in result.events if e.status in {"start", "ok", "fallback"}]
        print(f"{prompt[:50]:50s} -> tools={tools}  reply={result.reply[:60]!r}  ticket={result.ticket and result.ticket.get('ticket_id')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
