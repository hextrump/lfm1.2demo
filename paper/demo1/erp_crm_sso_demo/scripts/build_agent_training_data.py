from __future__ import annotations

import json
from pathlib import Path
from typing import Any

APP_DIR = Path(__file__).resolve().parents[1]
SESSION_DIR = APP_DIR / ".pi-agent" / "sessions" / "--home-mimi-coding-LFM1.2b-paper-demo1-erp_crm_sso_demo--"
OUT_DIR = APP_DIR / "training_data"


def iter_sessions() -> list[list[dict[str, Any]]]:
    sessions: list[list[dict[str, Any]]] = []
    for path in sorted(SESSION_DIR.glob("*.jsonl")):
        rows = []
        for line in path.read_text(encoding="utf-8").splitlines():
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        sessions.append(rows)
    return sessions


def message_text(message: dict[str, Any]) -> str:
    parts = []
    for item in message.get("content", []):
        if item.get("type") == "text":
            parts.append(str(item.get("text", "")))
    return "\n".join(parts).strip()


def tool_calls(message: dict[str, Any]) -> list[dict[str, Any]]:
    calls = []
    for item in message.get("content", []):
        if item.get("type") == "toolCall":
            calls.append({"name": item.get("name"), "arguments": item.get("arguments", {})})
    return calls


def session_messages(session: list[dict[str, Any]]) -> list[dict[str, Any]]:
    messages: list[dict[str, Any]] = []
    for row in session:
        if row.get("type") == "message":
            message = row.get("message", {})
        elif row.get("type") == "message_end":
            message = row.get("message", {})
        else:
            continue
        if isinstance(message, dict) and message.get("role") in {"user", "assistant"}:
            messages.append(message)
    return messages


def classify_prompt(text: str) -> str:
    lower = text.lower()
    stripped = text.strip()
    if stripped in {"こんにちは", "你好", "您好", "hello", "hi"}:
        return "greeting"
    if "今日は" in text or "何の日" in text:
        return "smalltalk_date"
    if "aadsts" in lower or "trace id" in lower or "sign-in failed" in lower:
        if any(word in lower for word in ["ticket", "チケット", "helpdesk", "itに連絡", "it に連絡"]):
            return "ticket_request"
        return "pasted_error"
    if any(word in lower for word in ["ticket", "チケット", "helpdesk", "itに連絡", "it に連絡", "contact it"]):
        return "ticket_request"
    if "今出ている" in text or "current error" in lower:
        return "current_error"
    return "other"


def chosen_for(prompt: str, kind: str) -> str:
    if kind == "greeting":
        return "こんにちは。"
    if kind == "smalltalk_date":
        return "今日は2026年6月17日です。"
    if kind == "pasted_error":
        safe_prompt = prompt.replace("\n", " ")
        return (
            '<tool_call>{"name":"erp_analyze_pasted_error_with_kb","arguments":'
            + json.dumps({"user_message": safe_prompt}, ensure_ascii=False)
            + "}</tool_call>"
        )
    if kind == "current_error":
        return '<tool_call>{"name":"erp_get_current_error","arguments":{}}</tool_call>'
    if kind == "ticket_request":
        return '<tool_call>{"name":"erp_create_ticket_from_current_error","arguments":{"user_message":' + json.dumps(prompt, ensure_ascii=False) + "}}</tool_call>"
    return ""


def is_bad_tool_for_kind(kind: str, calls: list[dict[str, Any]]) -> bool:
    names = {str(call.get("name")) for call in calls}
    if kind == "smalltalk_date":
        return bool(names)
    if kind == "greeting":
        return bool(names)
    if kind == "pasted_error":
        return "erp_create_ticket" in names or "erp_create_ticket_from_current_error" in names or "read" in names
    if kind == "ticket_request":
        return "erp_create_ticket_from_current_error" not in names
    if kind == "current_error":
        return "erp_get_current_error" not in names and "erp_inspect_current_error_with_kb" not in names
    return False


