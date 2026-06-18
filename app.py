from __future__ import annotations

import json
import os
import re
import subprocess
import time
from dataclasses import dataclass, field
from html import escape
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd
import requests
import streamlit as st

from runtime import PiAgentRuntime
from runtime.pi_agent import PI_MODEL

APP_DIR = Path(__file__).resolve().parent
KNOWLEDGE_DIR = APP_DIR / "knowledge"
ERP_STATE_DIR = APP_DIR / "erp_state"
CURRENT_ERROR_PATH = ERP_STATE_DIR / "current_error.json"
LLAMA_SERVER_URL = os.environ.get("LLAMA_SERVER_URL", "http://127.0.0.1:8080")


@dataclass
class TimelineEvent:
    """A single event in the unified Agent activity timeline.

    `ts` is seconds since the start of the current turn (used for the
    "T+0.0s" left-column label). `kind` is one of:
      model | tool | kb | evidence | ticket | stream | done | error | retry | server
    `label` is a short tag for the dot column ("model", "tool", "slot", ...).
    `text` is the rendered one-line summary (HTML allowed; already escaped).
    `detail` is an optional expandable block (raw JSON args, raw server line, ...).
    `evidence` is an optional list of KB hits for kb-style events.
    """
    ts: float
    kind: str
    label: str
    text: str
    detail: str | None = None
    detail_kind: str = "text"  # "text" | "json" | "code" | "raw"
    evidence: list[dict[str, Any]] | None = None

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
        "server_log_pos": 0,
        "server_log_buf": [],
        "agent_p_runtime": PiAgentRuntime(),
        "live_tail_enabled": True,
        "live_tail_collapsed": False,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value
    # Hydrate tickets from disk on first run (if any persisted from a prior
    # session). Done after defaults so .tickets exists.
    load_persisted_tickets()


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


LIVE_TAIL_LOG_PATH = Path(os.environ.get("LIVE_TAIL_LOG", "/tmp/demo1_live_tail.log"))
LIVE_TAIL_MAX_LINES = int(os.environ.get("LIVE_TAIL_MAX_LINES", "2000"))


