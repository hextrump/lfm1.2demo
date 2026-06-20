#!/usr/bin/env python3
"""Convert pi_agent.py's parametrized unit tests into SFT training rows.

For each `@pytest.mark.parametrize` block in the registered test files, this
script invokes the live `runtime.pi_agent.PiAgentRuntime` method that the
test is asserting on, captures the gold reply, and emits a ChatML row.

Each test function has a registered `oracle` in `TEST_REGISTRY` that knows
how to translate (parametrize args) → (system_prompt, user_text, assistant_text).
Oracles are either:
  - "canned" : call a `_direct_basic_reply`-family method and use its reply
  - "scenario": call `_scenario_recommendations(code, symptom)` and emit bullets
  - "it_action": emit a tool-call envelope for the matched verb
  - "structured_paste": render a structured Japanese reply for a pasted error

This script produces data/_tests_sft.jsonl (~80-150 rows) that covers the
exact short-circuit behaviors we want the model to internalize.
"""

from __future__ import annotations

import argparse
import ast
import json
import sys
from pathlib import Path
from typing import Any, Callable, Iterable

# Make sibling modules importable when run directly
sys.path.insert(0, str(Path(__file__).resolve().parent))
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from runtime.pi_agent import PiAgentRuntime  # noqa: E402


SYSTEM_PROMPT_DEFAULT = (
    "You are Agent P, an internal ERP / CRM / SSO support assistant. "
    "Always respond in Japanese. Keep error codes and product names "
    "(AADSTS50076, Dynamics 365, MFA, etc.) as-is."
)


# ── Oracles ────────────────────────────────────────────────────────────

def _agent() -> PiAgentRuntime:
    return PiAgentRuntime()


def oracle_canned_direct(q: str, **_unused: Any) -> dict | None:
    """Use _direct_basic_reply(q) as the gold reply. Returns None if no
    short-circuit matched (the test would have failed; we skip the row).

    Accepts arbitrary additional kwargs (e.g. `lang`, `expected_keyword`)
    because different tests parametrize with different trailing args.
    """
    reply = _agent()._direct_basic_reply(q)
    if not reply:
        return None
    return {"user": q, "assistant": reply}


def oracle_scenario_recs(code: str, symptom: str, **_unused: Any) -> dict | None:
    """Render _scenario_recommendations(code, symptom) as a Japanese reply."""
    recs = _agent()._scenario_recommendations(code, symptom)
    if not recs:
        return None
    user = f"Error Code: {code} (症状: {symptom}) の対応について教えてください。"
    assistant = "**推奨される次のステップ:**\n\n" + "\n".join(recs[:4])
    return {"user": user, "assistant": assistant}


def oracle_it_action(text: str, expected: str | None, **_unused: Any) -> dict | None:
    """For IT-verb detection tests. Emit an SFT row showing the model should
    call the corresponding erp_it_* tool. Returns None when expected is None
    (negative case — the model should NOT call any tool)."""
    if expected is None:
        return None
    tool_map = {
        "resolve": "erp_it_resolve_ticket",
        "close": "erp_it_close_ticket",
        "reassign": "erp_it_reassign_ticket",
        "triage": "erp_it_triage_ticket",
        "comment": "erp_it_add_comment",
    }
    tool = tool_map.get(expected)
    if not tool:
        return None
    args: dict[str, Any] = {}
    if expected == "comment":
        args = {"comment": text}
    elif expected == "reassign":
        # Reassign demos: assume the verb+target pattern; the model just calls the tool
        args = {"ticket_id": "", "new_route": "IT Operations"}
    else:
        args = {"ticket_id": ""}
    envelope = json.dumps({"name": tool, "arguments": args}, ensure_ascii=False)
    assistant = (
        f"<tool_call>\n{envelope}\n</tool_call>\n"
        f"承知しました。{expected} の処理を実行します。対象チケットIDを教えてください。"
    )
    return {"user": text, "assistant": assistant}


def oracle_structured_paste(pasted_text: str, code: str, system: str,
                            symptom: str) -> dict | None:
    """Render a structured Japanese reply from a pasted error block.

    Mirrors the shape produced by `_build_response_block` (pi_agent.py:592)
    but inlined here so the SFT data is independent of the post-processor.
    """
    from runtime.pi_agent import PiAgentRuntime as _P
    data = _P._extract_error_from_user_text(pasted_text)
    if not data:
        return None
    actual_code = data.get("error_code") or code
    actual_system = data.get("system") or system
    actual_symptom = data.get("symptom") or symptom
    if not actual_code and not actual_system:
        return None
    user = pasted_text
    bullets = _P._scenario_recommendations(actual_code, actual_symptom)
    parts = [
        f"**{actual_code or '不明'}** に関するお問い合わせですね。",
        f"{actual_system or '対象システム'} で発生しているエラーを確認しました。",
        "",
        "**追加でお聞きしたいこと:**",
        "",
        "1. 部署名・役職・業務への影響範囲",
        "2. 最後に正常に動作していた時期",
        "3. このエラーは再現しますか?",
    ]
    if bullets:
        parts.extend([
            "",
            "**推奨される次のステップ:**",
            "",
            *bullets[:4],
        ])
    return {"user": user, "assistant": "\n".join(parts)}


# ── Registry: test_id → (system_prompt, oracle) ────────────────────────

