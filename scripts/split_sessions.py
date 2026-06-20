#!/usr/bin/env python3
"""Split pi-coding-agent session JSONLs into 80/20 train/eval by mtime.

Reads every `*.jsonl` in `--sessions-dir`, sorts by mtime (oldest → newest),
and writes:
  --train-list   : newline-delimited list of paths used for training
  --eval-list    : newline-delimited list of paths held out for evaluation
  --eval-out     : ChatML JSONL materialized from the eval split (so the
                   validator can do leakage checks without re-parsing).

Sessions with malformed JSON are skipped (logged to stderr). Eval is always
the *newest* 20% — those most resemble current production traffic.
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path

# Make sibling modules importable when run directly
sys.path.insert(0, str(Path(__file__).resolve().parent))

from _session_parser import parse_session, render_sft_rows  # noqa: E402


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--sessions-dir",
        required=True,
        type=Path,
        help="Directory containing pi-coding-agent session .jsonl files",
    )
    p.add_argument("--ratio", type=float, default=0.8, help="Train fraction (default 0.8)")
    p.add_argument(
        "--train-list",
        type=Path,
        default=Path("data/sessions_train.txt"),
        help="Output: newline-delimited list of training-session paths",
    )
    p.add_argument(
        "--eval-list",
        type=Path,
        default=Path("data/sessions_eval.txt"),
        help="Output: newline-delimited list of eval-session paths",
    )
    p.add_argument(
        "--eval-out",
        type=Path,
        default=Path("data/eval_sessions.jsonl"),
        help="Output: ChatML JSONL materialized from the eval split",
    )
    p.add_argument(
        "--system-prompt",
        default=(
            "You are Agent P, an internal ERP / CRM / SSO support assistant. "
            "Always respond in Japanese. Use tools when appropriate."
        ),
        help="System prompt to attach to every materialized eval row",
    )
    return p.parse_args()


def main() -> int:
    args = _parse_args()
    sessions_dir: Path = args.sessions_dir
    if not sessions_dir.is_dir():
        print(f"sessions-dir not found: {sessions_dir}", file=sys.stderr)
        return 2

    # Collect + sort by mtime (oldest first)
    files = sorted(
        sessions_dir.glob("*.jsonl"),
        key=lambda p: p.stat().st_mtime,
    )
    n = len(files)
    if n == 0:
        print(f"no .jsonl files in {sessions_dir}", file=sys.stderr)
        return 2

    n_train = max(1, int(round(n * args.ratio)))
    train_files = files[:n_train]
    eval_files = files[n_train:]
    if not eval_files:
        # Always keep at least 1 in eval even if ratio would round to 1.0
        eval_files = files[-1:]
        train_files = files[:-1]

    args.train_list.parent.mkdir(parents=True, exist_ok=True)
    args.train_list.write_text(
        "\n".join(str(p) for p in train_files) + "\n", encoding="utf-8"
    )
    args.eval_list.write_text(
        "\n".join(str(p) for p in eval_files) + "\n", encoding="utf-8"
    )

    # Materialize eval as ChatML
    args.eval_out.parent.mkdir(parents=True, exist_ok=True)
    n_rows = 0
    skipped = 0
    with args.eval_out.open("w", encoding="utf-8") as out:
        for path in eval_files:
            turns = parse_session(path)
            if not turns:
                skipped += 1
                continue
            for row in render_sft_rows(turns, args.system_prompt):
                out.write(__import__("json").dumps(row, ensure_ascii=False) + "\n")
                n_rows += 1

    print(
        f"split_sessions: total={n} train={len(train_files)} eval={len(eval_files)} "
        f"eval_rows_materialized={n_rows} parse_skipped={skipped}",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())