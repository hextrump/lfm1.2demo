"""Small offline smoke test for the customer package.

This validates the Python runtime routing and fallback paths without needing a
real Pi binary, npm install, or a running LFM server.
"""
from __future__ import annotations

from dataclasses import dataclass
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tests.mock_pi import MockPi, patch_subprocess  # noqa: E402


@dataclass
class Case:
    name: str
    prompt: str
    must_call: str | None = None
    must_call_any: tuple[str, ...] = ()
    must_not_call: tuple[str, ...] = ()
    require_ticket: bool = False


CASES = [
    Case(
        name="greeting_no_tools",
        prompt="こんにちは",
        must_not_call=("read", "erp_get_current_error", "erp_analyze_pasted_error_with_kb", "erp_create_ticket_from_current_error"),
    ),
    Case(
        name="date_no_tools",
        prompt="こんにちは今日は何の日",
        must_not_call=("read", "erp_get_current_error", "erp_analyze_pasted_error_with_kb", "erp_create_ticket_from_current_error"),
    ),
    Case(
        name="pasted_sso_error",
        prompt="Sign-in failed Additional authentication required Error Code: AADSTS50076 Trace ID: trc-demo Correlation ID: corr-demo",
        must_call="erp_analyze_pasted_error_with_kb",
        must_not_call=("read", "erp_create_ticket_from_current_error"),
    ),
    Case(
        name="current_error",
        prompt="今出ているエラーを確認して",
        must_call_any=("erp_get_current_error", "erp_inspect_current_error_with_kb"),
        must_not_call=("read",),
    ),
    Case(
        name="ticket_request",
        prompt="まだ解決しないのでITに連絡してチケットを作成してください",
        must_call="erp_create_ticket_from_current_error",
        must_not_call=("read",),
        require_ticket=True,
    ),
]


def main() -> int:
    mock = MockPi(mode="ok")
    patch_subprocess(mock)
    from runtime import PiAgentRuntime  # noqa: E402

    runtime = PiAgentRuntime()
    failed = 0

    for case in CASES:
        result = runtime.chat(case.prompt)
        tools = [event.tool for event in result.events if event.status in {"start", "ok", "fallback"}]
        reasons: list[str] = []
        if case.must_call and case.must_call not in tools:
            reasons.append(f"missing {case.must_call}")
        if case.must_call_any and not any(tool in tools for tool in case.must_call_any):
            reasons.append(f"missing one of {case.must_call_any}")
        forbidden = [tool for tool in tools if tool in case.must_not_call]
        if forbidden:
            reasons.append(f"forbidden tools {forbidden}")
        if case.require_ticket and not result.ticket:
            reasons.append("missing ticket")

        if reasons:
            failed += 1
            print(f"FAIL {case.name}: {', '.join(reasons)}")
            print(f"  tools={tools}")
            print(f"  reply={result.reply}")
        else:
            print(f"PASS {case.name}")

    if failed:
        print(f"{len(CASES) - failed}/{len(CASES)} smoke cases passed")
        return 1
    print(f"{len(CASES)}/{len(CASES)} smoke cases passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
