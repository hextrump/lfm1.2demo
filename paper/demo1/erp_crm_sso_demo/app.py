from __future__ import annotations

import json
import re
import subprocess
import time
from html import escape
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd
import requests
import streamlit as st

from agent_q import PiAgentRuntime

APP_DIR = Path(__file__).resolve().parent
KNOWLEDGE_DIR = APP_DIR / "knowledge"
ERP_STATE_DIR = APP_DIR / "erp_state"
CURRENT_ERROR_PATH = ERP_STATE_DIR / "current_error.json"
LLAMA_SERVER_URL = "http://127.0.0.1:8080"

st.set_page_config(
    page_title="Internal ERP Portal",
    page_icon="",
    layout="wide",
)

SCENARIOS: dict[str, dict[str, Any]] = {
    "AADSTS50076": {
        "label": "SSO / MFA login failure",
        "title": "Additional authentication required",
        "system": "Dynamics 365",
        "symptom": "login_failed",
        "category": "Microsoft Entra ID / MFA / Conditional Access",
        "risk": "Medium",
        "priority": "P3",
        "route": "Identity / Entra ID 管理チーム",
        "impact": "single_user",
        "error_code": "AADSTS50076",
        "error_text": "Due to a configuration change made by your administrator, or because you moved to a new location, you must use multi-factor authentication.",
        "user_prompt": "Dynamics 365 にログインできません。AADSTS50076 と表示されます。",
        "self_steps": [
            "Edge または Chrome の InPrivate / シークレットモードで再ログインしてください。",
            "Microsoft Authenticator の通知を確認し、MFA を完了してください。",
            "会社支給端末または VPN 経由で再試行してください。",
            "端末変更・出張・海外アクセスがある場合はチケットに記載してください。",
        ],
        "keywords": ["AADSTS50076", "MFA", "Conditional Access", "Dynamics 365"],
    },
    "AADSTS50105": {
        "label": "User not assigned to app",
        "title": "User assignment required",
        "system": "Salesforce",
        "symptom": "app_assignment_missing",
        "category": "Application Assignment / Permission",
        "risk": "Medium",
        "priority": "P3",
        "route": "業務システム権限管理チーム",
        "impact": "single_user",
        "error_code": "AADSTS50105",
        "error_text": "The signed in user is not assigned to a role for the application.",
        "user_prompt": "Salesforce に入ろうとすると AADSTS50105 が出ます。同僚は入れます。",
        "self_steps": [
            "利用申請が完了しているか確認してください。",
            "所属部署、利用目的、上長承認の有無を確認してください。",
            "同僚が使えても個人またはグループ単位の割当が必要な場合があります。",
        ],
        "keywords": ["AADSTS50105", "User not assigned", "Salesforce", "権限"],
    },
    "LICENSE_MISSING": {
        "label": "Dynamics license missing",
        "title": "License required",
        "system": "Dynamics 365",
        "symptom": "license_missing",
        "category": "License / Microsoft 365",
        "risk": "Medium",
        "priority": "P3",
        "route": "Microsoft 365 ライセンス管理チーム",
        "impact": "single_user",
        "error_code": "LICENSE_MISSING",
        "error_text": "This user does not have the required Dynamics 365 license.",
        "user_prompt": "Dynamics 365 のライセンスがないと表示されます。",
        "self_steps": [
            "利用開始申請が承認済みか確認してください。",
            "対象業務と利用開始日をチケットに記載してください。",
            "ライセンス付与はシステムオーナー承認後に実施されます。",
        ],
        "keywords": ["Dynamics 365", "License missing", "ライセンス"],
    },
    "CA_BLOCK": {
        "label": "Conditional Access blocked",
        "title": "Access blocked by policy",
        "system": "社内ERP",
        "symptom": "conditional_access_block",
        "category": "Security / Conditional Access",
        "risk": "High",
        "priority": "P2",
        "route": "Security / Conditional Access チーム",
        "impact": "single_user",
        "error_code": "CA_BLOCK",
        "error_text": "Your sign-in was blocked because the device, network, or user risk did not satisfy company access policy.",
        "user_prompt": "出張先から社内ERPに入ろうとしたら条件付きアクセスでブロックされました。",
        "self_steps": [
            "会社支給端末からアクセスしてください。",
            "VPN または許可されたネットワークから再試行してください。",
            "私物端末、海外 IP、未知の場所からのアクセスは制限される場合があります。",
        ],
        "keywords": ["Conditional Access", "CA_BLOCK", "社内ERP", "Security"],
    },
    "CRM_MENU_MISSING": {
        "label": "CRM menu missing after login",
        "title": "Sales menu not visible",
        "system": "Dynamics 365 Sales",
        "symptom": "menu_missing",
        "category": "CRM Role / Business Unit Permission",
        "risk": "Medium",
        "priority": "P3",
        "route": "CRM Owner / Dynamics 管理者",
        "impact": "single_user",
        "error_code": "NO_ERROR_CODE",
        "error_text": "Login succeeded, but Sales Hub menu and customer opportunities are not visible.",
        "user_prompt": "ログインはできますが、Dynamics 365 で営業案件メニューが見えません。",
        "self_steps": [
            "所属チームと業務ロールが正しいか確認してください。",
            "異動直後の場合、旧部署の権限が残っていないか確認してください。",
            "上長承認済みの権限申請番号をチケットに記載してください。",
        ],
        "keywords": ["Dynamics 365 Sales", "Menu hidden", "Security role missing", "営業案件"],
    },
    "POWERBI_DENIED": {
        "label": "Power BI report permission denied",
        "title": "Report access denied",
        "system": "Power BI",
        "symptom": "report_permission_denied",
        "category": "Power BI Workspace / Dataset Permission",
        "risk": "Low",
        "priority": "P3",
        "route": "BI 管理者 / Data Platform Team",
        "impact": "single_user",
        "error_code": "PBI_ACCESS_DENIED",
        "error_text": "You do not have permission to view this report or dataset.",
        "user_prompt": "オーナーアプリの Power BI レポートが見られません。",
        "self_steps": [
            "対象レポート名、Workspace 名、利用目的を確認してください。",
            "Power BI Pro / Fabric ライセンスの有無を確認してください。",
            "レポート所有者または BI 管理者へアクセス申請が必要です。",
        ],
        "keywords": ["Power BI", "Workspace permission denied", "Dataset permission", "Owner App"],
    },
    "MULTI_USER_OUTAGE": {
        "label": "Multiple users cannot access ERP",
        "title": "Possible service incident",
        "system": "社内ERP",
        "symptom": "multi_user_outage",
        "category": "IT Ops / Service Incident",
        "risk": "High",
        "priority": "P2",
        "route": "IT Ops / Incident Manager",
        "impact": "multiple_users",
        "error_code": "MULTI_USER_OUTAGE",
        "error_text": "Multiple users from the same department reported access failures within a short time window.",
        "user_prompt": "経理部の複数人が社内ERPに入れません。全員同じ画面で止まります。",
        "self_steps": [
            "個人端末の問題ではない可能性があります。",
            "影響部署、人数、開始時刻を記録してください。",
            "ステータスページと IT 告知を確認してください。",
        ],
        "keywords": ["multiple users", "社内ERP", "Incident Manager", "P2"],
    },
    "VENDOR_MFA_EXCEPTION": {
        "label": "Vendor requests MFA exception",
        "title": "High-risk MFA exception request",
        "system": "Integration Account",
        "symptom": "vendor_mfa_exception",
        "category": "Security Exception / Vendor Access",
        "risk": "High",
        "priority": "P2",
        "route": "Security Team + IAM Approval Board",
        "impact": "privileged_account",
        "error_code": "VENDOR_MFA_EXCEPTION",
        "error_text": "Vendor requested a privileged integration account without MFA or Conditional Access.",
        "user_prompt": "ベンダーが連携アカウントの MFA を無効化してほしいと言っています。",
        "self_steps": [
            "MFA 無効化は自助対応できません。",
            "サービスプリンシパル、証明書認証、最小権限設計を検討してください。",
            "例外が必要な場合は Security と IAM の承認が必須です。",
        ],
        "keywords": ["Vendor Access", "MFA exception", "Global Admin risk", "Service Principal"],
    },
}