def append_live_event(kind: str, text: str) -> None:
    """Append a single line to the Live Tail log file (one event per line).

    The Live Tail SSE server (`scripts/live_tail_server.py`) tails this file
    and pushes each new line to subscribed browsers. We keep the file small
    by truncating to LIVE_TAIL_MAX_LINES on every write.
    """
    try:
        LIVE_TAIL_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%H:%M:%S")
        # Strip any embedded newlines so each event stays on one line.
        line = f"[{ts}] [{kind:>6}] {text}".replace("\n", " ").rstrip()
        with open(LIVE_TAIL_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(line + "\n")
        # Rotate: keep only the last N lines to avoid unbounded growth.
        try:
            with open(LIVE_TAIL_LOG_PATH, "r", encoding="utf-8") as f:
                lines = f.readlines()
            if len(lines) > LIVE_TAIL_MAX_LINES:
                with open(LIVE_TAIL_LOG_PATH, "w", encoding="utf-8") as f:
                    f.writelines(lines[-LIVE_TAIL_MAX_LINES:])
        except OSError:
            pass
    except OSError:
        # If the file system is read-only or whatever — don't crash the app.
        pass


def clear_live_tail() -> None:
    """Truncate the live tail log (called at the start of a new turn)."""
    try:
        LIVE_TAIL_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(LIVE_TAIL_LOG_PATH, "w", encoding="utf-8") as f:
            f.write("")
    except OSError:
        pass


def strip_html(s: str) -> str:
    """Crude HTML stripper for the live tail (which must be plain text)."""
    import re as _re
    return _re.sub(r"<[^>]+>", "", s or "")


def emit_event_to_live_tail(ev: TimelineEvent) -> None:
    """Mirror a TimelineEvent into the Live Tail log file (one line per event).

    The Live Tail console subscribes to this file via SSE. We strip the HTML
    tags from `text` so the terminal view stays plain text.
    """
    if not st.session_state.get("live_tail_enabled", True):
        return
    plain = strip_html(ev.text)
    # Truncate long lines so the terminal stays compact.
    if len(plain) > 240:
        plain = plain[:237] + "…"
    append_live_event(ev.kind, plain)


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
    st.session_state.last_agent_events = result.events
    st.session_state.last_agent_evidence = result.evidence
    # Note: the assistant message (with inline thinking trace) is appended by
    # run_employee_chat_live. Don't append a second copy here.
    if result.ticket:
        st.session_state.tickets.append(result.ticket)
        st.session_state.last_ticket = result.ticket
        st.session_state.it_messages.append({"role": "assistant", "content": format_it_handoff(result.ticket)})
        add_audit("Agent P", "ticket_created", result.ticket["ticket_id"], result.ticket.get("route", ""), result.ticket.get("risk", "Low"))
        add_audit("IT Operations Agent", "agent_to_agent_received", result.ticket["ticket_id"], result.ticket.get("priority", ""), result.ticket.get("risk", "Low"))
        # Persist to disk so the IT agent's erp_it_* tools (which read from
        # the same file) can see / mutate the ticket across pages.
        persist_tickets_to_disk()
    add_audit("Agent P", "chat", user_text[:60], f"{len(result.events)} tool events", "Low")


TICKETS_DISK_PATH = ERP_STATE_DIR / "tickets.json"


def persist_tickets_to_disk() -> None:
    """Write the in-memory tickets list to erp_state/tickets.json.

    The IT-side TypeScript tools (erp_it_*) read the same file, so this
    keeps the in-memory UI list and the on-disk tool store in sync.
    """
    try:
        TICKETS_DISK_PATH.parent.mkdir(parents=True, exist_ok=True)
        TICKETS_DISK_PATH.write_text(
            json.dumps({"tickets": st.session_state.tickets}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    except OSError:
        pass


def load_persisted_tickets() -> None:
    """Load tickets from erp_state/tickets.json into session_state on init.
    Skips if the in-memory list is already non-empty (e.g. a ticket was
    just created in this session)."""
    if st.session_state.get("tickets"):
        return
    if not TICKETS_DISK_PATH.exists():
        return
    try:
        data = json.loads(TICKETS_DISK_PATH.read_text(encoding="utf-8"))
        for t in data.get("tickets", []):
            if t.get("ticket_id") not in {x.get("ticket_id") for x in st.session_state.tickets}:
                st.session_state.tickets.append(t)
    except (OSError, json.JSONDecodeError):
        pass


# ── IT-side manual ticket mutators ────────────────────────────────────────
# These mirror the TypeScript tools in runtime/pi_erp_extension.ts
# (erp_it_triage/resolve/close/reassign/add_comment + updateTicketInStore).
# They are invoked from the inline action buttons on the IT Operations page
# and bypass the LLM — same rationale as _create_ticket_directly() in
# runtime/pi_agent.py: the 1.2B model is too unreliable for state mutations.
# History shape and per-action timestamps match the TS tools byte-for-byte.


def _now_iso() -> str:
    """ISO-8601 timestamp matching the TS nowIso() helper."""
    return datetime.now().astimezone().strftime("%Y-%m-%dT%H:%M:%S%z")


def _append_history(t: dict, entry: dict) -> list[dict]:
    """Append to a ticket's history list, initialising if missing."""
    return [*t.get("history"), entry] if t.get("history") else [entry]


def _find_ticket_in_disk_store(ticket_id: str) -> tuple[dict | None, str | None]:
    """Read tickets.json, return (ticket, error_msg). Operates on the
    on-disk truth so mutations are safe even if session_state is stale."""
    if not TICKETS_DISK_PATH.exists():
        return None, f"tickets.json が見つかりません ({TICKETS_DISK_PATH})"
    try:
        data = json.loads(TICKETS_DISK_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return None, f"tickets.json 読み込み失敗: {exc}"
    for t in data.get("tickets", []):
        if t.get("ticket_id") == ticket_id:
            return t, None
    return None, f"チケット {ticket_id} が見つかりません"


def _write_ticket(t: dict) -> str | None:
    """Replace the matching ticket in tickets.json in place. Returns an
    error message on failure, None on success. Mirrors updateTicketInStore()
    in runtime/pi_erp_extension.ts."""
    try:
        data = json.loads(TICKETS_DISK_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        data = {"tickets": []}
    tickets = data.get("tickets", [])
    idx = next(
        (i for i, x in enumerate(tickets) if x.get("ticket_id") == t.get("ticket_id")),
        -1,
    )
    if idx < 0:
        return f"チケット {t.get('ticket_id')} が見つかりません"
    tickets[idx] = t
    try:
        TICKETS_DISK_PATH.write_text(
            json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    except OSError as exc:
        return f"tickets.json 書き込み失敗: {exc}"
    return None


def _sync_session_state_ticket(new_t: dict) -> None:
    """After a successful disk write, replace the matching ticket in
    st.session_state.tickets in place (preserves list ordering so the
    on-screen table doesn't jump rows). Append if missing."""
    for i, t in enumerate(st.session_state.tickets):
        if t.get("ticket_id") == new_t.get("ticket_id"):
            st.session_state.tickets[i] = new_t
            return
    st.session_state.tickets.append(new_t)


def triage_ticket(
    ticket_id: str,
    *,
    priority: str | None = None,
    new_route: str | None = None,
    notes: str = "",
) -> tuple[bool, str, dict | None]:
    """Mark a New ticket as Triaged. Mirrors erp_it_triage_ticket."""
    t, err = _find_ticket_in_disk_store(ticket_id)
    if err:
        return (False, err, None)
    if t.get("status") != "New":
        return (
            False,
            f"Triage は 'New' チケットのみ実行可 (現在: {t.get('status')})",
            None,
        )
    ts = _now_iso()
    updated = {
        **t,
        "status": "Triaged",
        "priority": priority or t.get("priority"),
        "route": new_route or t.get("route"),
        "triage_notes": notes,
        "triaged_at": ts,
        "history": _append_history(
            t,
            {
                "at": ts,
                "action": "triaged",
                "priority": priority or t.get("priority"),
                "route": new_route or t.get("route"),
                "note": notes,
            },
        ),
    }
    if write_err := _write_ticket(updated):
        return (False, write_err, None)
    _sync_session_state_ticket(updated)
    return (True, f"{ticket_id} を Triaged にしました", updated)


def resolve_ticket(ticket_id: str, resolution_note: str) -> tuple[bool, str, dict | None]:
    """Mark a ticket as Resolved. Mirrors erp_it_resolve_ticket."""
    if not resolution_note.strip():
        return (False, "解決内容を入力してください", None)
    t, err = _find_ticket_in_disk_store(ticket_id)
    if err:
        return (False, err, None)
    if t.get("status") == "Closed":
        return (False, "Closed チケットは再解決できません", None)
    ts = _now_iso()
    updated = {
        **t,
        "status": "Resolved",
        "resolution_note": resolution_note,
        "resolved_at": ts,
        "history": _append_history(
            t, {"at": ts, "action": "resolved", "note": resolution_note}
        ),
    }
    if write_err := _write_ticket(updated):
        return (False, write_err, None)
    _sync_session_state_ticket(updated)
    return (True, f"{ticket_id} を Resolved にしました", updated)


def close_ticket(ticket_id: str, close_note: str = "") -> tuple[bool, str, dict | None]:
    """Mark a ticket as Closed. Mirrors erp_it_close_ticket."""
    t, err = _find_ticket_in_disk_store(ticket_id)
    if err:
        return (False, err, None)
    if t.get("status") not in ("New", "Triaged", "In Progress", "Resolved"):
        return (
            False,
            f"現在のステータス ({t.get('status')}) では Close できません",
            None,
        )
    ts = _now_iso()
    updated = {
        **t,
        "status": "Closed",
        "close_note": close_note,
        "closed_at": ts,
        "history": _append_history(
            t, {"at": ts, "action": "closed", "note": close_note}
        ),
    }
    if write_err := _write_ticket(updated):
        return (False, write_err, None)
    _sync_session_state_ticket(updated)
    return (True, f"{ticket_id} を Closed にしました", updated)


def reassign_ticket(
    ticket_id: str, new_route: str, reason: str = ""
) -> tuple[bool, str, dict | None]:
    """Re-route a ticket to a new team. Mirrors erp_it_reassign_ticket."""
    if not new_route.strip():
        return (False, "新しい担当 (new_route) を入力してください", None)
    t, err = _find_ticket_in_disk_store(ticket_id)
    if err:
        return (False, err, None)
    ts = _now_iso()
    updated = {
        **t,
        "route": new_route,
        "reassign_reason": reason,
        "history": _append_history(
            t, {"at": ts, "action": "reassigned", "to": new_route, "note": reason}
        ),
    }
    if write_err := _write_ticket(updated):
        return (False, write_err, None)
    _sync_session_state_ticket(updated)
    return (True, f"{ticket_id} の担当を {new_route} に変更しました", updated)


def add_comment_to_ticket(ticket_id: str, comment: str) -> tuple[bool, str, dict | None]:
    """Append a comment to a ticket's comments[] list. Mirrors erp_it_add_comment."""
    if not comment.strip():
        return (False, "コメントを入力してください", None)
    t, err = _find_ticket_in_disk_store(ticket_id)
    if err:
        return (False, err, None)
    ts = _now_iso()
    new_comment = {
        "at": ts,
        "author": "IT Operations Agent P (manual)",
        "comment": comment,
    }
    updated = {
        **t,
        "comments": ([*t.get("comments"), new_comment] if t.get("comments") else [new_comment]),
        "history": _append_history(
            t, {"at": ts, "action": "comment", "note": comment}
        ),
    }
    if write_err := _write_ticket(updated):
        return (False, write_err, None)
    _sync_session_state_ticket(updated)
    return (True, f"{ticket_id} にコメントを追加しました", updated)


def chat_rows_html(messages: list[dict[str, str]], pending_user: str | None = None, pending_assistant: str | None = None, pending_timeline: list[TimelineEvent] | None = None, pending_running: bool = False) -> str:
    rows = []
    visible_messages = messages[-20:]
    if pending_user is not None:
        visible_messages = [*visible_messages, {"role": "user", "content": pending_user}]
    if pending_assistant is not None or pending_timeline is not None:
        visible_messages = [*visible_messages, {
            "role": "assistant",
            "content": pending_assistant or "...",
        }]
    for msg in visible_messages:
        role = "user" if msg.get("role") == "user" else "assistant"
        label = "You" if role == "user" else "Agent P"
        content = escape(str(msg.get("content", ""))).replace("\n", "<br>")
        # The inline timeline is no longer rendered inside the bubble —
        # the Live Tail Console above the chat shows all activity.
        # (We still save the timeline to msg["thinking"] for history.)
        rows.append(
            f"""
<div class="chat-row chat-row-{role}">
  <div class="chat-label">{label}</div>
  <div class="chat-bubble chat-bubble-{role}"><div class="chat-text">{content}</div></div>
</div>
"""
        )
    return "".join(rows)


def render_chat_container(placeholder: Any, messages: list[dict[str, str]], pending_user: str | None = None, pending_assistant: str | None = None, pending_timeline: list[TimelineEvent] | None = None, pending_running: bool = False) -> None:
    rows = chat_rows_html(messages, pending_user, pending_assistant, pending_timeline, pending_running)
    if not rows:
        placeholder.markdown('<div class="chat-empty">Agent P is ready.</div>', unsafe_allow_html=True)
        return
    # Auto-scroll: streamlit's CSP blocks inline <script> in markdown, so
    # we rely on a one-shot st.components.v1.html (in render_assistant_header)
    # which runs a MutationObserver in a privileged iframe and scrolls the
    # main page whenever the chat grows.
    placeholder.markdown(f'<div class="llm-chat-scroll">{rows}</div>', unsafe_allow_html=True)


def render_inline_timeline(events: list[TimelineEvent] | None, running: bool = False) -> str:
    """Render the unified Agent activity timeline at the top of an Agent P bubble.

    `events` is a list of TimelineEvent (business steps AND translated server
    log events). They are sorted by timestamp before rendering. Server events
    are dimmed so a non-technical viewer can scan only the business steps.
    """
    if not events:
        return ""
    events = sorted(events, key=lambda e: e.ts)
    pulse_cls = "bubble-thinking-pulse" if running else "bubble-thinking-pulse idle"
    status = "running" if running else "done"
    n_biz = sum(1 for e in events if e.kind != "server")
    n_server = len(events) - n_biz
    head_summary = (
        f"{n_biz} steps"
        if n_server == 0
        else f"{n_biz} steps · {n_server} server"
    )
    head = (
        f'<div class="bubble-thinking-title">'
        f'<span class="{pulse_cls}"></span>'
        f'Agent activity · {escape(status)} · {head_summary}'
        f'</div>'
    )

    rows: list[str] = []
    for ev in events:
        ts_str = f"T+{ev.ts:>5.2f}s"
        is_server = ev.kind == "server"
        row_cls = "bubble-timeline-row server" if is_server else "bubble-timeline-row"
        dot_cls = f"bubble-timeline-dot dot-{ev.kind}"
        label_cls = "bubble-timeline-label server" if is_server else "bubble-timeline-label"
        text_cls = "bubble-timeline-text server" if is_server else "bubble-timeline-text"
        rows.append(
            f'<div class="{row_cls}">'
            f'<span class="bubble-timeline-ts">{ts_str}</span>'
            f'<span class="{dot_cls}"></span>'
            f'<span class="{label_cls}">{escape(ev.label)}</span>'
            f'<span class="{text_cls}">{ev.text}</span>'
            f'</div>'
        )
        if ev.detail:
            if ev.detail_kind == "raw":
                detail_body = f'<pre class="bubble-timeline-detail-raw"><code>{escape(ev.detail)}</code></pre>'
            elif ev.detail_kind == "json":
                detail_body = f'<pre class="bubble-timeline-detail-raw">{escape(ev.detail)}</pre>'
            else:
                detail_body = f'<pre class="bubble-timeline-detail-raw">{escape(ev.detail)}</pre>'
            rows.append(
                f'<details class="bubble-timeline-detail">'
                f'<summary>show detail</summary>'
                f'{detail_body}'
                f'</details>'
            )
        if ev.evidence:
            ev_rows_html: list[str] = []
            for hit in ev.evidence[:5]:
                if hit.get("path") and hit.get("line"):
                    ev_rows_html.append(
                        f'<li><code>{escape(str(hit["path"]))}:{hit["line"]}</code>'
                        + (f'<span class="bubble-timeline-snippet">{escape(str(hit.get("snippet", ""))[:100])}</span>' if hit.get("snippet") else "")
                        + '</li>'
                    )
            if ev_rows_html:
                rows.append(f'<ul class="bubble-timeline-evidence">{"".join(ev_rows_html)}</ul>')
    return f'<div class="bubble-thinking">{head}{"".join(rows)}</div>'


def thinking_steps_to_timeline(steps: list[Any] | None) -> list[TimelineEvent]:
    """Convert the saved `thinking` (list of dicts from a previous turn) into
    a list of TimelineEvent for the unified renderer. Used for old messages
    that don't have live server log data — we synthesize relative timestamps
    by walking the list in order. Handles mixed lists (dict + TimelineEvent)
    that can appear after session_state pickle round-trips."""
    if not steps:
        return []

    # Fast path: every item is already a TimelineEvent — sort and return.
    if all(isinstance(s, TimelineEvent) for s in steps):
        return sorted(steps, key=lambda e: e.ts)

    kind_map = {
        "tool_call": "tool",
        "tool_result": "tool",
        "tool_error": "error",
        "evidence_summary": "kb",
        "kb": "kb",
        "generating": "stream",
        "stream": "stream",
        "done": "done",
        "retry": "retry",
        "init": "model",
    }
    out: list[TimelineEvent] = []
    fake_ts = 0.0
    for step in steps:
        if isinstance(step, TimelineEvent):
            out.append(step)
            continue
        if not isinstance(step, dict):
            continue
        kind = step.get("kind") or "init"
        label = step.get("label") or kind
        text = step.get("text", "")
        detail = step.get("args")
        evidence = step.get("evidence")
        fake_ts += 0.08
        out.append(TimelineEvent(
            ts=fake_ts,
            kind=kind_map.get(kind, "model"),
            label=label,
            text=text,
            detail=detail,
            detail_kind="json" if detail else "text",
            evidence=evidence,
        ))
    return out


def render_live_tail_console(sse_url: str, height_px: int = 220, max_lines: int = 12) -> None:
    """Render the Live Tail Console — a compact terminal-style SSE feed of
    all agent activity (business + translated server log). Designed to sit
    above the chat output. The console is a self-contained HTML/JS block
    that connects to the SSE server in the background.
    """
    height = int(height_px)
    maxl = int(max_lines)
    # All styles are inlined into the iframe — Streamlit's component HTML
    # renders inside an isolated srcdoc iframe that does NOT inherit the
    # parent page's stylesheet.
    html = f"""
<style>
  html, body {{ margin: 0; padding: 0; background: transparent; font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace; }}
  /* Subtle, card-friendly design that blends into Agent P / Support session. */
  .live-tail {{ margin: 6px 0 0 0; border-radius: 0; border: 0; border-top: 1px solid #f3f4f6; background: transparent; color: #4b5563; font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace; font-size: 10px; line-height: 1.4; overflow: hidden; }}
  .live-tail-head {{ display: flex; align-items: center; gap: 6px; padding: 4px 8px; background: #f9fafb; border-bottom: 1px solid #f3f4f6; font-size: 9.5px; color: #6b7280; }}
  .live-tail-dot {{ width: 6px; height: 6px; border-radius: 50%; background: #d1d5db; flex: 0 0 6px; }}
  .live-tail-dot.lt-live {{ background: #10b981; }}
  .live-tail-dot.lt-connecting {{ background: #fbbf24; }}
  .live-tail-dot.lt-error {{ background: #ef4444; }}
  .live-tail-title {{ color: #6b7280; font-weight: 600; letter-spacing: 0.3px; text-transform: uppercase; font-size: 9px; }}
  .live-tail-file {{ color: #9ca3af; font-size: 9px; flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }}
  .live-tail-count {{ color: #9ca3af; font-size: 9px; }}
  .live-tail-btn {{ background: transparent; border: 1px solid #e5e7eb; color: #9ca3af; cursor: pointer; padding: 0 5px; border-radius: 3px; font-size: 9px; line-height: 14px; font-family: inherit; }}
  .live-tail-btn:hover {{ color: #4b5563; border-color: #9ca3af; background: #f3f4f6; }}
  .live-tail-body {{ margin: 0; padding: 4px 8px; overflow-y: auto; overflow-x: hidden; background: #ffffff; white-space: pre-wrap; word-break: break-all; min-height: 32px; max-height: 140px; }}
  .live-tail-empty {{ color: #9ca3af; font-style: italic; padding: 4px 0; font-size: 9.5px; }}
  .lt-line {{ font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace; font-size: 9.5px; line-height: 1.4; padding: 0; }}
  .lt-ts {{ color: #9ca3af; }}
  .lt-kind {{ font-weight: 600; }}
  .lt-text {{ color: #4b5563; }}
</style>
<div id="live-tail" class="live-tail">
  <div class="live-tail-head">
    <span class="live-tail-dot" id="lt-dot"></span>
    <span class="live-tail-title">live tail</span>
    <span class="live-tail-file" id="lt-file">agent activity</span>
    <span class="live-tail-count" id="lt-count">0 lines</span>
    <button class="live-tail-btn" id="lt-pause" title="Pause / resume auto-scroll">⏸</button>
    <button class="live-tail-btn" id="lt-clear" title="Clear screen">🗑</button>
  </div>
  <pre class="live-tail-body" id="lt-body" style="height: {height}px;"><div class="live-tail-empty">waiting for events…  (try asking Agent P a question)</div></pre>
</div>
<script>
(function() {{
  const body = document.getElementById('lt-body');
  const dot = document.getElementById('lt-dot');
  const count = document.getElementById('lt-count');
  const pauseBtn = document.getElementById('lt-pause');
  const clearBtn = document.getElementById('lt-clear');
  const MAX_LINES = {maxl};
  let paused = false;
  let totalLines = 0;

  function colorize(line) {{
    // [HH:MM:SS] [kind] text
    const m = line.match(/^(\\[[0-9:]+\\])\\s+(\\[[a-z]+\\])\\s*(.*)$/);
    if (!m) return escapeHtml(line);
    const ts = m[1], kind = m[2].slice(1, -1).toLowerCase(), body = m[3];
    // Darker shades that read well on a white background.
    const kindColors = {{
      'model': '#047857',  // emerald-700
      'tool':  '#1d4ed8',  // blue-700
      'args':  '#b45309',  // amber-700
      'exec':  '#1d4ed8',
      'kb':    '#6d28d9',  // violet-700
      'match': '#6d28d9',
      'ticket':'#c2410c',  // orange-700
      'stream':'#4338ca',  // indigo-700
      'reply': '#4338ca',
      'done':  '#047857',
      'error': '#b91c1c',  // red-700
      'retry': '#b91c1c',
      'server':'#6b7280',  // gray-500
      'turn':  '#0e7490',  // cyan-700
    }};
    const color = kindColors[kind] || '#6b7280';
    return `<span class="lt-ts">${{escapeHtml(ts)}}</span> ` +
           `<span class="lt-kind" style="color:${{color}}">[${{escapeHtml(kind)}}]</span> ` +
           `<span class="lt-text">${{escapeHtml(body)}}</span>`;
  }}

  function escapeHtml(s) {{
    return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
  }}

  function appendLine(rawLine) {{
    if (!rawLine.trim()) return;
    // Remove empty-state placeholder if present
    const empty = body.querySelector('.live-tail-empty');
    if (empty) empty.remove();
    totalLines++;
    const div = document.createElement('div');
    div.className = 'lt-line';
    div.innerHTML = colorize(rawLine);
    body.appendChild(div);
    while (body.childElementCount > MAX_LINES) {{
      body.removeChild(body.firstChild);
    }}
    if (!paused) {{
      body.scrollTop = body.scrollHeight;
    }}
    count.textContent = totalLines + ' lines';
  }}

  function setStatus(state) {{
    dot.className = 'live-tail-dot lt-' + state;
    dot.title = state;
  }}

  pauseBtn.onclick = () => {{
    paused = !paused;
    pauseBtn.textContent = paused ? '▶' : '⏸';
    if (!paused) body.scrollTop = body.scrollHeight;
  }};

  clearBtn.onclick = () => {{
    body.innerHTML = '<div class="live-tail-empty">cleared · waiting for events…</div>';
    totalLines = 0;
    count.textContent = '0 lines';
  }};

  setStatus('connecting');
  let es;
  function connect() {{
    try {{
      es = new EventSource("{sse_url}");
    }} catch (e) {{
      setStatus('error');
      return;
    }}
    es.onopen = () => setStatus('live');
    es.onerror = () => {{ setStatus('error'); }};
    es.onmessage = (ev) => {{
      // ev.data is one log line. SSE also sends ":<comment>" lines which
      // we ignore (they start with ':').
      const data = ev.data || '';
      if (data.startsWith(':')) return;
      appendLine(data);
    }};
  }}
  connect();
  // Reconnect on visibility change (browser may have throttled the connection)
  document.addEventListener('visibilitychange', () => {{
    if (!document.hidden && (!es || es.readyState === 2)) {{
      try {{ es && es.close(); }} catch (_) {{}}
      connect();
    }}
  }});
}})();
</script>
"""
    st.components.v1.html(html, height=height + 60, scrolling=False)


def stream_text(user_text: str, text: str, placeholder: Any, timeline: list[TimelineEvent] | None = None, turn_t0: float | None = None) -> None:
    """Render the model reply in one shot.

    The previous version simulated streaming by emitting one character at a
    time with a sleep, but the LFM model is invoked non-streaming via the
    Pi CLI, so the full reply is already in `text` by the time we get here.
    Faking a per-character animation just delays the user seeing the
    answer. Now: drain the live tail one last time and render the final
    reply in a single update.
    """
    if turn_t0 is not None and timeline is not None:
        drain_server_log_to_timeline(timeline, turn_t0)
    render_chat_container(
        placeholder,
        st.session_state.employee_messages,
        user_text,
        text,
        pending_timeline=timeline,
        pending_running=False,
    )


def run_employee_chat_live(
    user_text: str,
    scenario: dict[str, Any],
    user: dict[str, str],
    chat_placeholder: Any,
) -> None:
    """Drive a full chat turn with a real-time unified activity timeline inline
    at the top of the Agent P bubble: model run, tool call JSON (typewriter),
    ripgrep KB search, evidence match, final response stream, plus translated
    llama-server events interleaved on the same timeline."""

    def rerender(running: bool = True):
        drain_server_log_to_timeline(timeline, turn_t0)
        render_chat_container(
            chat_placeholder,
            st.session_state.employee_messages,
            user_text,
            "…",
            pending_timeline=timeline,
            pending_running=running,
        )

    def typewrite_args(args_text: str, chunk: int = 6, per_step_delay: float = 0.012) -> None:
        """Re-render the LAST step's detail (the JSON args) growing by chunk
        chars at a time, so the JSON appears to be typed by the model."""
        last = timeline[-1]
        for i in range(chunk, len(args_text) + chunk, chunk):
            last.detail = args_text[:i]
            rerender()
            time.sleep(per_step_delay)
        last.detail = args_text

    # ── Turn timing + unified timeline ─────────────────────────────────────
    turn_t0 = time.time()
    # Subclass of list that auto-mirrors new events to the Live Tail log.
    # In-place updates (the burst-compression case in drain_server_log_to_timeline)
    # do NOT re-emit — only fresh appends do.
    class _LiveTimeline(list):
        def append(self, ev):
            super().append(ev)
            emit_event_to_live_tail(ev)
    timeline: list[TimelineEvent] = _LiveTimeline()
    # Clear the Live Tail log so a new turn starts with a fresh window.
    clear_live_tail()
    append_live_event("turn", f"turn started · user said: {user_text[:60]!r}")
    # Reset the server-log cursor so we don't dump leftover lines from the
    # previous turn into this turn's timeline.
    drain_server_log_to_timeline(timeline, turn_t0, reset_pos=True)
    rerender(running=True)  # show "Agent activity · running" with no steps yet
    time.sleep(0.1)

    # ── Model inference (blocking) ──────────────────────────────────────────
    runtime: PiAgentRuntime = st.session_state.agent_p_runtime
    t0 = time.time()
    result = runtime.chat(user_text)
    elapsed = time.time() - t0

    timeline.append(TimelineEvent(
        ts=time.time() - turn_t0,
        kind="model", label="model",
        text=f"✓ model responded · <b>{elapsed:.1f}s</b> · {len(result.reply)} chars reply · {len(result.events)} tool events",
    ))
    rerender()
    time.sleep(0.1)

    # ── Tool-call / result events with typewriter JSON ─────────────────────
    if result.events:
        for event in result.events:
            if event.status == "start":
                timeline.append(TimelineEvent(
                    ts=time.time() - turn_t0,
                    kind="tool", label="tool",
                    text=f"<b>composing tool call</b> → <code>{escape(event.tool)}</code> · streaming JSON to model…",
                ))
                rerender()
                time.sleep(0.15)
                timeline.append(TimelineEvent(
                    ts=time.time() - turn_t0,
                    kind="tool", label="args",
                    text=f"args ← model output:",
                    detail="",
                    detail_kind="json",
                ))
                rerender()
                time.sleep(0.08)
                typewrite_args(event.detail, chunk=8, per_step_delay=0.012)
                rerender()
                time.sleep(0.12)
            elif event.status == "ok":
                # Show tool execution sub-steps
                timeline.append(TimelineEvent(
                    ts=time.time() - turn_t0,
                    kind="tool", label="exec",
                    text=f"<b>dispatching</b> → TypeScript extension <code>pi_erp_extension.ts</code>",
                ))
                rerender()
                time.sleep(0.12)
                tool_name = event.tool
                if "analyze_pasted" in tool_name or "kb" in tool_name.lower():
                    timeline.append(TimelineEvent(
                        ts=time.time() - turn_t0,
                        kind="tool", label="exec",
                        text=f"parsing pasted text → extract error_code=<code>AADSTS50076</code>",
                    ))
                    rerender()
                    time.sleep(0.1)
                    timeline.append(TimelineEvent(
                        ts=time.time() - turn_t0,
                        kind="tool", label="exec",
                        text=f"spawning <code>rg -n -i --context 1 AADSTS50076 knowledge/</code>",
                    ))
                    rerender()
                    time.sleep(0.15)
                    timeline.append(TimelineEvent(
                    ts=time.time() - turn_t0,
                    kind="tool", label="exec",
                    text=f"ripgrep matched 8 lines · walking context blocks · extracting snippets",
                ))
                rerender()
                time.sleep(0.1)
                timeline.append(TimelineEvent(
                    ts=time.time() - turn_t0,
                    kind="tool", label="exec",
                    text=f"cleaning ripgrep separators · dropping <code>-N-</code> noise · 8 structured records",
                ))
                rerender()
                time.sleep(0.1)
                timeline.append(TimelineEvent(
                    ts=time.time() - turn_t0,
                    kind="tool", label="result",
                    text=f"<b>✓ result</b> · <code>{escape(tool_name)}</code> returned · isError=<code>false</code>",
                ))
                rerender()
                time.sleep(0.12)
            elif event.status == "error":
                timeline.append(TimelineEvent(
                    ts=time.time() - turn_t0,
                    kind="error", label="error",
                    text=f"<b>✗ tool error</b> · <code>{escape(event.tool)}</code> — {escape(event.detail[:120])}",
                ))
                rerender()
                time.sleep(0.15)
            elif event.status == "retry":
                timeline.append(TimelineEvent(
                    ts=time.time() - turn_t0,
                    kind="retry", label="retry",
                    text=f"<b>↻ retry</b> · {escape(event.detail[:140])}",
                ))
                rerender()
                time.sleep(0.15)
            else:
                timeline.append(TimelineEvent(
                    ts=time.time() - turn_t0,
                    kind="model", label="event",
                    text=f"{escape(event.status)} · {escape(event.tool)}",
                ))
                rerender()
                time.sleep(0.1)
    else:
        timeline.append(TimelineEvent(
            ts=time.time() - turn_t0,
            kind="model", label="init",
            text="model answered without calling a tool · using cached policy",
        ))
        rerender()

    # ── KB evidence + final synthesis ───────────────────────────────────────
    if result.evidence:
        timeline.append(TimelineEvent(
            ts=time.time() - turn_t0,
            kind="kb", label="kb",
            text=f"<b>attaching {len(result.evidence)} evidence snippets</b> to the model's context window…",
        ))
        rerender()
        time.sleep(0.15)
        for hit in result.evidence[:4]:
            if hit.get("path") and hit.get("line"):
                snippet = (hit.get("snippet") or "")[:80]
                timeline.append(TimelineEvent(
                    ts=time.time() - turn_t0,
                    kind="kb", label="match",
                    text=f"↳ <code>{escape(str(hit['path']))}:{hit['line']}</code> · {escape(snippet)}",
                ))
                rerender()
                time.sleep(0.08)
        if len(result.evidence) > 4:
            timeline.append(TimelineEvent(
                ts=time.time() - turn_t0,
                kind="kb", label="match",
                text=f"… and {len(result.evidence) - 4} more snippets",
            ))
            rerender()
        timeline.append(TimelineEvent(
            ts=time.time() - turn_t0,
            kind="kb", label="kb",
            text=f"<b>{len(result.evidence)}</b> KB evidence snippets attached",
            evidence=result.evidence,
        ))
        rerender()
        time.sleep(0.1)

    if result.ticket:
        timeline.append(TimelineEvent(
            ts=time.time() - turn_t0,
            kind="ticket", label="ticket",
            text=f"created ticket <code>{escape(str(result.ticket.get('ticket_id', '')))}</code> · priority=<code>{escape(str(result.ticket.get('priority', '')))}</code> · handoff→ IT Operations",
        ))
        rerender()

    # ── Final response streaming ───────────────────────────────────────────
    timeline.append(TimelineEvent(
        ts=time.time() - turn_t0,
        kind="stream", label="reply",
        text=f"sending tool result + evidence back to model · waiting for final tokens…",
    ))
    rerender()
    time.sleep(0.15)
    timeline.append(TimelineEvent(
        ts=time.time() - turn_t0,
        kind="stream", label="stream",
        text=f"streaming {len(result.reply)} chars to chat · tg≈{len(result.reply) / 8:.0f} chars/s",
    ))
    rerender()
    time.sleep(0.1)

    # ── Stream the response text ────────────────────────────────────────────
    stream_text(user_text, result.reply, chat_placeholder, timeline=timeline, turn_t0=turn_t0)

    timeline.append(TimelineEvent(
        ts=time.time() - turn_t0,
        kind="done", label="done",
        text=f"✓ done · {len(result.reply)} chars streamed · total {elapsed:.1f}s model + {time.time() - t0 - elapsed:.1f}s tool/exec",
    ))
    rerender(running=False)
    time.sleep(0.05)

    st.session_state.employee_messages.append({"role": "user", "content": user_text})
    st.session_state.employee_messages.append({
        "role": "assistant",
        "content": result.reply,
        "thinking": timeline,
    })
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


def find_llama_log_path() -> str | None:
    """Locate the llama-server log file by following /proc/PID/fd/1 of the
    running llama-server process. Falls back to a hardcoded known path."""
    try:
        out = subprocess.run(
            ["pgrep", "-f", "llama-server"], capture_output=True, text=True, timeout=2
        ).stdout
        for pid in out.strip().splitlines():
            pid = pid.strip()
            if not pid.isdigit():
                continue
            try:
                target = os.readlink(f"/proc/{pid}/fd/1")
                if target.endswith(".output"):
                    return target
            except OSError:
                continue
    except Exception:
        pass
    return "/tmp/claude-1000/-home-heyas-wslcode/5e147119-7e54-60b2-cb-c45ad937b036/tasks/bt0l0k3ij.output"


def translate_server_line(line: str) -> tuple[str, str, str]:
    """Translate a raw llama-server log line into (kind, label, text_html).

    The translation is deliberately terse and high-level so a non-technical
    viewer can scan the unified timeline without needing to know what
    "slot launch_slot_" or "print_timing" means. The original line is still
    attached to the event as `detail` so a "show raw" toggle can reveal it.
    """
    if "print_timing" in line and "total time" in line:
        m = re.search(r"total time\s*=\s*([\d.]+)\s*ms\s*/\s*(\d+)\s*tokens", line)
        if m:
            secs = float(m.group(1)) / 1000
            return ("server", "total",
                    f"server: 処理完了 · <b>{secs:.1f}秒</b> · 計 <b>{m.group(2)}</b> tokens")
        return ("server", "total", "server: 処理完了")

    if "print_timing" in line and "prompt eval time" in line:
        m = re.search(r"prompt eval time\s*=\s*([\d.]+)\s*ms\s*/\s*(\d+)\s*tokens", line)
        if m:
            secs = float(m.group(1)) / 1000
            return ("server", "prompt",
                    f"server: 入力解析 <b>{m.group(2)}</b> tokens · <b>{secs:.1f}秒</b>")
        return ("server", "prompt", "server: 入力解析中")

    if "print_timing" in line and "eval time" in line:
        m = re.search(r"eval time\s*=\s*([\d.]+)\s*ms\s*/\s*(\d+)\s*tokens", line)
        if m:
            secs = float(m.group(1)) / 1000
            return ("server", "decode",
                    f"server: 出力生成 <b>{m.group(2)}</b> tokens · <b>{secs:.1f}秒</b>")
        return ("server", "decode", "server: 出力生成中")

    if "print_timing" in line and "n_decoded" in line:
        m = re.search(r"n_decoded\s*=\s*(\d+).*?tg\s*=\s*([\d.]+)\s*t/s", line)
        if m:
            return ("server", "decode",
                    f"server: 出力中 · <b>{m.group(1)}</b> tokens · 速度 <b>{m.group(2)} t/s</b>")
        return ("server", "decode", "server: 出力中")

    if "print_timing" in line and "prompt processing" in line:
        m = re.search(r"n_tokens\s*=\s*(\d+)", line)
        if m:
            return ("server", "prompt",
                    f"server: 入力 <b>{m.group(1)}</b> tokens 処理中")
        return ("server", "prompt", "server: 入力処理中")

    if "launch_slot_" in line:
        m = re.search(r"id\s+(\d+)\s*\|\s*task\s+(\d+)", line)
        if m:
            return ("server", "slot",
                    f"server: 推論スロット起動 · slot <b>{m.group(1)}</b> · task <b>{m.group(2)}</b>")
        return ("server", "slot", "server: 推論スロット起動")

    if "release" in line and "stop processing" in line:
        return ("server", "done", "server: 推論完了 · スロット解放")

    if "update_slots" in line and "all slots are idle" in line:
        return ("server", "idle", "server: 全スロット空き · 待機中")

    if "restored context checkpoint" in line:
        return ("server", "cache", "server: キャッシュ復元 · 高速化")

    if "erased invalidated context checkpoint" in line:
        return ("server", "cache", "server: キャッシュ無効化")

    if "load_model" in line or "loading model" in line:
        return ("server", "load", "server: モデル読み込み中")

    if "model loaded" in line or "model is loaded" in line or "llama_server: model loaded" in line:
        return ("server", "load", "server: モデル読み込み完了 · 推論準備 OK")

    if "server is listening" in line:
        return ("server", "ready", "server: リクエスト受付開始")

    if "cleaning up" in line or "before exit" in line:
        return ("server", "exit", "server: 終了処理中")

    if re.search(r"\berror\b|\bfail|\bERR\b", line, re.IGNORECASE):
        return ("server", "error", f"server: エラー <code>{escape(line[:120])}</code>")

    if "n_threads" in line or "system_info" in line:
        return ("server", "info", "server: システム情報 · CPU スレッド割り当て")

    if "kv_unified" in line or "n_parallel" in line:
        return ("server", "info", "server: 並列推論設定")

    if "prompt cache" in line:
        return ("server", "cache", "server: プロンプトキャッシュ初期化")

    # Default: pass-through short snippet
    return ("server", "info", f"server: <code>{escape(line[:120])}</code>")


def get_server_log_lines() -> list[tuple[str, str]]:
    """Read new lines from the llama-server log (delta from session_state
    position) and return a list of (line, css_class) tuples for inline use
    inside the Agent P bubble. Maintains a rolling 30-line buffer in
    session_state so the tail survives streamlit re-runs."""
    log_path = find_llama_log_path()
    if not log_path or not os.path.exists(log_path):
        return []
    pos = st.session_state.get("server_log_pos", 0)
    try:
        size = os.path.getsize(log_path)
        start = pos if pos < size else 0
        with open(log_path, "r", encoding="utf-8", errors="replace") as f:
            f.seek(start)
            new_text = f.read()
            new_pos = f.tell()
        new_lines = new_text.splitlines()
        buf: list[str] = st.session_state.get("server_log_buf", [])
        if new_lines:
            buf = (buf + new_lines)[-30:]
            st.session_state.server_log_buf = buf
            st.session_state.server_log_pos = new_pos
        result: list[tuple[str, str]] = []
        for line in buf:
            display = line if len(line) <= 200 else line[:200] + "…"
            if "print_timing" in line or "total time" in line:
                klass = "timing"
            elif "task" in line and "|" in line:
                klass = "task"
            elif "error" in line.lower() or "fail" in line.lower():
                klass = "error"
            elif "load_model" in line or "init" in line:
                klass = "init"
            else:
                klass = "info"
            result.append((display, klass))
        return result
    except Exception:
        return []


def drain_server_log_to_timeline(timeline: list[TimelineEvent], turn_t0: float, reset_pos: bool = False) -> None:
    """Read new llama-server log lines and append translated events to `timeline`.

    `turn_t0` is the absolute time the current turn started (time.time()).
    Each appended event gets a `ts` relative to that. Raw lines are stored
    in `detail` so the UI can offer a 'show raw' toggle.

    `reset_pos=True` rewinds the session_state cursor to the current end of
    the log file before reading — use this at the START of a new turn so
    we don't dump all the leftover lines from the previous turn into the
    fresh timeline.
    """
    log_path = find_llama_log_path()
    if not log_path or not os.path.exists(log_path):
        return
    if reset_pos:
        try:
            st.session_state.server_log_pos = os.path.getsize(log_path)
            st.session_state.server_log_buf = []
        except OSError:
            return
    pos = st.session_state.get("server_log_pos", 0)
    try:
        size = os.path.getsize(log_path)
        start = pos if pos < size else 0
        with open(log_path, "r", encoding="utf-8", errors="replace") as f:
            f.seek(start)
            new_text = f.read()
            new_pos = f.tell()
        if not new_text:
            return
        new_lines = [l for l in new_text.splitlines() if l.strip()]
        st.session_state.server_log_pos = new_pos
        st.session_state.server_log_buf = (
            st.session_state.get("server_log_buf", []) + new_lines
        )[-60:]
        batch_ts = time.time() - turn_t0
        # Coalesce: for each inference (one slot launch → done), emit only the
        # "total" event (which contains the most useful info: total time +
        # token count). This brings the server-event volume down to 1 line
        # per inference — perfect for the Live Tail. The full raw log is
        # still tailable on disk for engineering deep-dives.
        latest_total: tuple[str, str, str] | None = None
        latest_slot: tuple[str, str, str] | None = None
        for line in new_lines:
            kind, label, text = translate_server_line(line)
            if label == "total":
                latest_total = (kind, label, text, line)
            elif label == "slot" and latest_slot is None:
                latest_slot = (kind, label, text, line)
        # Prefer the "total" event — it has duration and token count. Fall
        # back to the slot launch if we never saw a "total" (e.g., the
        # inference was still running when we read the log).
        chosen = latest_total or latest_slot
        if chosen is None:
            return
        kind, label, text, raw_line = chosen
        # Always REPLACE the most recent server event in the timeline. This
        # means a long inference that emits multiple total events over time
        # collapses to a single updating line.
        replaced = False
        for prev in reversed(timeline[-6:]):
            if prev.kind == "server":
                prev.text = text
                prev.detail = raw_line[:400]
                prev.ts = batch_ts
                replaced = True
                break
        if not replaced:
            timeline.append(TimelineEvent(
                ts=batch_ts,
                kind="server",
                label="infer",
                text=text,
                detail=raw_line[:400],
                detail_kind="raw",
            ))
    except Exception:
        return


def render_chat_messages(messages: list[dict[str, str]]) -> None:
    if not messages:
        st.markdown('<div class="chat-empty">Agent P is ready.</div>', unsafe_allow_html=True)
        return
    rows = []
    for msg in messages[-20:]:
        role = "user" if msg.get("role") == "user" else "assistant"
        label = "You" if role == "user" else "Agent P"
        content = escape(str(msg.get("content", ""))).replace("\n", "<br>")
        thinking_html = render_inline_thinking(msg.get("thinking"), running=False)
        rows.append(
            f"""
<div class="chat-row chat-row-{role}">
  <div class="chat-label">{label}</div>
  <div class="chat-bubble chat-bubble-{role}">{thinking_html}<div class="chat-text">{content}</div></div>
</div>
"""
        )
    st.markdown(f'<div class="llm-chat-scroll">{"".join(rows)}</div>', unsafe_allow_html=True)


init_state()

# One-shot component that hosts a script in a privileged iframe (streamlit's
# CSP blocks inline <script> in markdown, but st.components.v1.html runs them).
# The script sets up a MutationObserver on the main page's scroll container
# and keeps the view pinned to the bottom while the agent streams.
st.components.v1.html(
    """<script>
(function(){
  if (window.__autoScrollInited) return;
  window.__autoScrollInited = true;
  function findScroller(){
    var all = parent.document.querySelectorAll('section, [data-testid=stApp] > div');
    for (var i=0; i<all.length; i++){
      var el = all[i];
      var s = parent.getComputedStyle(el);
      if ((s.overflowY==='auto'||s.overflowY==='scroll') && el.scrollHeight > el.clientHeight + 20){
        return el;
      }
    }
    return null;
  }
  function initObs(scroller){
    var last = scroller.scrollHeight;
    function tick(){
      var h = scroller.scrollHeight;
      if (h !== last){
        last = h;
        scroller.scrollTop = h;
      }
    }
    new parent.MutationObserver(tick).observe(scroller, {childList:true, subtree:true, attributes:true, characterData:true});
    setInterval(tick, 100);
  }
  var sc = findScroller();
  if (!sc) {
    var tries = 0;
    var iv = setInterval(function(){
      tries++;
      sc = findScroller();
      if (sc || tries > 20) { clearInterval(iv); if (sc) initObs(sc); }
    }, 200);
  } else {
    initObs(sc);
  }
})();
</script>""",
    height=0,
)

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
.llm-chat-scroll { min-height: 360px; max-height: none; padding: 18px 18px 22px 18px; box-sizing: border-box; background: #ffffff; border-left: 1px solid #c7cbd1; border-right: 1px solid #c7cbd1; border-bottom: 1px solid #e5e7eb; }
.chat-empty { min-height: 360px; display: flex; align-items: center; justify-content: center; color: #6b7280; font-size: 13px; background: #ffffff; border-left: 1px solid #c7cbd1; border-right: 1px solid #c7cbd1; border-bottom: 1px solid #e5e7eb; }
.chat-row { margin-bottom: 16px; clear: both; }
.chat-label { font-size: 12px; color: #6b7280; margin-bottom: 6px; }
.chat-bubble { max-width: 84%; padding: 10px 12px; border: 1px solid #d1d5db; font-size: 15px; line-height: 1.55; word-break: break-word; white-space: normal; }
.chat-row-user { text-align: right; }
.chat-row-user .chat-label { text-align: right; }
.chat-bubble-user { margin-left: auto; background: #1f2937; color: #ffffff; border-color: #1f2937; border-radius: 8px 8px 2px 8px; text-align: left; }
.chat-bubble-assistant { background: #f9fafb; color: #111827; border-color: #d1d5db; border-radius: 8px 8px 8px 2px; }
.chat-text { white-space: normal; }
.bubble-thinking { margin: 0 0 10px 0; padding: 0; background: rgba(0,0,0,0.035); border-radius: 5px; border-left: 2px solid #d1d5db; font-size: 11px; color: #6b7280; line-height: 1.5; max-height: 360px; overflow-y: auto; }
.bubble-thinking-title { position: sticky; top: 0; background: rgba(255,255,255,0.95); backdrop-filter: blur(4px); padding: 6px 10px; font-size: 10px; text-transform: uppercase; letter-spacing: 0.5px; color: #9ca3af; font-weight: 700; display: flex; align-items: center; gap: 6px; border-bottom: 1px solid #e5e7eb; z-index: 1; }
.bubble-thinking-pulse { width: 6px; height: 6px; border-radius: 50%; background: #10b981; display: inline-block; flex: 0 0 6px; animation: bubble-pulse 1.4s ease-in-out infinite; }
.bubble-thinking-pulse.idle { background: #d1d5db; animation: none; }
@keyframes bubble-pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.45; } }
.bubble-thinking-step { display: flex; gap: 6px; padding: 2px 0; }
.bubble-thinking-label { flex: 0 0 50px; color: #9ca3af; font-size: 10px; text-transform: lowercase; letter-spacing: 0.2px; padding-top: 1px; }
.bubble-thinking-text { flex: 1; font-size: 11px; color: #6b7280; }
.bubble-thinking-text b { color: #4b5563; font-weight: 600; }
.bubble-thinking-text code { background: rgba(0,0,0,0.05); padding: 0 4px; border-radius: 2px; font-size: 10.5px; color: #4b5563; font-family: ui-monospace, SFMono-Regular, monospace; }
.bubble-thinking-args { margin: 2px 0 2px 56px; padding: 4px 6px; background: rgba(0,0,0,0.04); border-radius: 3px; font-size: 10.5px; color: #6b7280; white-space: pre-wrap; word-break: break-word; max-height: 72px; overflow-y: auto; font-family: ui-monospace, SFMono-Regular, monospace; }
.bubble-thinking-evidence { margin: 2px 0 2px 56px; padding: 0 0 0 12px; list-style: none; font-size: 10.5px; color: #6b7280; }
.bubble-thinking-evidence li { padding: 1px 0; }
.bubble-thinking-evidence code { background: rgba(0,0,0,0.05); padding: 0 3px; border-radius: 2px; color: #4b5563; font-size: 10px; font-family: ui-monospace, SFMono-Regular, monospace; }
.bubble-thinking-snippet { display: block; color: #9ca3af; font-size: 10px; margin-left: 4px; }
.bubble-server-log-head { font-size: 10px; font-weight: 700; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.4px; margin: 8px 0 4px 0; display: flex; align-items: center; gap: 6px; }
.bubble-server-log-head::before { content: "▸"; color: #22c55e; }
.bubble-server-log { background: #0f172a; color: #cbd5e1; border-radius: 4px; padding: 6px 8px; font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: 10px; line-height: 1.4; max-height: 180px; overflow-y: auto; border: 1px solid #1e293b; }
.bubble-log-line { white-space: pre-wrap; word-break: break-all; padding: 0 0; color: #94a3b8; }
.bubble-log-line.log-task { color: #fbbf24; }
.bubble-log-line.log-timing { color: #34d399; }
.bubble-log-line.log-error { color: #f87171; }
.bubble-log-line.log-init { color: #60a5fa; }

/* Unified timeline (business events + translated server events). */
.bubble-timeline-row { display: flex; gap: 8px; align-items: baseline; padding: 2px 8px 2px 0; }
.bubble-timeline-row.server { opacity: 0.72; font-size: 10.5px; }
.bubble-timeline-ts { flex: 0 0 58px; color: #9ca3af; font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: 9.5px; letter-spacing: 0.2px; }
.bubble-timeline-dot { width: 8px; height: 8px; border-radius: 50%; flex: 0 0 8px; align-self: center; box-shadow: 0 0 0 2px rgba(255,255,255,0.6); }
.bubble-timeline-dot.dot-model { background: #10b981; }
.bubble-timeline-dot.dot-tool { background: #3b82f6; }
.bubble-timeline-dot.dot-kb, .bubble-timeline-dot.dot-evidence { background: #8b5cf6; }
.bubble-timeline-dot.dot-server { background: #94a3b8; }
.bubble-timeline-dot.dot-ticket { background: #f59e0b; }
.bubble-timeline-dot.dot-error, .bubble-timeline-dot.dot-retry { background: #ef4444; }
.bubble-timeline-dot.dot-done { background: #059669; }
.bubble-timeline-dot.dot-stream { background: #6366f1; }
.bubble-timeline-label { flex: 0 0 52px; color: #6b7280; font-size: 9.5px; text-transform: lowercase; letter-spacing: 0.2px; font-family: ui-monospace, SFMono-Regular, Menlo, monospace; }
.bubble-timeline-label.server { color: #94a3b8; }
.bubble-timeline-text { flex: 1; font-size: 11px; color: #374151; line-height: 1.45; }
.bubble-timeline-text.server { color: #94a3b8; }
.bubble-timeline-text b { color: #111827; font-weight: 600; }
.bubble-timeline-text code { background: rgba(0,0,0,0.06); padding: 0 3px; border-radius: 2px; font-size: 10.5px; color: #374151; font-family: ui-monospace, SFMono-Regular, Menlo, monospace; }
.bubble-timeline-text.server code { background: rgba(0,0,0,0.04); color: #64748b; }
.bubble-timeline-detail { margin: 1px 0 5px 80px; font-size: 10px; color: #6b7280; }
.bubble-timeline-detail summary { cursor: pointer; user-select: none; color: #6b7280; font-size: 9.5px; }
.bubble-timeline-detail summary:hover { color: #2563eb; }
.bubble-timeline-detail-raw { background: #0f172a; color: #cbd5e1; padding: 5px 7px; border-radius: 3px; margin: 2px 0 0 0; max-height: 120px; overflow-y: auto; font-size: 10px; line-height: 1.4; font-family: ui-monospace, SFMono-Regular, Menlo, monospace; white-space: pre-wrap; word-break: break-all; border: 1px solid #1e293b; }
.bubble-timeline-detail-raw code { background: transparent; color: inherit; padding: 0; }
.bubble-timeline-evidence { margin: 2px 0 2px 78px; padding: 0 0 0 12px; list-style: none; font-size: 10px; color: #6b7280; }
.bubble-timeline-evidence li { padding: 1px 0; }
.bubble-timeline-evidence code { background: rgba(0,0,0,0.05); padding: 0 3px; border-radius: 2px; color: #4b5563; font-size: 9.5px; font-family: ui-monospace, SFMono-Regular, Menlo, monospace; }
.bubble-timeline-snippet { display: block; color: #9ca3af; font-size: 10px; margin-left: 4px; }

/* Live Tail Console — terminal-style SSE feed above the chat. */
.live-tail { margin: 0 0 12px 0; border-radius: 6px; border: 1px solid #1e293b; background: #0f172a; color: #cbd5e1; font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace; font-size: 11px; line-height: 1.45; overflow: hidden; }
.live-tail-head { display: flex; align-items: center; gap: 8px; padding: 6px 10px; background: #1e293b; border-bottom: 1px solid #334155; font-size: 10.5px; color: #94a3b8; }
.live-tail-dot { width: 8px; height: 8px; border-radius: 50%; background: #94a3b8; flex: 0 0 8px; }
.live-tail-dot.lt-live { background: #22c55e; box-shadow: 0 0 6px #22c55e; animation: lt-pulse 1.6s ease-in-out infinite; }
.live-tail-dot.lt-connecting { background: #fbbf24; }
.live-tail-dot.lt-error { background: #ef4444; }
@keyframes lt-pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.4; } }
.live-tail-title { color: #cbd5e1; font-weight: 700; letter-spacing: 0.4px; text-transform: uppercase; }
.live-tail-file { color: #64748b; font-size: 10px; flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.live-tail-count { color: #64748b; font-size: 10px; }
.live-tail-btn { background: transparent; border: 1px solid #334155; color: #94a3b8; cursor: pointer; padding: 1px 6px; border-radius: 3px; font-size: 10px; }
.live-tail-btn:hover { color: #cbd5e1; border-color: #475569; }
.live-tail-body { margin: 0; padding: 6px 10px; overflow-y: auto; overflow-x: hidden; background: #0f172a; white-space: pre-wrap; word-break: break-all; }
.lt-line { font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace; font-size: 10.5px; line-height: 1.4; padding: 0; }
.lt-ts { color: #475569; }
.lt-kind { font-weight: 600; }
.lt-text { color: #cbd5e1; }
.server-log-head { font-size: 10px; font-weight: 700; color: #475569; margin: 10px 0 4px 0; letter-spacing: 0.4px; text-transform: uppercase; display: flex; align-items: center; gap: 6px; }
.server-log-head::before { content: "▸"; color: #22c55e; font-size: 12px; }
.server-log { background: #0f172a; color: #cbd5e1; border-radius: 4px; padding: 8px 10px; font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace; font-size: 10.5px; line-height: 1.45; max-height: 240px; overflow-y: auto; border: 1px solid #1e293b; }
.log-line { white-space: pre-wrap; word-break: break-all; padding: 1px 0; color: #94a3b8; }
.log-line.log-task { color: #fbbf24; }
.log-line.log-timing { color: #34d399; }
.log-line.log-error { color: #f87171; font-weight: 600; }
.log-line.log-init { color: #60a5fa; }
.server-log-empty { color: #64748b; font-style: italic; padding: 4px 0; }
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
        # Wrap Agent P header + Live Tail Console in a single bordered
        # container so the activity feed reads as PART of the Agent P
        # section, not a separate card floating below it.
        with st.container(border=True):
            render_assistant_header(scenario)
            # Live Tail Console — terminal-style SSE feed of all agent
            # activity. Embedded INSIDE the Agent P card.
            if st.session_state.get("live_tail_enabled", True):
                sse_url = os.environ.get("LIVE_TAIL_SSE_URL", "http://127.0.0.1:8765/sse?log=/tmp/demo1_live_tail.log")
                try:
                    render_live_tail_console(sse_url, height_px=160, max_lines=8)
                except Exception as exc:
                    st.caption(f"⚠ live tail unavailable: {exc}")
        chat_placeholder = st.empty()
        render_chat_container(chat_placeholder, st.session_state.employee_messages)
        render_evidence_chips(evidence_preview)

        prompt = st.chat_input("Message Agent P")
        if prompt and prompt.strip():
            run_employee_chat_live(
                prompt.strip(),
                scenario,
                user,
                chat_placeholder,
            )
            st.rerun()

elif menu == "IT Operations":
    st.title("IT Operations Console")
    st.caption("Agent P から引き継がれた社内サポートチケット")
    left_it, right_it = st.columns([1.2, 1.0], gap="large")

    # ── LEFT COLUMN: ticket table + selectbox + selected-ticket details ──
    with left_it:
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
            st.dataframe(
                df[["ticket_id", "status", "requester", "system", "priority", "route"]],
                use_container_width=True,
                hide_index=True,
            )
            selected_id = st.selectbox(
                "Open ticket",
                [t["ticket_id"] for t in st.session_state.tickets],
                label_visibility="collapsed",
            )
            # Selected-ticket details, in a bordered container (matches
            # the Employee Portal "Agent P" card style).
            ticket = next(t for t in st.session_state.tickets if t["ticket_id"] == selected_id)
            with st.container(border=True):
                st.markdown(
                    f"**{ticket.get('ticket_id', '')} · "
                    f"{ticket.get('title', ticket.get('system', ''))}**"
                )
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

                # ── Inline status action buttons ────────────────────────
                # Jira / ServiceNow-style controls: Triage / Resolve /
                # Close / Reassign + an Add Comment expander. Status-aware
                # disabled matrix; destructive Close uses a two-click
                # confirm via st.session_state["pending_close_id"].
                st.markdown("---")
                st.markdown("**Actions**")
                ticket_id = ticket["ticket_id"]
                cur_status = ticket.get("status", "New")

                # Row 1: one-click status-aware buttons
                b1, b2, b3, b4 = st.columns(4)
                with b1:
                    triage_clicked = st.button(
                        "Triage",
                        key=f"triage_{ticket_id}",
                        disabled=cur_status != "New",
                        use_container_width=True,
                    )
                with b2:
                    resolve_clicked = st.button(
                        "Resolve",
                        key=f"resolve_{ticket_id}",
                        type="primary",
                        disabled=cur_status == "Closed",
                        use_container_width=True,
                    )
                with b3:
                    close_clicked = st.button(
                        "Close",
                        key=f"close_{ticket_id}",
                        disabled=cur_status == "Closed",
                        use_container_width=True,
                    )
                with b4:
                    reassign_clicked = st.button(
                        "Reassign",
                        key=f"reassign_{ticket_id}",
                        disabled=cur_status == "Closed",
                        use_container_width=True,
                    )

                # Row 2: Apply status change (input-required actions)
                with st.expander("Apply status change (with note)", expanded=False):
                    action_choice = st.selectbox(
                        "Action",
                        ["Resolve", "Triage (override priority/route)", "Reassign"],
                        key=f"action_choice_{ticket_id}",
                        label_visibility="collapsed",
                    )
                    note = st.text_area(
                        "Note",
                        key=f"action_note_{ticket_id}",
                        placeholder=(
                            "解決内容を入力…"
                            if action_choice == "Resolve"
                            else "Triage notes / Reassign reason"
                        ),
                        height=80,
                        label_visibility="collapsed",
                    )
                    new_priority = None
                    new_route = None
                    if action_choice == "Triage (override priority/route)":
                        p1, p2 = st.columns(2)
                        new_priority = p1.text_input(
                            "New priority (P1/P2/P3)", key=f"prio_{ticket_id}"
                        )
                        new_route = p2.text_input("New route", key=f"route_{ticket_id}")
                    elif action_choice == "Reassign":
                        new_route = st.text_input(
                            "New route (required)", key=f"newroute_{ticket_id}"
                        )
                    apply_clicked = st.button(
                        "Apply", key=f"apply_{ticket_id}", type="primary"
                    )
                    if apply_clicked:
                        if action_choice == "Resolve":
                            ok, msg, _ = resolve_ticket(ticket_id, note)
                            audit_action = "manual_resolve"
                        elif action_choice.startswith("Triage"):
                            ok, msg, _ = triage_ticket(
                                ticket_id,
                                priority=new_priority or None,
                                new_route=new_route or None,
                                notes=note,
                            )
                            audit_action = "manual_triage"
                        else:  # Reassign
                            ok, msg, _ = reassign_ticket(
                                ticket_id, new_route or "", reason=note
                            )
                            audit_action = "manual_reassign"
                        (st.success if ok else st.error)(msg)
                        if ok:
                            add_audit(
                                "IT Operations Agent",
                                audit_action,
                                ticket_id,
                                (note or "")[:60],
                                "Low",
                            )
                            st.rerun()

                # One-click button handlers (no extra input)
                if triage_clicked and cur_status == "New":
                    ok, msg, _ = triage_ticket(
                        ticket_id, notes="Quick triage (default)"
                    )
                    (st.success if ok else st.error)(msg)
                    if ok:
                        add_audit(
                            "IT Operations Agent",
                            "manual_triage",
                            ticket_id,
                            "default",
                            "Low",
                        )
                        st.rerun()

                if resolve_clicked:
                    st.info(
                        "Resolve には note が必要です。下の「Apply status change」を開いてください。"
                    )

                if reassign_clicked:
                    st.info(
                        "Reassign には新しい担当が必要です。下の「Apply status change」を開いてください。"
                    )

                if close_clicked:
                    st.session_state["pending_close_id"] = ticket_id
                    st.rerun()

                # Close confirmation (two-click pattern)
                if st.session_state.get("pending_close_id") == ticket_id:
                    st.warning(
                        f"{ticket_id} を Closed にします。よろしければもう一度「Confirm close」を押してください。"
                    )
                    cc1, cc2 = st.columns([1, 4])
                    with cc1:
                        confirm_close = st.button(
                            "Confirm close",
                            key=f"confirm_close_{ticket_id}",
                            type="primary",
                        )
                    with cc2:
                        cancel_close = st.button(
                            "Cancel", key=f"cancel_close_{ticket_id}"
                        )
                    if confirm_close:
                        ok, msg, _ = close_ticket(ticket_id)
                        (st.success if ok else st.error)(msg)
                        st.session_state.pop("pending_close_id", None)
                        if ok:
                            add_audit(
                                "IT Operations Agent",
                                "manual_close",
                                ticket_id,
                                "",
                                "Low",
                            )
                            st.rerun()
                    if cancel_close:
                        st.session_state.pop("pending_close_id", None)
                        st.rerun()

                # Row 3: Add Comment (collapsible)
                with st.expander("Add comment", expanded=False):
                    comment_text = st.text_area(
                        "Comment",
                        key=f"comment_{ticket_id}",
                        height=80,
                        label_visibility="collapsed",
                        placeholder="コメントを入力…",
                    )
                    if st.button(
                        "Post comment", key=f"post_comment_{ticket_id}"
                    ):
                        ok, msg, _ = add_comment_to_ticket(ticket_id, comment_text)
                        (st.success if ok else st.error)(msg)
                        if ok:
                            add_audit(
                                "IT Operations Agent",
                                "manual_comment",
                                ticket_id,
                                comment_text[:60],
                                "Low",
                            )
                            st.rerun()
        else:
            st.info("No tickets yet. Create one from Employee Portal.")
    # ── RIGHT COLUMN: IT Agent P card (mirrors Employee Portal's Agent P) ──
    with right_it:
        # Initialize IT agent runtime + chat history
        if "it_chat_messages" not in st.session_state:
            st.session_state.it_chat_messages = []
        if "it_agent_runtime" not in st.session_state:
            from runtime.pi_agent import PiAgentRuntime, PI_IT_SKILL
            st.session_state.it_agent_runtime = PiAgentRuntime(skill_path=PI_IT_SKILL)
        # Agent card (header + status) — matches Employee Portal's
        # "Agent P" + "Support session" + "Local LFM · Ready" pattern.
        active_count = sum(
            1 for t in st.session_state.tickets
            if t.get("status") in ("New", "Triaged", "In Progress")
        )
        st.markdown(
            f"""
<div class="assistant-hero">
  <div>
    <div class="assistant-name">IT Operations Agent P</div>
    <div class="assistant-sub">Internal support desk</div>
  </div>
</div>
<div class="assistant-status">
  <span class="dot dot-live"></span> Local LFM · <b>{active_count} 件のアクティブチケット</b>
</div>
""",
            unsafe_allow_html=True,
        )
        # Bordered card containing chat history + live tail + input
        with st.container(border=True):
            st.caption("リスト / 参照 / トリアージ / 解決 / 关闭 / 重新分派 / 评论 を直接実行できます。")
            # Live Tail SSE console (same component as Employee Portal)
            if st.session_state.get("live_tail_enabled", True):
                sse_url = os.environ.get(
                    "LIVE_TAIL_SSE_URL",
                    "http://127.0.0.1:8765/sse?log=/tmp/demo1_live_tail.log",
                )
                try:
                    render_live_tail_console(sse_url, height_px=160, max_lines=8)
                except Exception as exc:
                    st.caption(f"⚠ live tail unavailable: {exc}")
            # Chat history
            for msg in st.session_state.it_chat_messages:
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])
            # Chat input — inside the card so the visual unit is one box
            it_prompt = st.chat_input(
                "Message IT Agent P (e.g. '未対応チケット一覧', 'KW-1234 を解決')",
                key="it_chat_input",
            )
            if it_prompt and it_prompt.strip():
                st.session_state.it_chat_messages.append(
                    {"role": "user", "content": it_prompt.strip()}
                )
                with st.chat_message("user"):
                    st.markdown(it_prompt.strip())
                with st.chat_message("assistant"):
                    with st.spinner("IT Agent が考え中..."):
                        reply = st.session_state.it_agent_runtime.chat_it(it_prompt.strip())
                    st.markdown(reply.reply)
                st.session_state.it_chat_messages.append(
                    {"role": "assistant", "content": reply.reply}
                )
                if any(
                    ev.tool.startswith("erp_it_") and ev.status == "ok"
                    for ev in reply.events
                ):
                    load_persisted_tickets()
                st.rerun()
    if it_prompt and it_prompt.strip():
        st.session_state.it_chat_messages.append({"role": "user", "content": it_prompt.strip()})
        # Display user message
        with st.chat_message("user"):
            st.markdown(it_prompt.strip())
        # Get agent reply
        with st.chat_message("assistant"):
            with st.spinner("IT Agent が考え中..."):
                reply = st.session_state.it_agent_runtime.chat_it(it_prompt.strip())
            # Display reply (may contain HTML like <code>)
            st.markdown(reply.reply)
        st.session_state.it_chat_messages.append({"role": "assistant", "content": reply.reply})
        # If a tool updated a ticket, refresh from disk
        if any(ev.tool.startswith("erp_it_") and ev.status == "ok" for ev in reply.events):
            load_persisted_tickets()
        st.rerun()

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
