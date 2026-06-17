"""End-to-end smoke test that does not require a running LFM server.

Verifies that the imports resolve, the agent layer can route prompts to the
correct tool profile, the eval cases pass under a mocked Pi, and the training
data is well-formed.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP_DIR))

from tests.mock_pi import MockPi, patch_subprocess  # noqa: E402


def check_imports() -> None:
    from runtime import PiAgentRuntime
    from scripts import eval_agent_p
    from scripts import build_agent_training_data
    from scripts import train_lora  # noqa: F401
    print("imports ok")


def check_training_data() -> None:
    for name in ("agent_p_sft.jsonl", "agent_p_dpo.jsonl"):
        path = APP_DIR / "training_data" / name
        if not path.exists():
            print(f"warn: {name} not found, skipping")
            continue
        rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
        assert rows, f"{name} is empty"
        if name == "agent_p_sft.jsonl":
            for row in rows:
                assert "messages" in row, f"SFT row missing messages: {row}"
                roles = {m.get("role") for m in row["messages"]}
                assert {"system", "user", "assistant"}.issubset(roles), f"SFT row missing roles: {row}"
        else:
            for row in rows:
                assert {"prompt", "chosen", "rejected"}.issubset(row), f"DPO row missing keys: {row}"
        print(f"{name}: {len(rows)} rows ok")


def check_eval_with_mock() -> None:
    from scripts.eval_agent_p import CASES

    mock = MockPi(mode="ok")
    patch_subprocess(mock)
    from runtime import PiAgentRuntime

    runtime = PiAgentRuntime()
    failed = 0
    for case in CASES:
        result = runtime.chat(case.prompt)
        tools = [event.tool for event in result.events if event.status in {"start", "ok", "fallback"}]
        ok = True
        if case.must_call and case.must_call not in tools:
            ok = False
        if case.must_call_any and not any(t in tools for t in case.must_call_any):
            ok = False
        if any(t in case.must_not_call for t in tools):
            ok = False
        if case.require_ticket and not result.ticket:
            ok = False
        if not ok:
            failed += 1
            print(f"  FAIL {case.name}: tools={tools}")
    print(f"eval: {len(CASES) - failed}/{len(CASES)} pass")
    if failed:
        raise SystemExit(1)


def check_audit_data() -> None:
    from runtime.pi_agent import SCENARIOS, ERP_INTENT_PATTERNS, TICKET_INTENT_PATTERNS

    assert len(SCENARIOS) >= 6, f"expected >=6 scenarios, got {len(SCENARIOS)}"
    assert "aadsts" in " ".join(ERP_INTENT_PATTERNS).lower()
    assert any("チケット" in p or "ticket" in p.lower() for p in TICKET_INTENT_PATTERNS)
    print(f"scenarios: {len(SCENARIOS)}, ERP patterns: {len(ERP_INTENT_PATTERNS)}, ticket patterns: {len(TICKET_INTENT_PATTERNS)}")


def main() -> None:
    print("=== smoke test ===")
    check_imports()
    check_training_data()
    check_audit_data()
    check_eval_with_mock()
    print("=== all checks passed ===")


if __name__ == "__main__":
    main()