def synthetic_prompts() -> list[tuple[str, str]]:
    pasted_errors = [
        "Sign-in failed Additional authentication required Error Code: AADSTS50076 Trace ID: trc-aadsts50076-015259",
        "Dynamics 365 に入れません。AADSTS50076 と Trace ID: trc-aadsts50076-015259 が表示されています",
        "Salesforce SSO error AADSTS50105 Trace ID: trc-aadsts50105-031500",
        "Power BI license error. User cannot open report. Error Code: LICENSE_REQUIRED",
        "CRM menu permission denied. Trace ID: trc-rbac-0042",
    ]
    current_errors = [
        "今出ているエラーを確認して",
        "現在のERP画面のログを取得して",
        "current error を見てください",
        "画面で出ているログを確認して",
    ]
    tickets = [
        "まだ解決しないのでITに連絡してチケットを作成してください",
        "このエラーをヘルプデスクにエスカレーションしてください",
        "Please contact IT and create a ticket for the current ERP error",
        "ITに連絡して、現在のエラーで問い合わせを作ってください",
    ]
    smalltalk = [
        "こんにちは",
        "こんにちは今日は何の日",
        "今日は何の日",
        "hello",
        "你好",
    ]
    rows: list[tuple[str, str]] = []
    rows.extend((prompt, "pasted_error") for prompt in pasted_errors)
    rows.extend((prompt, "current_error") for prompt in current_errors)
    rows.extend((prompt, "ticket_request") for prompt in tickets)
    rows.extend((prompt, classify_prompt(prompt)) for prompt in smalltalk)
    return rows


def build_examples() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    sft: list[dict[str, Any]] = []
    dpo: list[dict[str, Any]] = []
    for user_text, kind in synthetic_prompts():
        chosen = chosen_for(user_text, kind)
        if chosen:
            sft.append(sft_row(user_text, chosen))

    for session in iter_sessions():
        user_text = ""
        assistant_text = ""
        assistant_calls: list[dict[str, Any]] = []
        for message in session_messages(session):
            role = message.get("role")
            if role == "user":
                user_text = message_text(message)
            elif role == "assistant" and user_text:
                assistant_text = message_text(message)
                assistant_calls.extend(tool_calls(message))
        if not user_text:
            continue
        kind = classify_prompt(user_text)
        chosen = chosen_for(user_text, kind)
        if not chosen:
            continue
        sft.append(sft_row(user_text, chosen))
        rejected = assistant_text
        if assistant_calls:
            rejected = "<tool_call>" + json.dumps(assistant_calls[0], ensure_ascii=False) + "</tool_call>"
        if rejected and is_bad_tool_for_kind(kind, assistant_calls):
            dpo.append({
                "prompt": [
                    {"role": "system", "content": "You are Agent P. Choose correct ERP tools and avoid unrelated tools."},
                    {"role": "user", "content": user_text},
                ],
                "chosen": [{"role": "assistant", "content": chosen}],
                "rejected": [{"role": "assistant", "content": rejected}],
            })
    return dedupe(sft), dedupe(dpo)


def sft_row(user_text: str, chosen: str) -> dict[str, Any]:
    return {
        "messages": [
            {"role": "system", "content": "You are Agent P. Use tools only for ERP tasks. Do not use tools for greetings or date questions."},
            {"role": "user", "content": user_text},
            {"role": "assistant", "content": chosen},
        ]
    }


def dedupe(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen = set()
    output = []
    for row in rows:
        key = json.dumps(row, ensure_ascii=False, sort_keys=True)
        if key in seen:
            continue
        seen.add(key)
        output.append(row)
    return output


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8")


if __name__ == "__main__":
    sft_rows, dpo_rows = build_examples()
    write_jsonl(OUT_DIR / "agent_p_sft.jsonl", sft_rows)
    write_jsonl(OUT_DIR / "agent_p_dpo.jsonl", dpo_rows)
    print(f"SFT examples: {len(sft_rows)} -> {OUT_DIR / 'agent_p_sft.jsonl'}")
    print(f"DPO examples: {len(dpo_rows)} -> {OUT_DIR / 'agent_p_dpo.jsonl'}")
