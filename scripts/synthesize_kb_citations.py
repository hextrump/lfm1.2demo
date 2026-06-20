#!/usr/bin/env python3
"""Synthesize SFT rows that teach the model to cite real KB files.

For each markdown file under --kb, picks 3-5 question templates and emits a
multi-turn ChatML row:
  system → user(question) → assistant toolCall kb_rg_search →
  tool(result from real ripgrep) → assistant(Japanese text quoting 1-2 hits)

We call `PiAgentRuntime._kb_rg_search` (which runs actual `rg`) so every
emitted citation path/snippet corresponds to a real hit on disk.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from runtime.pi_agent import PiAgentRuntime  # noqa: E402


def _today_jp() -> str:
    from datetime import datetime as _dt
    weekdays = ["月曜日", "火曜日", "水曜日", "木曜日", "金曜日", "土曜日", "日曜日"]
    now = _dt.now()
    return f"{now.strftime('%Y-%m-%d')} {weekdays[now.weekday()]}"


SYSTEM_PROMPT = (
    "You are Agent P, an internal ERP / CRM / SSO support assistant. "
    f"Current local date is {_today_jp()} in Asia/Tokyo. "
    "LANGUAGE: always respond in Japanese. Use kb_rg_search when the user "
    "asks about internal rules, policies, or routing."
)


# (filename-substring, [keywords to query], [user questions])
KB_TEMPLATES = [
    (
        "sso/entra-id-login-errors.md",
        ["AADSTS50076", "MFA", "サインイン", "Entra ID"],
        [
            "AADSTS50076 の社内規程は?",
            "MFA 強認証の根拠は?",
            "Entra ID ログインエラーの対応手順を教えてください。",
        ],
    ),
    (
        "helpdesk/ticket-routing-priority-matrix.md",
        ["優先度", "ルーティング", "チケット", "P1", "P2", "P3"],
        [
            "チケットの優先度とルーティングの社内ルールを教えてください。",
            "P1 / P2 / P3 の判断基準は?",
        ],
    ),
    (
        "powerbi/workspace-report-permissions.md",
        ["Power BI", "ワークスペース", "レポート", "権限", "データセット"],
        [
            "Power BI ワークスペースの権限付与ルールは?",
            "Power BI レポートが見られない時の確認手順は?",
        ],
    ),
    (
        "security/mfa-exception-vendor-policy.md",
        ["MFA", "ベンダー", "例外", "申請"],
        [
            "ベンダー MFA 例外申請の社内規程は?",
            "外部パートナーに MFA を免除する条件は?",
        ],
    ),
    (
        "erp_crm/dynamics-salesforce-permissions.md",
        ["Dynamics", "Salesforce", "ロール", "Business Unit", "セキュリティ"],
        [
            "Dynamics 365 のロール付与ルールは?",
            "CRM の Business Unit 権限はどう設定しますか?",
        ],
    ),
]


def _tool_envelope(name: str, arguments: dict) -> str:
    return f"<tool_call>\n{json.dumps({'name': name, 'arguments': arguments}, ensure_ascii=False)}\n</tool_call>"


def _short_path(path: str) -> str:
    return path.split("/")[-1] if "/" in path else path


def _kb_results_for(query: str) -> list[dict]:
    """Run live ripgrep; return at most 3 hits as path/line/snippet."""
    return PiAgentRuntime._kb_rg_search(query)[:3]


def _build_reply(hits: list[dict]) -> str:
    if not hits:
        return "社内 KB に該当する規程が見つかりませんでした。IT Operations Agent P に直接お問い合わせください。"
    lines = ["**推奨される社内規程 / KB ヒッ ト:**", ""]
    for hit in hits[:2]:
        path = hit.get("path", "")
        snippet = (hit.get("snippet", "") or "")[:120].replace("\n", " ")
        if path:
            lines.append(f"- **{_short_path(path)}** を参照(社内規程)")
        if snippet:
            lines.append(f"  - {snippet}…")
    return "\n".join(lines)


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--kb", required=True, type=Path)
    p.add_argument("--out", required=True, type=Path)
    return p.parse_args()


def main() -> int:
    args = _parse_args()
    args.out.parent.mkdir(parents=True, exist_ok=True)

    n_rows = 0
    n_dropped = 0
    with args.out.open("w", encoding="utf-8") as out:
        for subpath, keywords, questions in KB_TEMPLATES:
            for question in questions:
                # Pick the keyword that yields the strongest hits for this file
                best_query = None
                best_hits: list[dict] = []
                for kw in keywords:
                    hits = _kb_results_for(kw)
                    # Filter to hits in this file
                    file_hits = [h for h in hits if subpath.split("/")[-1] in h.get("path", "")]
                    if file_hits and len(file_hits) >= len(best_hits):
                        best_query = kw
                        best_hits = file_hits
                if not best_query:
                    # Fall back: any hits anywhere in the KB that match the topic
                    for kw in keywords:
                        hits = _kb_results_for(kw)
                        if hits:
                            best_query = kw
                            best_hits = hits[:3]
                            break
                if not best_query:
                    n_dropped += 1
                    continue

                tool_result = json.dumps({"hits": best_hits}, ensure_ascii=False)
                assistant = _tool_envelope(
                    "kb_rg_search", {"query": best_query}
                ) + f"\n{best_query} について社内 KB を検索します。"
                final_assistant = _build_reply(best_hits)

                out.write(
                    json.dumps(
                        {
                            "messages": [
                                {"role": "system", "content": SYSTEM_PROMPT},
                                {"role": "user", "content": question},
                                {"role": "assistant", "content": assistant},
                                {"role": "tool", "content": tool_result},
                                {"role": "assistant", "content": final_assistant},
                            ]
                        },
                        ensure_ascii=False,
                    )
                    + "\n"
                )
                n_rows += 1

    print(
        f"synthesize_kb_citations: rows={n_rows} dropped_no_hits={n_dropped}",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())