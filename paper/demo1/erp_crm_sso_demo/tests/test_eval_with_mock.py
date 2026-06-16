"""Run the eval suite against a mock Pi runtime.

This validates the Python agent layer (tool profile routing, retry, fallback)
without needing a real `pi` binary, an LFM server, or npm install.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tests.mock_pi import MockPi, patch_subprocess  # noqa: E402
from scripts.eval_agent_p import CASES  # noqa: E402


def run_with_mode(mode: str) -> tuple[int, int]:
    mock = MockPi(mode=mode)
    patch_subprocess(mock)
    from agent_q import PiAgentRuntime  # noqa: E402

    runtime = PiAgentRuntime()
    failed = 0
    for case in CASES:
        result = runtime.chat(case.prompt)
        tools = [event.tool for event in result.events if event.status in {"start", "ok", "fallback"}]
        ok = True
        reasons: list[str] = []
        if case.must_call and case.must_call not in tools:
            ok = False
            reasons.append(f"missing {case.must_call}")
        if case.must_call_any and not any(tool in tools for tool in case.must_call_any):
            ok = False
            reasons.append(f"missing one of {case.must_call_any}")
        forbidden = [tool for tool in tools if tool in case.must_not_call]
        if forbidden:
            ok = False
            reasons.append(f"forbidden tools {forbidden}")
        if case.require_ticket and not result.ticket:
            ok = False
            reasons.append("missing ticket")
        if not ok:
            failed += 1
        status = "PASS" if ok else "FAIL"
        print(f"[{mode:7s}] {status} {case.name}")
        if not ok:
            print(f"           tools: {tools}")
            print(f"           ticket: {result.ticket and result.ticket.get('ticket_id')}")
            print(f"           reasons: {', '.join(reasons)}")
    return failed, len(CASES)


def main() -> int:
    print("=== ok mode (model calls required tool) ===")
    f1, t1 = run_with_mode("ok")
    print(f"\n=== silent mode (model says nothing — fallback must rescue) ===")
    f2, t2 = run_with_mode("silent")
    print(f"\n=== wrong mode (model picks unrelated tool) ===")
    f3, t3 = run_with_mode("wrong")
    print(f"\nresults: ok {t1 - f1}/{t1}, silent {t2 - f2}/{t2}, wrong {t3 - f3}/{t3}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