TEST_REGISTRY: dict[str, Callable[..., dict | None]] = {
    # tests/unit/test_direct_reply.py
    "test_identity_short_circuit": oracle_canned_direct,
    "test_capability_short_circuit": oracle_canned_direct,
    "test_greeting_short_circuit": oracle_canned_direct,
    "test_date_short_circuit": oracle_canned_direct,
    # tests/runtime/test_chat_identity.py
    "test_identity_question_returns_agent_p": oracle_canned_direct,
    "test_capability_question": oracle_canned_direct,
    "test_greeting": oracle_canned_direct,
    "test_date": oracle_canned_direct,
    # tests/unit/test_it_action_shortcut.py
    "test_user_wants_it_action": oracle_it_action,
    # tests/unit/test_language_and_recs.py
    "test_scenario_recommendations": oracle_scenario_recs,
}


# ── AST walk ───────────────────────────────────────────────────────────

def _iter_parametrize_rows(pyfile: Path) -> Iterable[tuple[str, dict[str, Any]]]:
    """Yield (test_name, kwargs_dict) for each parametrize block."""
    try:
        tree = ast.parse(pyfile.read_text(encoding="utf-8"))
    except SyntaxError as exc:
        print(f"  skip {pyfile}: {exc}", file=sys.stderr)
        return
    for node in ast.walk(tree):
        if not isinstance(node, ast.FunctionDef):
            continue
        for dec in node.decorator_list:
            if not isinstance(dec, ast.Call):
                continue
            func = dec.func
            attr = getattr(func, "attr", "") or getattr(func, "id", "")
            if attr != "parametrize":
                continue
            if len(dec.args) < 2:
                continue
            try:
                argnames = ast.literal_eval(dec.args[0])
                argvalues = ast.literal_eval(dec.args[1])
            except (ValueError, SyntaxError):
                continue
            names = [n.strip() for n in argnames.split(",")]
            if not isinstance(argvalues, list):
                continue
            for vals in argvalues:
                if not isinstance(vals, tuple):
                    vals = (vals,)
                if len(vals) != len(names):
                    continue
                yield node.name, dict(zip(names, vals))


def _row_from_test(
    test_name: str,
    kwargs: dict[str, Any],
    system_prompt: str,
) -> dict[str, Any] | None:
    oracle = TEST_REGISTRY.get(test_name)
    if oracle is None:
        return None
    try:
        result = oracle(**kwargs)
    except Exception as exc:  # noqa: BLE001 — oracle must not crash the loop
        print(f"  oracle {test_name} raised: {exc}", file=sys.stderr)
        return None
    if not result:
        return None
    return {
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": result["user"]},
            {"role": "assistant", "content": result["assistant"]},
        ]
    }


# ── Hard-coded test rows for non-parametrize tests (test_error_parser.py) ──

PASTE_TEST_ROWS = [
    # (pasted_text, code, system, symptom)
    (
        "Sign-in failed\nAdditional authentication required\n"
        "Error Code: AADSTS50076\nTrace ID: trc-aadsts50076-110001\n"
        "Correlation ID: corr-20260618",
        "AADSTS50076",
        "Dynamics 365",
        "login_failed",
    ),
    (
        "Application access issue\nReport access denied\nError Code: PBI_ACCESS_DENIED",
        "PBI_ACCESS_DENIED",
        "Power BI",
        "report_permission_denied",
    ),
    (
        "Sales Hub menu is not visible\nLogin succeeded, but Sales Hub menu and "
        "customer opportunities are not visible.",
        "NO_ERROR_CODE",
        "Dynamics 365 Sales",
        "menu_missing",
    ),
    (
        "This user does not have the required license. Error Code: LICENSE_MISSING",
        "LICENSE_MISSING",
        "Dynamics 365",
        "license_missing",
    ),
    (
        "Access blocked by Conditional Access policy. Error Code: CA_BLOCK",
        "CA_BLOCK",
        "Dynamics 365",
        "conditional_access_block",
    ),
]


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--tests",
        nargs="+",
        type=Path,
        default=[PROJECT_ROOT / "tests" / "unit", PROJECT_ROOT / "tests" / "runtime"],
        help="Directories or files to scan for @pytest.mark.parametrize blocks",
    )
    p.add_argument("--out", required=True, type=Path)
    p.add_argument(
        "--system-prompt",
        default=SYSTEM_PROMPT_DEFAULT,
        help="System prompt used for every emitted SFT row",
    )
    return p.parse_args()


def _walk_tests(paths: list[Path]) -> Iterable[Path]:
    for p in paths:
        if p.is_file():
            yield p
        elif p.is_dir():
            yield from sorted(p.rglob("test_*.py"))


def main() -> int:
    args = _parse_args()
    files = list(_walk_tests(args.tests))
    args.out.parent.mkdir(parents=True, exist_ok=True)

    n_rows = 0
    skipped_unknown = 0
    skipped_oracle = 0
    with args.out.open("w", encoding="utf-8") as out:
        for path in files:
            for test_name, kwargs in _iter_parametrize_rows(path):
                row = _row_from_test(test_name, kwargs, args.system_prompt)
                if row is None:
                    if test_name not in TEST_REGISTRY:
                        skipped_unknown += 1
                    else:
                        skipped_oracle += 1
                    continue
                out.write(json.dumps(row, ensure_ascii=False) + "\n")
                n_rows += 1

        # Hard-coded structured-paste rows (from test_error_parser.py)
        for pasted_text, code, system, symptom in PASTE_TEST_ROWS:
            result = oracle_structured_paste(pasted_text, code, system, symptom)
            if result is None:
                skipped_oracle += 1
                continue
            out.write(
                json.dumps(
                    {
                        "messages": [
                            {"role": "system", "content": args.system_prompt},
                            {"role": "user", "content": result["user"]},
                            {"role": "assistant", "content": result["assistant"]},
                        ]
                    },
                    ensure_ascii=False,
                )
                + "\n"
            )
            n_rows += 1

    print(
        f"extract_tests_to_sft: rows={n_rows} "
        f"unknown_test={skipped_unknown} oracle_returned_none={skipped_oracle}",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())