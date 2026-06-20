#!/usr/bin/env python3
"""Mine pi-coding-agent session JSONLs into SFT + DPO training rows.

For each session listed in `--sessions-list`:
  * Parse the turn sequence (reusing _session_parser).
  * Emit one SFT row per (user, [tool_call, tool_result, ...], assistant_text)
    subsequence where every tool_call name is in the canonical tool set.
  * Mine DPO rows by detecting observed failure modes in the assistant text:
      - mostly-English reply (ASCII ratio > 0.70)         → "lang" failure
      - wrong/non-canonical tool name                     → "tool" failure
      - no tool call when one was expected                → "no-tool" failure
    Each failure produces a {prompt, chosen, rejected} triple where
    `chosen` is a corrected Japanese reply that references the actual
    toolResult, and `rejected` is the original bad output.

This script is the largest SFT source (~150-300 rows from 166 train sessions).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _session_parser import (  # noqa: E402
    CANONICAL_TOOLS,
    Turn,
    parse_session,
    render_sft_rows,
)


SYSTEM_PROMPT = (
    "You are Agent P, an internal ERP / CRM / SSO support assistant. "
    "You help employees troubleshoot sign-in failures, permission and "
    "license requests, Power BI access, and route unresolved issues to IT "
    "as tickets. Current local date is 2026-06-18 木曜日 in Asia/Tokyo. "
    "LANGUAGE: always respond in Japanese. Keep error codes and product "
    "names (AADSTS50076, Dynamics 365, MFA, etc.) as-is. Use the "
    "available tools when the user asks about an error, ticket, or "
    "knowledge base lookup."
)


def _ascii_ratio(text: str, min_letters: int = 30) -> float:
    """Same heuristic as PiAgentRuntime._is_mostly_english (pi_agent.py:557).

    Returns 0.0 if the text has fewer than `min_letters` alphabetic chars.
    """
    letters = [c for c in text if c.isalpha()]
    if len(letters) < min_letters:
        return 0.0
    ascii_letters = [c for c in letters if ord(c) < 128]
    return len(ascii_letters) / len(letters)


def _looks_like_japanese(text: str) -> bool:
    return any(0x3040 <= ord(c) <= 0x309F or 0x30A0 <= ord(c) <= 0x30FF for c in text)


def _make_chosen_japanese(
    user_text: str,
    tool_results: list[Turn],
) -> str:
    """Build a corrected Japanese reply that references the actual tool data.

    We do NOT try to mimic a specific style — we just want a clean JA reply
    that names the scenario / error code if present. The model learns to
    output Japanese; the exact phrasing is the LoRA's job.
    """
    bits: list[str] = []
    code = ""
    system = ""
    for tr in tool_results:
        # toolResult text is JSON-ish; pull error_code and system out cheaply
        text = tr.text
        for marker in ("AADSTS50076", "AADSTS50105", "LICENSE_MISSING", "CA_BLOCK",
                       "PBI_ACCESS_DENIED", "NO_ERROR_CODE", "MULTI_USER_OUTAGE",
                       "VENDOR_MFA_EXCEPTION"):
            if marker in text:
                code = marker
                break
        if "Dynamics 365" in text:
            system = "Dynamics 365"
        elif "Power BI" in text:
            system = "Power BI"
        elif "Salesforce" in text:
            system = "Salesforce"
    if code:
        bits.append(f"**{code}** ですね。{system or '対象システム'} の状況を確認しました。")
    else:
        bits.append("お問い合わせ内容を確認しました。")
    # Add the user-text echo for traceability (Japanese-friendly paraphrase stub)
    if user_text and not _looks_like_japanese(user_text):
        bits.append(f"ご入力: {user_text[:60]}")
    bits.append("詳細を確認しましたので、次のステップをご提案できます。")
    return "\n\n".join(bits)


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--sessions-list",
        required=True,
        type=Path,
        help="Newline-delimited list of session JSONL paths (output of split_sessions.py)",
    )
    p.add_argument("--out-sft", required=True, type=Path)
    p.add_argument("--out-dpo", required=True, type=Path)
    p.add_argument(
        "--system-prompt",
        default=SYSTEM_PROMPT,
        help="System prompt used for every emitted SFT row",
    )
    return p.parse_args()


def _mine_failure_turns(turns: list[Turn]) -> list[dict]:
    """Walk turns and yield SFT-shaped triples that exhibit failure modes."""
    mined: list[dict] = []
    i = 0
    while i < len(turns):
        t = turns[i]
        if t.kind != "user":
            i += 1
            continue
        user_text = t.text
        # Advance to find the assistant turn(s) in this user window
        j = i + 1
        tool_calls: list[Turn] = []
        tool_results: list[Turn] = []
        assistant_text = ""
        while j < len(turns) and turns[j].kind in ("tool_call", "tool_result", "assistant_text"):
            nxt = turns[j]
            if nxt.kind == "tool_call":
                tool_calls.append(nxt)
            elif nxt.kind == "tool_result":
                tool_results.append(nxt)
            elif nxt.kind == "assistant_text":
                assistant_text = nxt.text
                j += 1
                break
            j += 1

        # Failure mode A: English reply when system prompt demands Japanese
        if assistant_text and _ascii_ratio(assistant_text) > 0.70:
            prompt = [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_text},
            ]
            chosen_text = _make_chosen_japanese(user_text, tool_results)
            mined.append(
                {
                    "prompt": prompt,
                    "chosen": [{"role": "assistant", "content": chosen_text}],
                    "rejected": [{"role": "assistant", "content": assistant_text[:4000]}],
                    "_failure": "lang",
                }
            )

        # Failure mode B: assistant called a non-canonical tool (e.g. `read`)
        if tool_calls and any(tc.tool_name not in CANONICAL_TOOLS for tc in tool_calls):
            prompt = [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_text},
            ]
            # Chosen: a canonical replacement — call erp_get_current_error first
            # when the user is asking about "the current error"
            chosen_text = (
                "<tool_call>\n"
                + json.dumps({"name": "erp_get_current_error", "arguments": {}}, ensure_ascii=False)
                + "\n</tool_call>\n"
                + "現在のエラー状況を確認します。"
            )
            bad_call = next(tc for tc in tool_calls if tc.tool_name not in CANONICAL_TOOLS)
            rejected_text = (
                f"<tool_call>\n"
                + json.dumps({"name": bad_call.tool_name, "arguments": bad_call.arguments or {}}, ensure_ascii=False)
                + "\n</tool_call>"
                + (assistant_text if assistant_text else "")
            )
            mined.append(
                {
                    "prompt": prompt,
                    "chosen": [{"role": "assistant", "content": chosen_text}],
                    "rejected": [{"role": "assistant", "content": rejected_text[:4000]}],
                    "_failure": "tool",
                }
            )

        # Failure mode C: user asked a ticket-creating-style question but
        # assistant never called a tool
        ticket_kw = ("チケット", "問い合わせ", "helpdesk", "ticket")
        wants_ticket = any(k in user_text.lower() for k in ticket_kw)
        if wants_ticket and not tool_calls and assistant_text:
            prompt = [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_text},
            ]
            chosen_text = (
                "<tool_call>\n"
                + json.dumps(
                    {"name": "erp_create_ticket_from_current_error", "arguments": {}},
                    ensure_ascii=False,
                )
                + "\n</tool_call>\n"
                + "IT 部門へのチケット起票を進めます。"
            )
            mined.append(
                {
                    "prompt": prompt,
                    "chosen": [{"role": "assistant", "content": chosen_text}],
                    "rejected": [{"role": "assistant", "content": assistant_text[:4000]}],
                    "_failure": "no-tool",
                }
            )

        # Failure mode D: user mentioned error/ticket keywords but the
        # assistant rambled in text without ever calling any tool. This is
        # the most common failure in our sessions (~62 of 208). Emit two
        # distinct rejection patterns so the model learns to reject BOTH the
        # original rambling text AND a fenced-json hallucination.
        action_kw = (
            "チケット", "問い合わせ", "helpdesk", "ticket",
            "エラー", "error", "aadsts", "サインイン", "sign-in", "sign in",
            "ライセンス", "license", "erp", "crm", "dynamics", "power bi",
        )
        user_wants_action = any(k in user_text.lower() for k in action_kw)
        if user_wants_action and not tool_calls and assistant_text and len(assistant_text) > 80:
            prompt = [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_text},
            ]
            chosen_text = (
                "<tool_call>\n"
                + json.dumps(
                    {
                        "name": "erp_analyze_pasted_error_with_kb",
                        "arguments": {"user_message": user_text},
                    },
                    ensure_ascii=False,
                )
                + "\n</tool_call>\n"
                + "該当のエラーを解析します。"
            )
            mined.append(
                {
                    "prompt": prompt,
                    "chosen": [{"role": "assistant", "content": chosen_text}],
                    "rejected": [{"role": "assistant", "content": assistant_text[:4000]}],
                    "_failure": "no-action-tool",
                }
            )

        # Failure mode E: assistant emitted a fenced ```json ... ``` block
        # instead of the proper `<tool_call>...</tool_call>` envelope.
        if tool_calls and any("```json" in (t.arguments or {}) and False for t in tool_calls):
            pass  # placeholder; the check below uses assistant_text instead
        if tool_calls and not any("```json" in str(t.arguments) for t in tool_calls):
            # We instead check the assistant_text for ```json markers indicating
            # a malformed tool call attempt.
            pass
        if "```json" in assistant_text and tool_calls:
            prompt = [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_text},
            ]
            # Chosen: clean tool envelope; Rejected: the same intent in fenced json
            tc = tool_calls[0]
            chosen_text = (
                f"<tool_call>\n"
                + json.dumps({"name": tc.tool_name, "arguments": tc.arguments or {}}, ensure_ascii=False)
                + "\n</tool_call>"
            )
            rejected_text = "```json\n" + json.dumps(
                {"name": tc.tool_name, "arguments": tc.arguments or {}}, ensure_ascii=False
            ) + "\n```"
            mined.append(
                {
                    "prompt": prompt,
                    "chosen": [{"role": "assistant", "content": chosen_text}],
                    "rejected": [{"role": "assistant", "content": rejected_text}],
                    "_failure": "fenced-json",
                }
            )

        # Failure mode F: assistant called a tool then produced a short /
        # useless reply (< 80 chars) — the model needs to follow up with
        # real Japanese guidance after a tool result, not "OK."
        if tool_calls and assistant_text and 0 < len(assistant_text) < 80:
            prompt = [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_text},
            ]
            chosen_text = (
                f"<tool_call>\n"
                + json.dumps(
                    {"name": tool_calls[0].tool_name, "arguments": tool_calls[0].arguments or {}},
                    ensure_ascii=False,
                )
                + "\n</tool_call>\n"
                + "確認しました。社内 KB と照合し、次のステップをご提案します。"
            )
            mined.append(
                {
                    "prompt": prompt,
                    "chosen": [{"role": "assistant", "content": chosen_text}],
                    "rejected": [{"role": "assistant", "content": assistant_text[:4000]}],
                    "_failure": "short-after-tool",
                }
            )

        i = j if j > i else i + 1

    return mined


def main() -> int:
    args = _parse_args()
    if not args.sessions_list.exists():
        print(f"sessions-list not found: {args.sessions_list}", file=sys.stderr)
        return 2

    files = [Path(line.strip()) for line in args.sessions_list.read_text().splitlines() if line.strip()]
    if not files:
        print(f"no paths in {args.sessions_list}", file=sys.stderr)
        return 2

    args.out_sft.parent.mkdir(parents=True, exist_ok=True)
    args.out_dpo.parent.mkdir(parents=True, exist_ok=True)

    n_sft = 0
    n_dpo = 0
    n_sessions_ok = 0
    n_sessions_skip = 0
    with args.out_sft.open("w", encoding="utf-8") as sft_out, \
         args.out_dpo.open("w", encoding="utf-8") as dpo_out:
        for path in files:
            turns = parse_session(path)
            if not turns:
                n_sessions_skip += 1
                continue
            n_sessions_ok += 1
            for row in render_sft_rows(turns, args.system_prompt):
                sft_out.write(json.dumps(row, ensure_ascii=False) + "\n")
                n_sft += 1
            for failure in _mine_failure_turns(turns):
                # Strip the private _failure key before writing
                dpo_row = {k: v for k, v in failure.items() if not k.startswith("_")}
                dpo_out.write(json.dumps(dpo_row, ensure_ascii=False) + "\n")
                n_dpo += 1

    print(
        f"build_agent_training_data: sessions_ok={n_sessions_ok} skipped={n_sessions_skip} "
        f"sft_rows={n_sft} dpo_rows={n_dpo}",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())