USERS = [
    {"name": "山田 太郎", "email": "taro.yamada@demo.local", "dept": "営業部", "role": "Sales", "location": "Tokyo HQ"},
    {"name": "佐藤 花子", "email": "hanako.sato@demo.local", "dept": "経理部", "role": "Finance", "location": "Osaka Branch"},
    {"name": "鈴木 一郎", "email": "ichiro.suzuki@vendor.example", "dept": "外部委託", "role": "Contractor", "location": "Remote"},
]


def init_state() -> None:
    defaults = {
        "scenario_key": "AADSTS50076",
        "employee_messages": [],
        "it_messages": [],
        "tickets": [],
        "audit_logs": [],
        "assistant_open": True,
        "last_ticket": None,
        "active_error": None,
        "last_agent_events": [],
        "last_agent_evidence": [],
        "agent_p_runtime": PiAgentRuntime(),
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def now_text() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S JST")


def add_audit(agent: str, action: str, target: str, result: str, risk: str = "Low") -> None:
    st.session_state.audit_logs.append({
        "time": now_text(),
        "agent": agent,
        "action": action,
        "target": target,
        "result": result,
        "risk": risk,
    })


def llama_server_available() -> bool:
    try:
        return requests.get(f"{LLAMA_SERVER_URL}/health", timeout=2).ok
    except requests.RequestException:
        return False


def rg_search(query: str, limit: int = 8) -> list[dict[str, str]]:
    if not KNOWLEDGE_DIR.exists():
        return []
    try:
        result = subprocess.run(
            ["rg", "-n", "-i", "--context", "1", query, str(KNOWLEDGE_DIR)],
            check=False,
            capture_output=True,
            text=True,
            timeout=4,
        )
    except (subprocess.SubprocessError, FileNotFoundError):
        return []

    hits: list[dict[str, str]] = []
    for line in result.stdout.splitlines():
        if not line or line.startswith("--"):
            continue
        match = re.match(r"([^:]+):(\d+)[:-](.*)", line)
        if not match:
            continue
        path, line_no, snippet = match.groups()
        rel_path = str(Path(path).relative_to(APP_DIR)) if path.startswith(str(APP_DIR)) else path
        hits.append({"path": rel_path, "line": line_no, "snippet": snippet.strip()})
        if len(hits) >= limit:
            break
    return hits


def format_it_handoff(ticket: dict[str, Any]) -> str:
    refs = "\n".join(f"- `{h['path']}:{h['line']}` {h['snippet']}" for h in ticket.get("evidence", [])[:5])
    return f"""
### IT Operations

**受信チケット**: `{ticket.get('ticket_id', '')}`  
**分類**: {ticket.get('category', 'Agent P ticket')}
**優先度**: {ticket.get('priority', 'P3')}  
**影響範囲**: {ticket.get('impact', 'unknown')}  
**推奨キュー**: {ticket.get('route', 'IT Operations')}

#### Agent P からの引継ぎ

- Title: {ticket.get('title', ticket.get('summary', ''))}
- System: {ticket.get('system', '')}
- Error code: {ticket.get('error_code', '')}
- Trace ID: {ticket.get('trace_id', '')}
- Requester: {ticket.get('requester', '')}

#### 参照根拠
{refs or '- No evidence attached.'}
"""


def write_current_error_state(error_state: dict[str, Any] | None) -> None:
    ERP_STATE_DIR.mkdir(parents=True, exist_ok=True)
    if error_state is None:
        CURRENT_ERROR_PATH.write_text(json.dumps({"active": False}, ensure_ascii=False, indent=2), encoding="utf-8")
        return
    CURRENT_ERROR_PATH.write_text(json.dumps({"active": True, **error_state}, ensure_ascii=False, indent=2), encoding="utf-8")


def persist_agent_result(user_text: str, result: Any) -> None:
    st.session_state.employee_messages.append({"role": "assistant", "content": result.reply})
    st.session_state.last_agent_events = result.events
    st.session_state.last_agent_evidence = result.evidence
    if result.ticket:
        st.session_state.tickets.append(result.ticket)
        st.session_state.last_ticket = result.ticket
        st.session_state.it_messages.append({"role": "assistant", "content": format_it_handoff(result.ticket)})
        add_audit("Agent P", "ticket_created", result.ticket["ticket_id"], result.ticket.get("route", ""), result.ticket.get("risk", "Low"))
        add_audit("IT Operations Agent", "agent_to_agent_received", result.ticket["ticket_id"], result.ticket.get("priority", ""), result.ticket.get("risk", "Low"))
    add_audit("Agent P", "chat", user_text[:60], f"{len(result.events)} tool events", "Low")


def render_live_trace(lines: list[str], placeholder: Any) -> None:
    trace = "\n".join(lines[-18:])
    placeholder.markdown(
        f"""
<div class="runtime-panel">
  <div class="runtime-head"><span></span> Runtime trace</div>
  <pre class="live-trace">{escape(trace)}</pre>
</div>
""",
        unsafe_allow_html=True,
    )


def chat_rows_html(messages: list[dict[str, str]], pending_user: str | None = None, pending_assistant: str | None = None) -> str:
    rows = []
    visible_messages = messages[-20:]
    if pending_user is not None:
        visible_messages = [*visible_messages, {"role": "user", "content": pending_user}]
    if pending_assistant is not None:
        visible_messages = [*visible_messages, {"role": "assistant", "content": pending_assistant or "..."}]
    for msg in visible_messages:
        role = "user" if msg.get("role") == "user" else "assistant"
        label = "You" if role == "user" else "Agent P"
        content = escape(str(msg.get("content", ""))).replace("\n", "<br>")
        rows.append(
            f"""
<div class="chat-row chat-row-{role}">
  <div class="chat-label">{label}</div>
  <div class="chat-bubble chat-bubble-{role}">{content}</div>
</div>
"""
        )
    return "".join(rows)


def render_chat_container(placeholder: Any, messages: list[dict[str, str]], pending_user: str | None = None, pending_assistant: str | None = None) -> None:
    rows = chat_rows_html(messages, pending_user, pending_assistant)
    if not rows:
        placeholder.markdown('<div class="chat-empty">Agent P is ready.</div>', unsafe_allow_html=True)
        return
    placeholder.markdown(f'<div class="llm-chat-scroll">{rows}</div>', unsafe_allow_html=True)


def stream_text(user_text: str, text: str, placeholder: Any) -> None:
    output = ""
    chunks = re.split(r"(\s+)", text)
    for chunk in chunks:
        output += chunk
        render_chat_container(placeholder, st.session_state.employee_messages, user_text, output)
        time.sleep(0.012)


def run_employee_chat_live(user_text: str, scenario: dict[str, Any], user: dict[str, str], trace_placeholder: Any, chat_placeholder: Any) -> None:
    render_chat_container(chat_placeholder, st.session_state.employee_messages, user_text, "")
    lines = [
        "$ session.start",
        f"> user.input {user_text[:120]}",
        "> runtime Pi + local LFM2.5",
        "> tools profile resolving",
    ]
    runtime: PiAgentRuntime = st.session_state.agent_p_runtime
    lines.append("$ pi local-lfm/lfm2.5-1.2b-instruct")
    result = runtime.chat(user_text)
    if result.session_file:
        lines.append(f"> session {result.session_file}")
    if result.events:
        render_live_trace(lines, trace_placeholder)
        for event in result.events:
            lines.append(f"{event.tool} {event.status}: {event.detail[:180]}")
            render_live_trace(lines, trace_placeholder)
            time.sleep(0.08)
    else:
        lines.append("> no tool call required")
    if result.evidence:
        lines.append(f"> evidence {len(result.evidence)} snippets")
    if result.ticket:
        lines.append(f"> ticket {result.ticket.get('ticket_id')}")
    lines.append("> response.stream")
    if result.events or result.evidence or result.ticket:
        render_live_trace(lines, trace_placeholder)
    stream_text(user_text, result.reply, chat_placeholder)
    st.session_state.employee_messages.append({"role": "user", "content": user_text})
    persist_agent_result(user_text, result)


def render_status_badge(text: str, kind: str) -> None:
    classes = {"ok": "badge-ok", "warn": "badge-warn", "bad": "badge-bad"}
    st.markdown(f'<span class="badge {classes.get(kind, "badge-warn")}">{text}</span>', unsafe_allow_html=True)


def render_assistant_header(scenario: dict[str, Any]) -> None:
    active_error = st.session_state.get("active_error")
    status_kind = "bad" if active_error and scenario["risk"] == "High" else "warn" if active_error and scenario["risk"] == "Medium" else "ok"
    status_text = f"{scenario['risk']} · {scenario['route']}" if active_error else "Ready · waiting for ERP event log"
    st.markdown(
        f"""
<div class="assistant-hero">
  <div>
    <div class="assistant-name">Agent P</div>
    <div class="assistant-sub">Support session</div>
  </div>
</div>
<div class="assistant-status">
  <span class="dot dot-live"></span> Local LFM · <span class="risk-{status_kind}">{status_text}</span>
</div>
""",
        unsafe_allow_html=True,
    )


def render_evidence_chips(evidence: list[dict[str, str]]) -> None:
    if not evidence:
        return
    chips = []
    for hit in evidence[:5]:
        if hit.get("path") and hit.get("line"):
            label = f"{Path(str(hit['path'])).name}:{hit['line']}"
            title = f"{hit.get('path')}:{hit.get('line')}"
        elif hit.get("raw"):
            label = str(hit["raw"]).replace(str(APP_DIR), "").strip("/")[:64]
            title = str(hit["raw"])
        else:
            continue
        chips.append(f'<span class="evidence-chip" title="{escape(title)}">{escape(label)}</span>')
    if not chips:
        return
    st.markdown(f'<div class="evidence-strip">{"".join(chips)}</div>', unsafe_allow_html=True)


def render_activity_event(event: Any) -> str:
    if event.status == "fallback":
        label = "runtime fallback"
        css_class = "activity-line activity-line-fallback"
    elif event.status == "error":
        label = "model missed required tool"
        css_class = "activity-line activity-line-error"
    elif event.status == "retry":
        label = "retry"
        css_class = "activity-line activity-line-retry"
    else:
        label = event.status
        css_class = "activity-line"
    detail = escape(event.detail[:150])
    return f'<div class="{css_class}"><b>{escape(event.tool)}</b> {escape(label)}: {detail}</div>'


def render_chat_messages(messages: list[dict[str, str]]) -> None:
    if not messages:
        st.markdown('<div class="chat-empty">Agent P is ready.</div>', unsafe_allow_html=True)
        return
    rows = []
    for msg in messages[-20:]:
        role = "user" if msg.get("role") == "user" else "assistant"
        label = "You" if role == "user" else "Agent P"
        content = escape(str(msg.get("content", ""))).replace("\n", "<br>")
        rows.append(
            f"""
<div class="chat-row chat-row-{role}">
  <div class="chat-label">{label}</div>
  <div class="chat-bubble chat-bubble-{role}">{content}</div>
</div>
"""
        )
    st.markdown(f'<div class="llm-chat-scroll">{"".join(rows)}</div>', unsafe_allow_html=True)


init_state()

st.markdown(
    """
<style>
.stApp { background: #f3f4f6; color: #1f2937; }
.block-container { padding-top: 0.6rem; max-width: 1560px; }
[data-testid="stSidebar"] { background: #e5e7eb; border-right: 1px solid #c7cbd1; }
[data-testid="stSidebar"] * { color: #1f2937; }
.kw-topbar { border: 1px solid #b8bec7; background: #f8f9fb; padding: 10px 12px; border-radius: 0; margin-bottom: 10px; }
.kw-title { font-size: 18px; font-weight: 700; color: #111827; }
.kw-subtitle { color: #4b5563; font-size: 12px; margin-top: 2px; }
.error-box { border: 1px solid #c7cbd1; border-left: 4px solid #b91c1c; background: #fff; border-radius: 0; padding: 12px; color: #1f2937; }
.success-box { border: 1px solid #c7cbd1; border-left: 4px solid #6b7280; background: #fff; border-radius: 0; padding: 12px; color: #1f2937; }
.assistant-hero { display: flex; align-items: center; gap: 12px; padding: 12px 14px; background: #f8fafc; color: #111827; border: 1px solid #c7cbd1; border-bottom: 0; }
.assistant-name { font-weight: 700; font-size: 15px; }
.assistant-sub { color: #4b5563; font-size: 12px; margin-top: 2px; }
.assistant-status { padding: 8px 14px; background: #ffffff; border-left: 1px solid #c7cbd1; border-right: 1px solid #c7cbd1; border-bottom: 1px solid #e5e7eb; font-size: 12px; color: #374151; }
.dot { display:inline-block; width: 8px; height: 8px; border-radius: 50%; margin-right: 5px; }
.dot-live { background: #15803d; }
.risk-ok { color: #166534; font-weight: 700; }
.risk-warn { color: #92400e; font-weight: 700; }
.risk-bad { color: #991b1b; font-weight: 700; }
.assistant-section { padding: 14px 16px; border-bottom: 1px solid #eef2f7; }
.assistant-section-title { font-size: 12px; font-weight: 800; text-transform: uppercase; color: #64748b; margin-bottom: 8px; letter-spacing: .02em; }
.quick-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }
.quick-card { border: 1px solid #dbe3ef; border-radius: 6px; padding: 9px; background: #ffffff; font-size: 12px; color: #334155; }
.tool-trace { padding: 12px 16px; background: #ffffff; border-bottom: 1px solid #e5e7eb; }
.tool-title { font-size: 12px; font-weight: 800; color: #475569; margin-bottom: 8px; }
.tool-step { display: flex; gap: 9px; align-items: flex-start; padding: 7px 0; border-top: 1px solid #eef2f7; }
.tool-step:first-of-type { border-top: 0; }
.tool-step span { width: 21px; height: 21px; border-radius: 50%; display:flex; align-items:center; justify-content:center; font-size: 11px; font-weight: 800; flex: 0 0 21px; }
.tool-step.done span { background: #dcfce7; color: #166534; }
.tool-step.blocked span { background: #fee2e2; color: #991b1b; }
.tool-step b { font-size: 12px; color: #0f172a; }
.tool-step small { color: #64748b; }
.evidence-strip { padding: 8px 12px; background: #ffffff; display: flex; flex-wrap: wrap; gap: 4px; border-left: 1px solid #c7cbd1; border-right: 1px solid #c7cbd1; border-bottom: 1px solid #e5e7eb; }
.evidence-chip { display:inline-block; max-width: 100%; border: 1px solid #c7cbd1; border-radius: 0; padding: 3px 6px; font-size: 11px; color:#374151; background:#f9fafb; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.llm-chat-scroll { height: 520px; overflow-y: auto; padding: 18px 18px 22px 18px; box-sizing: border-box; background: #ffffff; border-left: 1px solid #c7cbd1; border-right: 1px solid #c7cbd1; border-bottom: 1px solid #e5e7eb; }
.chat-empty { height: 520px; display: flex; align-items: center; justify-content: center; color: #6b7280; font-size: 13px; background: #ffffff; border-left: 1px solid #c7cbd1; border-right: 1px solid #c7cbd1; border-bottom: 1px solid #e5e7eb; }
.chat-row { margin-bottom: 16px; clear: both; }
.chat-label { font-size: 12px; color: #6b7280; margin-bottom: 6px; }
.chat-bubble { max-width: 84%; padding: 10px 12px; border: 1px solid #d1d5db; font-size: 15px; line-height: 1.55; word-break: break-word; white-space: normal; }
.chat-row-user { text-align: right; }
.chat-row-user .chat-label { text-align: right; }
.chat-bubble-user { margin-left: auto; background: #1f2937; color: #ffffff; border-color: #1f2937; border-radius: 8px 8px 2px 8px; text-align: left; }
.chat-bubble-assistant { background: #f9fafb; color: #111827; border-color: #d1d5db; border-radius: 8px 8px 8px 2px; }
.activity-strip { min-height: 42px; max-height: 92px; overflow-y: auto; padding: 8px 12px; border-left: 1px solid #c7cbd1; border-right: 1px solid #c7cbd1; border-bottom: 1px solid #e5e7eb; background: #fafafa; box-sizing: border-box; }
.activity-title { font-size: 11px; font-weight: 700; color: #4b5563; margin-bottom: 5px; }
.activity-line { font-size: 11px; color: #4b5563; margin: 2px 0; line-height: 1.35; }
.activity-line-error { color: #991b1b; }
.activity-line-retry { color: #92400e; }
.activity-line-fallback { color: #166534; font-weight: 600; }
.runtime-panel { border-left: 1px solid #c7cbd1; border-right: 1px solid #c7cbd1; border-bottom: 1px solid #c7cbd1; background: #0f172a; }
.runtime-head { height: 28px; padding: 6px 10px 0 10px; color: #cbd5e1; font-size: 11px; font-weight: 700; box-sizing: border-box; border-bottom: 1px solid rgba(148, 163, 184, .25); }
.runtime-head span { display: inline-block; width: 7px; height: 7px; border-radius: 999px; background: #22c55e; margin-right: 6px; }
.live-trace { height: 112px; overflow-y: auto; margin: 0; padding: 9px 10px 11px 10px; background: #0f172a; color: #d1fae5; font-size: 11px; line-height: 1.45; white-space: pre-wrap; font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", monospace; }
div[data-testid="stForm"] { border: 1px solid #c7cbd1; border-top: 0; border-radius: 0; padding: 10px 12px 12px 12px; background: #ffffff; }
div[data-testid="stForm"] [data-testid="stHorizontalBlock"] { align-items: end; gap: 8px; }
div[data-testid="stForm"] [data-testid="stTextInput"] input { border-radius: 6px; border: 1px solid #c7cbd1; min-height: 40px; font-size: 14px; background: #ffffff; color: #111827; }
div[data-testid="stForm"] .stButton button { min-height: 40px; border-radius: 6px; }
div[data-testid="stChatInput"] textarea { border-radius: 6px; border: 1px solid #c7cbd1; font-size: 14px; }
.badge { display: inline-block; padding: 3px 6px; border-radius: 0; font-size: 12px; font-weight: 600; margin-right: 6px; border: 1px solid #c7cbd1; }
.badge-ok { background: #f9fafb; color: #166534; }
.badge-warn { background: #f9fafb; color: #92400e; }
.badge-bad { background: #f9fafb; color: #991b1b; }
.metric-row { display:grid; grid-template-columns: repeat(4, 1fr); gap: 10px; }
.metric-card { border: 1px solid #c7cbd1; border-radius: 0; padding: 12px; background: #fff; }
.metric-value { font-size: 22px; font-weight: 800; color: #0f172a; }
.metric-label { color: #64748b; font-size: 12px; }
</style>
""",
    unsafe_allow_html=True,
)

st.sidebar.title("Internal ERP Portal")
st.sidebar.caption("Private ERP / CRM / BI portal")
menu = st.sidebar.radio("Console", ["Employee Portal", "IT Operations", "Knowledge Search", "Audit Log"], index=0)
st.sidebar.divider()
render_status_badge("Local LFM connected" if llama_server_available() else "LFM fallback mode", "ok" if llama_server_available() else "warn")
st.sidebar.caption(f"Knowledge files: {len(list(KNOWLEDGE_DIR.rglob('*.md'))) if KNOWLEDGE_DIR.exists() else 0}")
st.sidebar.caption(f"Tickets: {len(st.session_state.tickets)}")
if st.sidebar.button("Reset session", use_container_width=True):
    for key in [
        "employee_messages",
        "it_messages",
        "tickets",
        "audit_logs",
        "last_ticket",
        "active_error",
        "last_agent_events",
        "last_agent_evidence",
    ]:
        if key in st.session_state:
            del st.session_state[key]
    write_current_error_state(None)
    init_state()
    st.rerun()

if menu == "Employee Portal":
    st.markdown('<div class="kw-topbar"><div class="kw-title">Internal ERP Portal</div><div class="kw-subtitle">Employee transaction screen / SSO protected applications</div></div>', unsafe_allow_html=True)
    left, right = st.columns([1.45, 1.0], gap="large")

    with left:
        c1, c2 = st.columns(2)
        with c1:
            user = st.selectbox("Signed-in user", USERS, format_func=lambda u: f"{u['name']} / {u['dept']} / {u['role']}")
        with c2:
            scenario_key = st.selectbox("Inquiry scenario", list(SCENARIOS), index=list(SCENARIOS).index(st.session_state.scenario_key), format_func=lambda k: SCENARIOS[k]["label"])
            st.session_state.scenario_key = scenario_key
        scenario = SCENARIOS[scenario_key]

        st.markdown(f"#### Sign in to {scenario['system']}")
        email = st.text_input("Email", value=user["email"])
        st.text_input("Password", value="********", type="password")
        login_cols = st.columns([1, 1, 2])
        with login_cols[0]:
            sign_in = st.button("Sign in", type="primary", use_container_width=True)
        with login_cols[1]:
            report = st.button("Report issue", use_container_width=True)
        if sign_in or report:
            error_state = {
                "scenario_key": scenario_key,
                "system": scenario["system"],
                "title": scenario["title"],
                "error_text": scenario["error_text"],
                "error_code": scenario["error_code"],
                "symptom": scenario["symptom"],
                "category": scenario["category"],
                "risk": scenario["risk"],
                "priority": scenario["priority"],
                "route": scenario["route"],
                "impact": scenario["impact"],
                "trace_id": f"trc-{scenario_key.lower()}-{datetime.now().strftime('%H%M%S')}",
                "correlation_id": f"corr-{user['dept']}-{datetime.now().strftime('%Y%m%d')}",
                "timestamp": now_text(),
                "user_email": email,
                "user_name": user["name"],
                "department": user["dept"],
                "role": user["role"],
                "location": user["location"],
            }
            st.session_state.active_error = error_state
            write_current_error_state(error_state)
            st.session_state.last_agent_events = []
            st.session_state.last_agent_evidence = []
            add_audit("ERP Simulator", "error_log_created", scenario_key, scenario["error_code"], scenario["risk"])

        active_error = st.session_state.active_error if st.session_state.active_error and st.session_state.active_error["scenario_key"] == scenario_key else None
        if not active_error:
            pass
        elif scenario_key in ["CRM_MENU_MISSING", "POWERBI_DENIED"]:
            st.markdown(f"""
<div class="error-box">
<h4>Application access issue</h4>
<b>{scenario['title']}</b><br>
{scenario['error_text']}<br>
Trace ID: {active_error['trace_id']}<br>
Correlation ID: {active_error['correlation_id']}<br>
Timestamp: {active_error['timestamp']}
</div>
""", unsafe_allow_html=True)
        elif scenario_key == "MULTI_USER_OUTAGE":
            st.markdown(f"""
<div class="error-box">
<h4>Service access degraded</h4>
<b>{scenario['title']}</b><br>
{scenario['error_text']}<br>
Incident signal: multiple affected users<br>
Timestamp: {active_error['timestamp']}
</div>
""", unsafe_allow_html=True)
        else:
            st.markdown(f"""
<div class="error-box">
<h4>Sign-in failed</h4>
<b>{scenario['title']}</b><br>
Error Code: {scenario['error_code']}<br>
{scenario['error_text']}<br>
Trace ID: {active_error['trace_id']}<br>
Correlation ID: {active_error['correlation_id']}<br>
Timestamp: {active_error['timestamp']}
</div>
""", unsafe_allow_html=True)

    with right:
        evidence_preview = st.session_state.last_agent_evidence
        render_assistant_header(scenario)
        chat_placeholder = st.empty()
        render_chat_container(chat_placeholder, st.session_state.employee_messages)

        trace_placeholder = st.empty()
        if st.session_state.last_agent_events:
            activity_rows = ['<div class="activity-title">Agent activity</div>']
            for event in st.session_state.last_agent_events[-6:]:
                activity_rows.append(render_activity_event(event))
            trace_placeholder.markdown(f'<div class="activity-strip">{"".join(activity_rows)}</div>', unsafe_allow_html=True)
        render_evidence_chips(evidence_preview)

        prompt = st.chat_input("Message Agent P")
        if prompt and prompt.strip():
            run_employee_chat_live(prompt.strip(), scenario, user, trace_placeholder, chat_placeholder)
            st.rerun()

elif menu == "IT Operations":
    st.title("IT Operations Console")
    st.caption("Agent P から引き継がれた社内サポートチケット")
    if st.session_state.tickets:
        df = pd.DataFrame(st.session_state.tickets)
        for column, default in {
            "status": "New",
            "requester": "",
            "system": "",
            "category": "",
            "priority": "",
            "impact": "",
            "route": "",
        }.items():
            if column not in df.columns:
                df[column] = default
        left_it, right_it = st.columns([1.2, 1.0], gap="large")
        with left_it:
            st.dataframe(
                df[["ticket_id", "status", "requester", "system", "priority", "route"]],
                use_container_width=True,
                hide_index=True,
            )
            selected_id = st.selectbox("Open ticket", [t["ticket_id"] for t in st.session_state.tickets], label_visibility="collapsed")
        ticket = next(t for t in st.session_state.tickets if t["ticket_id"] == selected_id)
        with right_it:
            st.markdown(f"#### {ticket.get('ticket_id')} · {ticket.get('title', ticket.get('system', ''))}")
            st.markdown(
                f"""
**Status**: {ticket.get('status', 'New')}  
**Requester**: {ticket.get('requester', '')}  
**System**: {ticket.get('system', '')}  
**Category**: {ticket.get('category', '')}  
**Priority**: {ticket.get('priority', '')}  
**Route**: {ticket.get('route', '')}  
**Impact**: {ticket.get('impact', '')}  
**Trace ID**: {ticket.get('trace_id', '')}
"""
            )
            st.markdown("**Summary**")
            st.caption(ticket.get("summary", ""))
            evidence = ticket.get("evidence") or []
            if evidence:
                st.markdown("**Evidence**")
                for hit in evidence[:5]:
                    if hit.get("path") and hit.get("line"):
                        st.caption(f"{hit['path']}:{hit['line']} - {hit.get('snippet', '')}")
                    elif hit.get("raw"):
                        st.caption(str(hit["raw"]))
            blocked = ticket.get("blocked_actions") or []
            if blocked:
                st.markdown("**Blocked actions**")
                st.write(", ".join(blocked))
    else:
        st.info("No tickets yet. Create one from Employee Portal.")
    if st.session_state.it_messages:
        st.markdown("### Agent handoff")
        st.markdown(st.session_state.it_messages[-1]["content"], unsafe_allow_html=True)

elif menu == "Knowledge Search":
    st.title("Local Knowledge Search")
    st.caption("rg / grep style retrieval over local ERP, CRM, SSO, Power BI and security policies.")
    query = st.text_input("Search local policies", value="AADSTS50076")
    st.button("Run rg search", type="primary")
    hits = rg_search(query, limit=30) if query else []
    st.write(f"Found {len(hits)} snippets")
    if hits:
        st.dataframe(pd.DataFrame(hits), use_container_width=True, hide_index=True)
    else:
        st.warning("No local knowledge snippets found.")
    st.markdown("### Knowledge files")
    files = [{"path": str(p.relative_to(APP_DIR)), "lines": len(p.read_text(encoding="utf-8").splitlines())} for p in KNOWLEDGE_DIR.rglob("*.md")] if KNOWLEDGE_DIR.exists() else []
    st.dataframe(pd.DataFrame(files), use_container_width=True, hide_index=True)

else:
    st.title("Audit Log")
    st.caption("Agent decisions, evidence lookup, ticket handoff and blocked actions.")
    if st.session_state.audit_logs:
        st.dataframe(pd.DataFrame(st.session_state.audit_logs), use_container_width=True, hide_index=True)
    else:
        st.info("No audit events yet.")
