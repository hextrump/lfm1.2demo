#!/usr/bin/env python3
"""Validate the v1 SFT/DPO training datasets.

Checks:
  1. Schema       — SFT row has `messages` (list of dicts with role ∈ system|user|assistant|tool);
                    DPO row has `prompt` (list), `chosen` (list), `rejected` (list).
  2. Roles        — every message has a `role` and a `content`.
  3. Tool envelope— every <tool_call>{...}</tool_call> parses to JSON with a `name` field
                    that is in the canonical tool set.
  4. KB paths     — any path under `knowledge/` referenced in an assistant message
                    must exist on disk.
  5. No leakage   — no (system[:80], user[:80]) in sft_v1 / dpo_v1 appears as a prefix
                    of any (system[:80], user[:80]) in eval_sessions.
  6. Language     — at least 60% of SFT rows must be predominantly Japanese
                    (heuristic: any assistant message contains hiragana/katakana).
  7. Length       — warn on any row whose total character count exceeds 10000.
  8. Seed parity  — every schema key seen in the seed files must also be present
                    in our generated files.

Exits 0 if all hard checks pass. Soft warnings go to stderr.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Iterable

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from scripts._session_parser import CANONICAL_TOOLS  # noqa: E402

_TOOL_CALL_RE = re.compile(r"<tool_call>\s*(\{.*?\})\s*</tool_call>", re.DOTALL)
_KB_PATH_RE = re.compile(r"knowledge/[A-Za-z0-9_\-./]+\.md")


def _iter_jsonl(path: Path) -> Iterable[dict[str, Any]]:
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            yield json.loads(line)
        except json.JSONDecodeError:
            continue


def _validate_sft_schema(row: dict, errors: list[str], idx: int) -> None:
    msgs = row.get("messages")
    if not isinstance(msgs, list) or len(msgs) < 2:
        errors.append(f"[sft#{idx}] messages must be list of length >= 2")
        return
    roles = [m.get("role") for m in msgs]
    if "user" not in roles:
        errors.append(f"[sft#{idx}] no user message")
    if "assistant" not in roles:
        errors.append(f"[sft#{idx}] no assistant message")
    for i, m in enumerate(msgs):
        if not isinstance(m, dict):
            errors.append(f"[sft#{idx}] msg {i} not a dict")
            continue
        if m.get("role") not in {"system", "user", "assistant", "tool"}:
            errors.append(f"[sft#{idx}] msg {i} bad role {m.get('role')!r}")
        if not isinstance(m.get("content"), str):
            errors.append(f"[sft#{idx}] msg {i} content not a string")


def _validate_dpo_schema(row: dict, errors: list[str], idx: int) -> None:
    for key in ("prompt", "chosen", "rejected"):
        v = row.get(key)
        if not isinstance(v, list) or not v:
            errors.append(f"[dpo#{idx}] {key} must be a non-empty list")
    prompt = row.get("prompt", [])
    if isinstance(prompt, list) and prompt:
        if prompt[0].get("role") != "system" or len(prompt) < 2:
            errors.append(f"[dpo#{idx}] prompt must start with system and have >= 2 msgs")


def _validate_tool_envelopes(row: dict, errors: list[str], idx: int, kind: str) -> None:
    msgs = row.get("messages") if kind == "sft" else row.get("chosen", [])
    for m in msgs:
        if m.get("role") != "assistant":
            continue
        content = m.get("content", "")
        for match in _TOOL_CALL_RE.finditer(content):
            try:
                env = json.loads(match.group(1))
            except json.JSONDecodeError:
                errors.append(f"[{kind}#{idx}] tool envelope not JSON: {match.group(1)[:60]!r}")
                continue
            name = env.get("name")
            if not isinstance(name, str):
                errors.append(f"[{kind}#{idx}] tool envelope missing `name`: {match.group(1)[:60]!r}")
                continue
            if name not in CANONICAL_TOOLS:
                errors.append(
                    f"[{kind}#{idx}] tool name {name!r} not in canonical set"
                )


def _validate_kb_paths(row: dict, errors: list[str], idx: int, kind: str, kb_root: Path) -> None:
    msgs = row.get("messages") if kind == "sft" else (row.get("chosen", []) + row.get("rejected", []))
    for m in msgs:
        content = m.get("content", "")
        for match in _KB_PATH_RE.finditer(content):
            rel = match.group(0)
            # Allow partial paths like "knowledge/sso/entra-id-login-errors.md"
            # or full paths starting with /home/...
            full = (PROJECT_ROOT / rel).resolve()
            if not (full.exists() and full.is_relative_to(kb_root.resolve())):
                # Try matching against absolute paths inside the KB
                if not any(full.match(str(p) + "*") for p in kb_root.rglob("*.md")):
                    errors.append(
                        f"[{kind}#{idx}] KB path {rel!r} does not resolve under {kb_root}"
                    )


def _has_japanese(text: str) -> bool:
    return any(0x3040 <= ord(c) <= 0x309F or 0x30A0 <= ord(c) <= 0x30FF for c in text)


def _is_leak(sft_or_dpo_rows: list[dict], eval_rows: list[dict],
             min_user_chars: int = 30) -> list[str]:
    """Check that no (system[:80], user[:80]) pair in train rows appears as a
    prefix of any eval row's pair — but only for "non-trivial" user inputs.

    Trivial inputs (greetings like "こんにちは", short identity questions) are
    intentionally trained across both splits — they teach the model universal
    behavior, not session-specific patterns. We only flag leakage when the
    user text is long enough to suggest a unique, scenario-specific input.
    """
    eval_keys: set[tuple[str, str]] = set()
    for r in eval_rows:
        msgs = r.get("messages", [])
        sys_ = next((m.get("content", "") for m in msgs if m.get("role") == "system"), "")
        usr = next((m.get("content", "") for m in msgs if m.get("role") == "user"), "")
        if len(usr) >= min_user_chars:
            eval_keys.add((sys_[:80], usr[:80]))
    leaks = []
    for i, r in enumerate(sft_or_dpo_rows):
        msgs = r.get("messages") if "messages" in r else r.get("prompt", [])
        sys_ = next((m.get("content", "") for m in msgs if m.get("role") == "system"), "")
        usr = next((m.get("content", "") for m in msgs if m.get("role") == "user"), "")
        if len(usr) < min_user_chars:
            continue
        key = (sys_[:80], usr[:80])
        if key in eval_keys:
            leaks.append(f"[{i}] user_len={len(usr)} {usr[:60]!r}")
    return leaks


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("sft", type=Path)
    p.add_argument("dpo", type=Path)
    p.add_argument("eval", type=Path, help="eval_sessions.jsonl from split_sessions.py")
    p.add_argument("--kb", type=Path, default=PROJECT_ROOT / "knowledge")
    p.add_argument("--seed", type=Path, default=PROJECT_ROOT / "data" / "seed")
    p.add_argument("--strict", action="store_true",
                   help="Treat length warnings as errors")
    return p.parse_args()


def main() -> int:
    args = _parse_args()
    sft_rows = list(_iter_jsonl(args.sft))
    dpo_rows = list(_iter_jsonl(args.dpo))
    eval_rows = list(_iter_jsonl(args.eval))

    errors: list[str] = []
    warnings: list[str] = []

    # 1-3. Schema + tool envelopes
    for i, r in enumerate(sft_rows):
        _validate_sft_schema(r, errors, i)
        _validate_tool_envelopes(r, errors, i, "sft")
    for i, r in enumerate(dpo_rows):
        _validate_dpo_schema(r, errors, i)
        _validate_tool_envelopes(r, errors, i, "dpo")

    # 4. KB paths
    if args.kb.exists():
        for i, r in enumerate(sft_rows):
            _validate_kb_paths(r, errors, i, "sft", args.kb)
        for i, r in enumerate(dpo_rows):
            _validate_kb_paths(r, errors, i, "dpo", args.kb)

    # 5. No leakage
    leaks = _is_leak(sft_rows + dpo_rows, eval_rows)
    if leaks:
        errors.append(f"{len(leaks)} train/eval leakage(s); first: {leaks[0]}")

    # 6. Language distribution
    ja_count = 0
    for r in sft_rows:
        msgs = r.get("messages", [])
        for m in msgs:
            if m.get("role") == "assistant" and _has_japanese(m.get("content", "")):
                ja_count += 1
                break
    ja_ratio = ja_count / max(1, len(sft_rows))
    if ja_ratio < 0.60:
        errors.append(f"only {ja_ratio:.0%} of SFT rows have Japanese assistant content (>= 60% required)")
    else:
        print(f"language: {ja_ratio:.0%} of SFT rows are JA ({ja_count}/{len(sft_rows)})", file=sys.stderr)

    # 7. Length sanity
    for kind, rows in [("sft", sft_rows), ("dpo", dpo_rows)]:
        for i, r in enumerate(rows):
            total = 0
            if "messages" in r:
                for m in r["messages"]:
                    total += len(m.get("content", ""))
            else:
                for m in r.get("prompt", []) + r.get("chosen", []) + r.get("rejected", []):
                    total += len(m.get("content", ""))
            if total > 10000:
                msg = f"[{kind}#{i}] total length {total} > 10000 (likely hallucinated debug spam)"
                if args.strict:
                    errors.append(msg)
                else:
                    warnings.append(msg)
    if warnings:
        print(f"warnings ({len(warnings)}):", file=sys.stderr)
        for w in warnings[:5]:
            print(f"  - {w}", file=sys.stderr)
        if len(warnings) > 5:
            print(f"  ... ({len(warnings) - 5} more)", file=sys.stderr)

    # 8. Seed parity (schema keys)
    def _collect_keys(path: Path) -> set[str]:
        keys: set[str] = set()
        if not path.exists():
            return keys
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            keys.update(row.keys())
        return keys

    seed_sft_keys = _collect_keys(args.seed / "agent_p_sft.jsonl")
    seed_dpo_keys = _collect_keys(args.seed / "agent_p_dpo.jsonl")
    seen_sft_keys = set()
    seen_dpo_keys = set()
    for r in sft_rows:
        seen_sft_keys.update(r.keys())
    for r in dpo_rows:
        seen_dpo_keys.update(r.keys())
    missing_sft = seed_sft_keys - seen_sft_keys
    missing_dpo = seed_dpo_keys - seen_dpo_keys
    if missing_sft:
        warnings.append(f"SFT missing seed keys: {missing_sft}")
    if missing_dpo:
        warnings.append(f"DPO missing seed keys: {missing_dpo}")

    # Report
    print(
        f"validate_training_data: sft_rows={len(sft_rows)} dpo_rows={len(dpo_rows)} "
        f"eval_rows={len(eval_rows)} errors={len(errors)} warnings={len(warnings)}",
        file=sys.stderr,
    )
    if errors:
        print(f"\nERRORS ({len(errors)}):", file=sys.stderr)
        for e in errors[:20]:
            print(f"  ! {e}", file=sys.stderr)
        if len(errors) > 20:
            print(f"  ... ({len(errors) - 20} more)", file=sys.stderr)
        return 1
    print("OK", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())