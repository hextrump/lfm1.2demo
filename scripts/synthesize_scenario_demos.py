#!/usr/bin/env python3
"""Synthesize SFT + DPO rows from tests/fixtures/scenarios.py × user-phrase templates.

For each of 8 scenarios × 6 user-phrase templates, emit:
  - 1 SFT row (ChatML messages array) with the gold assistant content
  - 1 DPO row (TRL prompt/chosen/rejected) pairing the SFT row with a
    synthetic "bad" response (English reply / no tool call / fake ticket id)

Templates:
  1. pasted-error     : full scenario.error_text → erp_analyze_pasted_error_with_kb
  2. short-paste      : just scenario.error_code → erp_analyze_pasted_error_with_kb
  3. natural-language : Japanese paraphrase → erp_analyze_pasted_error_with_kb
  4. ticket-request   : "これ IT に連絡して"   → erp_create_ticket_from_current_error
  5. policy-lookup    : "社内規程 / 根拠"      → kb_rg_search with error_code
  6. follow-up-answer : "経理部 / Manager"     → multi-turn ack + recommendations

This produces ~48 SFT + 48 DPO rows. It reuses `pi_agent._system_prompt`,
`_scenario_recommendations`, `_build_followup_ack`, `_build_recommendations_block`
as the source of gold labels (so SFT data matches what the runtime currently
emits — the model learns to reproduce the gold).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from runtime.pi_agent import PiAgentRuntime  # noqa: E402


def _today_jp() -> str:
    from datetime import datetime as _dt
    weekdays = ["月曜日", "火曜日", "水曜日", "木曜日", "金曜日", "土曜日", "日曜日"]
    now = _dt.now()
    return f"{now.strftime('%Y-%m-%d')} {weekdays[now.weekday()]}"


SYSTEM_PROMPT = (
    "You are Agent P, an internal ERP / CRM / SSO support assistant. "
    "You help employees troubleshoot sign-in failures, permission and "
    "license requests, Power BI access, and route unresolved issues to IT "
    f"as tickets. Current local date is {_today_jp()} in Asia/Tokyo. "
    "LANGUAGE: always respond in Japanese. Keep error codes and product "
    "names as-is. Use tools when appropriate; reply directly for greetings/identity/date."
)


# ── Natural-language paraphrases (hand-curated mapping per scenario) ─────

NL_PARAPHRASES = {
    "AADSTS50076": [
        "Dynamics 365 にログインできません。追加認証を要求されます。",
        "サインインに失敗して MFA の通知が届きません。",
    ],
    "AADSTS50105": [
        "アプリが割り当てられていないと言われます。アクセスできません。",
    ],
    "LICENSE_MISSING": [
        "Dynamics 365 のライセンスがありません。サインインできません。",
        "必要なライセンスが割り当てられていないようです。",
    ],
    "CA_BLOCK": [
        "自宅の PC からアクセスしようとするとブロックされます。",
        "Conditional Access で弾かれてしまいます。",
    ],
    "CRM_MENU_MISSING": [
        "Sales Hub のメニューが見えません。ログインは成功しています。",
        "Dynamics 365 の Sales Hub メニューと案件が表示されません。",
    ],
    "POWERBI_DENIED": [
        "Power BI のレポートが見られません。権限がないと言われます。",
    ],
    "MULTI_USER_OUTAGE": [
        "部署全員で Dynamics 365 にログインできません。サービス障害だと思います。",
    ],
    "VENDOR_MFA_EXCEPTION": [
        "ベンダー連携アカウントに MFA を免除したいのですが、例外申請はどうすればいいですか。",
    ],
}


# ── Helpers ────────────────────────────────────────────────────────────

def _tool_envelope(name: str, arguments: dict[str, Any]) -> str:
    return f"<tool_call>\n{json.dumps({'name': name, 'arguments': arguments}, ensure_ascii=False)}\n</tool_call>"


def _synthesize_tool_result(scenario: dict[str, Any], tool_name: str) -> str:
    """Build a realistic JSON toolResult payload for the chosen tool."""
    if tool_name in ("erp_analyze_pasted_error_with_kb", "erp_get_current_error",
                     "erp_inspect_current_error_with_kb"):
        return json.dumps(
            {
                "scenario_key": scenario["scenario_key"],
                "system": scenario["system"],
                "symptom": scenario["symptom"],
                "error_code": scenario["error_code"],
                "category": scenario["category"],
                "risk": scenario["risk"],
                "priority": scenario["priority"],
                "route": scenario["route"],
                "impact": scenario["impact"],
                "trace_id": scenario["trace_id"],
                "correlation_id": scenario["correlation_id"],
                "user_name": scenario["user_name"],
                "department": scenario["department"],
                "role": scenario["role"],
            },
            ensure_ascii=False,
        )
    if tool_name == "kb_rg_search":
        # Pretend ripgrep returned 2 hits
        return json.dumps(
            {
                "hits": [
                    {
                        "path": "knowledge/sso/entra-id-login-errors.md",
                        "line": 6,
                        "snippet": "## Rule SSO-001: Microsoft Entra ID / AADSTS50076 MFA 強認証",
                    },
                    {
                        "path": "knowledge/security/mfa-exception-vendor-policy.md",
                        "line": 4,
                        "snippet": "## Vendor MFA Exception Policy",
                    },
                ]
            },
            ensure_ascii=False,
        )
    return "{}"


def _build_recommendations_reply(scenario: dict[str, Any]) -> str:
    """Compose a gold assistant reply that lists scenario recommendations."""
    recs = PiAgentRuntime._scenario_recommendations(
        scenario["error_code"], scenario["symptom"]
    )
    if not recs:
        recs = ["- 社内 KB に該当する規程が見つかりませんでした。IT Operations Agent P に直接お問い合わせください。"]
    head = (
        f"**{scenario['error_code']}** に関するお問い合わせですね。\n\n"
        f"{scenario['system']} で発生しているエラーを確認しました。\n\n"
        "**追加でお聞きしたいこと:**\n\n"
        "1. 部署名・役職・業務への影響範囲\n"
        "2. このエラーは再現しますか?\n"
        "3. 他 colleagues も同じエラーが出ていますか?\n\n"
        "**推奨される次のステップ:**\n\n" + "\n".join(recs[:4])
    )
    return head


def _build_followup_answer_messages(scenario: dict[str, Any]) -> list[dict[str, str]]:
    """Multi-turn ChatML: user pastes error → assistant toolCall → tool result
    → user answers followup → assistant structured JA reply."""
    user_paste = (
        f"Error Code: {scenario['error_code']}\n"
        f"Trace ID: {scenario['trace_id']}\n"
        f"Correlation ID: {scenario['correlation_id']}"
    )
    followup = (
        f"{scenario['department']} / {scenario['role']} / "
        f"{scenario['user_name']} です。影響は自分だけです。昨日から発生しています。"
    )
    tool_result = _synthesize_tool_result(scenario, "erp_analyze_pasted_error_with_kb")
    # The ack + recommendations block (matches _build_followup_ack + _build_recommendations_block shape)
    error_data = {
        "user_name": scenario["user_name"],
        "department": scenario["department"],
        "role": scenario["role"],
        "system": scenario["system"],
        "error_code": scenario["error_code"],
    }
    ack = (
        f"**{scenario['user_name']} さん ({scenario['department']} / "
        f"{scenario['role']}) の情報を受領しました。**\n\n"
        f"状況: {scenario['system']} で **{scenario['error_code']}** が発生中。\n"
    )
    recs = PiAgentRuntime._scenario_recommendations(
        scenario["error_code"], scenario["symptom"]
    )
    rec_block = (
        "\n**推奨される次のステップ:**\n\n"
        + ("\n".join(recs[:4]) if recs else "- 社内 KB に該当する規程が見つかりませんでした。")
    )
    final_assistant = ack + rec_block
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_paste},
        {
            "role": "assistant",
            "content": _tool_envelope(
                "erp_analyze_pasted_error_with_kb", {"user_message": user_paste}
            )
            + "\n該当のエラーを解析します。",
        },
        {"role": "tool", "content": tool_result},
        {"role": "user", "content": followup},
        {"role": "assistant", "content": final_assistant},
    ]


def _sft_row(messages: list[dict[str, str]]) -> dict[str, Any]:
    return {"messages": messages}


def _dpo_row(
    prompt: list[dict[str, str]],
    chosen_text: str,
    rejected_text: str,
) -> dict[str, Any]:
    return {
        "prompt": prompt,
        "chosen": [{"role": "assistant", "content": chosen_text}],
        "rejected": [{"role": "assistant", "content": rejected_text}],
    }


# ── Template implementations ────────────────────────────────────────────

def _tpl_pasted_error(s: dict[str, Any]) -> dict[str, Any]:
    pasted = (
        f"{s['error_text']}\n"
        f"Error Code: {s['error_code']}\n"
        f"Trace ID: {s['trace_id']}\n"
        f"Correlation ID: {s['correlation_id']}\n"
        f"Timestamp: {s['timestamp']}"
    )
    tool_result = _synthesize_tool_result(s, "erp_analyze_pasted_error_with_kb")
    return _sft_row(
        [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": pasted},
            {
                "role": "assistant",
                "content": _tool_envelope(
                    "erp_analyze_pasted_error_with_kb", {"user_message": pasted}
                )
                + "\nエラー内容を解析して社内 KB と照合します。",
            },
            {"role": "tool", "content": tool_result},
            {"role": "assistant", "content": _build_recommendations_reply(s)},
        ]
    )


def _tpl_short_paste(s: dict[str, Any]) -> dict[str, Any]:
    return _sft_row(
        [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Error Code: {s['error_code']}"},
            {
                "role": "assistant",
                "content": _tool_envelope(
                    "erp_analyze_pasted_error_with_kb",
                    {"user_message": f"Error Code: {s['error_code']}"},
                )
                + f"\n{s['error_code']} について解析します。",
            },
            {"role": "tool", "content": _synthesize_tool_result(s, "erp_analyze_pasted_error_with_kb")},
            {"role": "assistant", "content": _build_recommendations_reply(s)},
        ]
    )


def _tpl_natural_language(s: dict[str, Any], paraphrase: str) -> dict[str, Any]:
    return _sft_row(
        [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": paraphrase},
            {
                "role": "assistant",
                "content": _tool_envelope(
                    "erp_analyze_pasted_error_with_kb", {"user_message": paraphrase}
                )
                + "\n状況を詳しく確認します。",
            },
            {"role": "tool", "content": _synthesize_tool_result(s, "erp_analyze_pasted_error_with_kb")},
            {"role": "assistant", "content": _build_recommendations_reply(s)},
        ]
    )


def _tpl_ticket_request(s: dict[str, Any]) -> dict[str, Any]:
    user = "これ IT に連絡してチケットを作成してください。"
    tool_result = json.dumps(
        {
            "ticket_id": f"KW-{(hash(s['scenario_key']) % 9000) + 1000:04d}",
            "status": "New",
            "route": s["route"],
            "priority": s["priority"],
            "risk": s["risk"],
            "system": s["system"],
            "error_code": s["error_code"],
        },
        ensure_ascii=False,
    )
    ticket_id = json.loads(tool_result)["ticket_id"]
    return _sft_row(
        [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user},
            {
                "role": "assistant",
                "content": _tool_envelope(
                    "erp_create_ticket_from_current_error", {"user_message": user}
                )
                + "\nIT チケットを作成します。",
            },
            {"role": "tool", "content": tool_result},
            {
                "role": "assistant",
                "content": (
                    f"**IT チケットを作成しました**\n\n"
                    f"- **チケットID:** `{ticket_id}`\n"
                    f"- **担当:** {s['route']}\n"
                    f"- **優先度:** {s['priority']}\n"
                    f"- **システム:** {s['system']}\n"
                    f"- **エラーコード:** {s['error_code']}\n\n"
                    "左メニューの **IT Operations** から進捗を確認できます。"
                ),
            },
        ]
    )


def _tpl_policy_lookup(s: dict[str, Any]) -> dict[str, Any]:
    user = f"{s['error_code']} の社内規程・根拠・ルーティングを教えてください。"
    return _sft_row(
        [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user},
            {
                "role": "assistant",
                "content": _tool_envelope("kb_rg_search", {"query": s["error_code"]})
                + f"\n{s['error_code']} について社内 KB を検索します。",
            },
            {"role": "tool", "content": _synthesize_tool_result(s, "kb_rg_search")},
            {
                "role": "assistant",
                "content": (
                    f"**{s['error_code']}** の社内規程をご案内します。\n\n"
                    f"- 担当: {s['route']} · 優先度: {s['priority']} · リスク: {s['risk']}\n"
                    "- **knowledge/sso/entra-id-login-errors.md** を参照(社内規程)\n"
                    "- **knowledge/security/mfa-exception-vendor-policy.md** を参照(関連規程)"
                ),
            },
        ]
    )


def _tpl_followup_answer(s: dict[str, Any]) -> dict[str, Any]:
    return _sft_row(_build_followup_answer_messages(s))


# ── DPO "rejected" synthesizers per template ───────────────────────────

def _dpo_rejected_for(template: str, scenario: dict[str, Any]) -> str:
    """Produce a believable but wrong assistant text for the given template."""
    if template == "pasted_error" or template == "short_paste" or template == "natural_language":
        return (
            "I see the error. Let me help you.\n\n"
            f"Error code: {scenario['error_code']}\n"
            "Please try signing in again. If that doesn't work, contact IT."
        )
    if template == "ticket_request":
        return f"I've created ticket ERC20260117-001 for you. IT will follow up shortly."
    if template == "policy_lookup":
        return "We don't have a specific policy for that error. Please contact IT."
    if template == "followup_answer":
        return "Got it. I'll pass this to IT and they will handle it."
    return "OK."


# ── Main ──────────────────────────────────────────────────────────────

def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--scenarios",
        required=True,
        type=Path,
        help="Path to scenarios.py (must define SCENARIOS dict)",
    )
    p.add_argument("--out", required=True, type=Path, help="SFT JSONL output")
    p.add_argument("--out-dpo", required=True, type=Path, help="DPO JSONL output")
    return p.parse_args()


def _load_scenarios(path: Path) -> dict[str, dict[str, Any]]:
    """Load SCENARIOS dict from a Python source file (no import needed)."""
    src = path.read_text(encoding="utf-8")
    mod_globals: dict[str, Any] = {}
    # Provide a stub for `Path` / etc. if the module needs it (scenarios.py uses no imports)
    exec(compile(src, str(path), "exec"), mod_globals)
    if "SCENARIOS" not in mod_globals:
        raise SystemExit(f"{path} does not define SCENARIOS")
    return mod_globals["SCENARIOS"]


def main() -> int:
    args = _parse_args()
    scenarios = _load_scenarios(args.scenarios)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out_dpo.parent.mkdir(parents=True, exist_ok=True)

    n_sft = 0
    n_dpo = 0
    with args.out.open("w", encoding="utf-8") as sft_out, \
         args.out_dpo.open("w", encoding="utf-8") as dpo_out:
        for key, s in scenarios.items():
            # Templates 1, 2: 1 SFT each + 1 DPO
            for row, label in [
                (_tpl_pasted_error(s), "pasted_error"),
                (_tpl_short_paste(s), "short_paste"),
            ]:
                sft_out.write(json.dumps(row, ensure_ascii=False) + "\n")
                n_sft += 1
                # DPO: same prompt, chosen = first assistant message of SFT,
                # rejected = English/bad version
                chosen_text = row["messages"][-1]["content"]
                prompt_msgs = row["messages"][:2]  # system + user
                dpo_out.write(
                    json.dumps(
                        _dpo_row(
                            prompt=prompt_msgs,
                            chosen_text=chosen_text,
                            rejected_text=_dpo_rejected_for(label, s),
                        ),
                        ensure_ascii=False,
                    )
                    + "\n"
                )
                n_dpo += 1

            # Template 3: 1-2 natural-language paraphrases
            for paraphrase in NL_PARAPHRASES.get(key, []):
                row = _tpl_natural_language(s, paraphrase)
                sft_out.write(json.dumps(row, ensure_ascii=False) + "\n")
                n_sft += 1
                chosen_text = row["messages"][-1]["content"]
                dpo_out.write(
                    json.dumps(
                        _dpo_row(
                            prompt=row["messages"][:2],
                            chosen_text=chosen_text,
                            rejected_text=_dpo_rejected_for("natural_language", s),
                        ),
                        ensure_ascii=False,
                    )
                    + "\n"
                )
                n_dpo += 1

            # Template 4, 5, 6: 1 SFT + 1 DPO each
            for tpl_fn, label in [
                (_tpl_ticket_request(s), "ticket_request"),
                (_tpl_policy_lookup(s), "policy_lookup"),
                (_tpl_followup_answer(s), "followup_answer"),
            ]:
                row = tpl_fn
                sft_out.write(json.dumps(row, ensure_ascii=False) + "\n")
                n_sft += 1
                chosen_text = row["messages"][-1]["content"]
                dpo_out.write(
                    json.dumps(
                        _dpo_row(
                            prompt=row["messages"][:2],
                            chosen_text=chosen_text,
                            rejected_text=_dpo_rejected_for(label, s),
                        ),
                        ensure_ascii=False,
                    )
                    + "\n"
                )
                n_dpo += 1

    print(
        f"synthesize_scenario_demos: scenarios={len(scenarios)} "
        f"sft_rows={n_sft} dpo_rows={n_dpo}",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())