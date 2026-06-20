from __future__ import annotations

import json
import os
import re
import subprocess
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

APP_DIR = Path(__file__).resolve().parents[1]
PI_BIN_DIR = APP_DIR / "node_modules" / ".bin"
_DEFAULT_PI_CLI = PI_BIN_DIR / ("pi.cmd" if os.name == "nt" else "pi")
PI_CLI = Path(os.environ.get("PI_CLI_PATH", str(_DEFAULT_PI_CLI)))
PI_AGENT_DIR = Path(os.environ.get("PI_AGENT_DIR", str(APP_DIR / ".pi-agent")))
PI_ERP_EXTENSION = APP_DIR / "runtime" / "pi_erp_extension.ts"
PI_ERP_SKILL = APP_DIR / ".pi" / "skills" / "erp-support"
PI_IT_SKILL = APP_DIR / ".pi" / "skills" / "it-support"
PI_PROVIDER = "local-lfm"
PI_MODEL = "lfm2-1.2b-tool-q4_k_m.gguf"
PI_TIMEOUT_SECONDS = 180   # 1.2B + QLoRA slow on some prompts; 3 min ceiling
PI_TOOL_RETRY_LIMIT = 2

BUILTIN_TOOL_INTENT_PATTERNS = [
    "ファイル", "ソースコード", "ディレクトリ", "フォルダ", "bash", "shell", "terminal",
    "file", "source code", "directory", "folder", "read file", "write file", "edit file",
]

ERP_INTENT_PATTERNS = [
    "aadsts", "sign-in failed", "error code", "trace id", "correlation id", "mfa",
    "erp", "crm", "sso", "dynamics", "salesforce", "power bi", "license", "conditional access",
    "ログイン", "サインイン", "エラー", "権限", "ライセンス", "チケット", "ヘルプデスク",
    "itに連絡", "it に連絡", "問い合わせ", "社内規程", "根拠", "検索",
]

TICKET_INTENT_PATTERNS = [
    "ticket", "チケット", "helpdesk", "ヘルプデスク", "itに連絡", "it に連絡",
    "問い合わせ", "エスカレーション", "まだ解決しない", "解決しない",
    "create ticket", "contact it", "連絡して",
]

# IT-side action intent patterns — used by chat_it() to bypass the model
# when the user clearly wants to Triage/Resolve/Close/Reassign/comment on
# a ticket. The 1.2B model hallucinates ticket IDs and resolution notes
# (see _create_ticket_directly docstring for the same problem on creation).
IT_RESOLVE_PATTERNS = [
    "解決して", "解決する", "解決します", "解決マーク", "resolve",
    "解決して", "resolved にして", "解決済み",
]
IT_CLOSE_PATTERNS = [
    "クローズして", "クローズする", "閉じる", "closed にして", "close",
    "关闭", "クローズ",
]
IT_REASSIGN_PATTERNS = [
    "再分派", "再アサイン", "担当変更", "transfer", "reassign",
    "重新分派", "引き継ぎ",
]
IT_TRIAGE_PATTERNS = [
    "トリアージして", "triage", "triaged にして",
]
IT_COMMENT_PATTERNS = [
    "コメント", "comment", "评论", "備考",
]

ERP_ANALYSIS_TOOLS = [
    "erp_analyze_pasted_error_with_kb",
]

ERP_CURRENT_ERROR_TOOLS = [
    "erp_get_current_error",
    "erp_inspect_current_error_with_kb",
    "kb_rg_search",
    "kb_read_knowledge",
]

ERP_TICKET_TOOLS = [
    "erp_create_ticket_from_current_error",
]

IT_TOOLS = [
    # Read-only ticket lookup (lets the agent reference a ticket by id).
    "erp_it_get_ticket",
    "kb_rg_search",
    "kb_read_knowledge",
    # The only write the IT agent is allowed: a "[Agent P 分析]"
    # comment. The UI action buttons handle resolve/close/reassign/triage.
    "erp_it_add_comment",
]


@dataclass
class PiAgentEvent:
    tool: str
    status: str
    detail: str


@dataclass
class PiAgentResult:
    reply: str
    events: list[PiAgentEvent] = field(default_factory=list)
    evidence: list[dict[str, Any]] = field(default_factory=list)
    ticket: dict[str, Any] | None = None
    session_file: str | None = None


class PiAgentRuntime:
    """Pi-first Agent P runtime used by the ERP web UI.

    Streamlit sends the user's text to Pi. Pi/LFM decides whether to answer
    normally or call ERP/document tools. Python only launches Pi and renders the
    returned messages/events.
    """

    def __init__(
        self,
        app_dir: Path = APP_DIR,
        pi_cli: Path = PI_CLI,
        pi_agent_dir: Path = PI_AGENT_DIR,
        extension_path: Path = PI_ERP_EXTENSION,
        skill_path: Path = PI_ERP_SKILL,
        provider: str = PI_PROVIDER,
        model: str = PI_MODEL,
    ) -> None:
        self.app_dir = app_dir
        self.pi_cli = pi_cli
        self.pi_agent_dir = pi_agent_dir
        self.extension_path = extension_path
        self.skill_path = skill_path
        self.provider = provider
        self.model = model

    def available(self) -> bool:
        return all([
            self.pi_cli.exists(),
            self.pi_agent_dir.exists(),
            self.extension_path.exists(),
            self.skill_path.exists(),
        ])

    def chat(self, user_text: str) -> PiAgentResult:
        self._last_user_text = user_text
        if not self.available():
            return PiAgentResult(
                reply="Pi Agent P is not available.",
                events=[PiAgentEvent("pi_agent", "error", "missing CLI, config, extension, or skill")],
            )
        direct_reply = self._direct_basic_reply(user_text)
        if direct_reply:
            return PiAgentResult(reply=direct_reply)
        env = os.environ.copy()
        env.update({
            "PI_CODING_AGENT_DIR": str(self.pi_agent_dir),
            "PI_OFFLINE": "1",
            "PI_SKIP_VERSION_CHECK": "1",
        })
        today = datetime.now().strftime("%Y-%m-%d %A")
        tool_profile = self._tool_profile(user_text)
        required_tool = self._required_tool(tool_profile)
        parsed = self._run_pi(user_text, tool_profile, today, env)
        # If the model ignored the Japanese instruction and produced a
        # mostly-English reply, retry once with a forceful language
        # instruction. This usually succeeds — the 1.2B model often
        # just needs an explicit reminder mid-conversation.
        if self._is_mostly_english(parsed.reply) and not required_tool:
            parsed = self._run_pi(
                user_text, tool_profile, today, env,
                retry_instruction=(
                    "重要: あなたの前回/現在の返答が英語になっています。"
                    "【必ず日本語で返答してください】。"
                    "Keep error codes like AADSTS50076, MFA, Dynamics 365, "
                    "Power BI as-is — but ALL explanatory text, analysis, "
                    "and questions must be in Japanese."
                ),
            )
        if self._has_required_tool(parsed, required_tool):
            return self._ensure_followup_questions(parsed)
        if not required_tool:
            # No tool was required. If the user asked for a ticket but the
            # model didn't actually call the ticket tool, build the ticket
            # in code (the 1.2B model hallucinates ticket ids/content).
            if parsed.ticket is None and self._user_wants_ticket(user_text):
                real = self._create_ticket_directly(user_text)
                return self._ensure_followup_questions(real)
            return self._ensure_followup_questions(parsed)

        last = parsed
        for attempt in range(1, PI_TOOL_RETRY_LIMIT + 1):
            retry = self._run_pi(
                user_text,
                tool_profile,
                today,
                env,
                retry_instruction=(
                    f"Previous attempt failed because it answered without calling {required_tool}. "
                    f"The next assistant action MUST be a real Pi tool call to {required_tool}. "
                    "Do not apologize. Do not explain first. Do not answer in text before the tool call."
                ),
            )
            retry.events.insert(0, PiAgentEvent("pi_agent", "retry", f"missing required tool {required_tool}; attempt {attempt}"))
            if self._has_required_tool(retry, required_tool):
                return self._ensure_followup_questions(retry)
            last = retry
        last.events.insert(
            0,
            PiAgentEvent("pi_agent", "error", f"required tool was not called: {required_tool}; local model returned text only"),
        )
        # If the user asked for a ticket but the 1.2B model hallucinated a
        # ticket in text instead of calling the tool, build a real one.
        if self._user_wants_ticket(user_text):
            real = self._create_ticket_directly(user_text)
            return self._ensure_followup_questions(real)
        # 1.2B models are too weak to reliably follow "ask follow-up questions"
        # instructions, so we do a post-processing pass: if the model handled
        # an erp_get_current_error or erp_analyze_pasted_error_with_kb call
        # but the error data is vague (NO_ERROR_CODE / generic symptom / empty
        # trace id), APPEND a numbered list of follow-up questions to the
        # reply. The model can still lead with whatever summary it produced.
        last = self._ensure_followup_questions(last)
        return last

    def chat_it(self, user_text: str) -> PiAgentResult:
        """Run the IT Operations Agent P in KB-ANALYST mode.

        Flow:
          1. Short-circuit on ticket-mutating intent
             (resolve/close/reassign/triage) — redirect to UI buttons.
          2. Detect analysis intent ("why", "原因", etc.) and pre-run
             kb_rg_search in Python, returning citations + suggested
             next steps directly (the 1.2B model can't reliably emit
             `<tool_call>kb_rg_search</tool_call>` envelopes).
          3. If the user pastes a ticket id, look it up via
             erp_it_get_ticket and include the structured data in
             the system prompt.
          4. Otherwise fall through to the LLM with the KB-context
             prepended to the system prompt.
        """
        if not self.available():
            return PiAgentResult(
                reply="IT Agent P is not available.",
                events=[PiAgentEvent("it_agent", "error", "missing CLI, config, extension, or skill")],
            )
        # 1. UI-action redirect short-circuit
        direct = self._direct_it_action(user_text)
        if direct is not None:
            return direct
        # 1b. Greeting / identity / date short-circuit (same logic as
        # the Employee Portal's _direct_basic_reply; the 1.2B model
        # hallucinates shell commands for these otherwise).
        basic = self._direct_basic_reply(user_text)
        if basic is not None:
            return PiAgentResult(reply=basic)
        # 2. KB analysis short-circuit: detect intent, do the search
        # in Python, synthesize a structured Japanese response with
        # citations. The 1.2B model is too weak to reliably emit
        # tool_call envelopes for kb_rg_search; the seed SFT data
        # had only 11 KB-citation rows vs 311 total.
        analysis = self._direct_it_kb_analysis(user_text)
        if analysis is not None:
            return analysis
        # 3. Fall through to the LLM with KB context appended
        env = os.environ.copy()
        env.update({
            "PI_CODING_AGENT_DIR": str(self.pi_agent_dir),
            "PI_OFFLINE": "1",
            "PI_SKIP_VERSION_CHECK": "1",
        })
        today = datetime.now().strftime("%Y-%m-%d %A")
        # 3a. If the user pasted a ticket id, attach the structured
        # ticket data so the model can ground its answer.
        sys_prompt = self._it_system_prompt(today)
        ticket_id = self._extract_it_ticket_id(user_text)
        ticket_ctx = ""
        if ticket_id:
            ticket_ctx = self._fetch_ticket_context(ticket_id)
        # 3b. If the user mentioned an error code, pre-run kb_rg_search
        # so the model can quote real citations rather than hallucinate.
        kb_ctx = self._fetch_kb_context_for_text(user_text)
        full_prompt = sys_prompt
        if ticket_ctx:
            full_prompt += "\n\n" + ticket_ctx
        if kb_ctx:
            full_prompt += "\n\n" + kb_ctx
        result = self._run_pi(
            user_text,
            "erp_it",
            today,
            env,
            skill_path=PI_IT_SKILL,
            system_prompt=full_prompt,
        )
        return result

    def _direct_it_kb_analysis(self, user_text: str) -> "PiAgentResult | None":
        """If the user asks an analysis question (cause, why, 原因,
        考えられる), pre-run kb_rg_search in Python and synthesize
        the answer. Returns None if the user didn't ask an analysis
        question (caller falls through to the LLM).

        Always returns a structured response (never None) when an
        analysis intent is detected — even on 0 hits, we return a
        clear Japanese "no KB match" message rather than letting the
        LLM hallucinate tool calls.
        """
        triggers = (
            "原因", "なぜ", "why", "what causes", "考えられる",
            "理由は", "原因は何", "原因を教", "教えて", "explain",
            "analyze", "分析", "ヘルプ", "help", "調べ",
        )
        if not any(t in user_text.lower() for t in triggers):
            return None
        # Query resolution order (each step's "winner" becomes the
        # kb_rg_search query string):
        #   1. Error code in user text (AADSTS50076 etc.)
        #   2. Japanese symptom keyword (ログイン, MFA, license, ...)
        #   3. Ticket id (KW-####) in user text → look up the ticket's
        #      error_code from erp_state/tickets.json. This handles
        #      "KW-5511 の原因を調べて" where the operator only
        #      knows the ticket number.
        #   4. Fallback: first 60 chars of user text.
        m = re.search(r"\b(AADSTS\d{4,6}|PBI_[A-Z_]+|LICENSE_MISSING|CA_BLOCK|NO_ERROR_CODE|MULTI_USER_OUTAGE|VENDOR_MFA_EXCEPTION)\b", user_text)
        if m:
            query = m.group(1)
        else:
            symptom_match = None
            for kw, code in (
                ("mfa", "AADSTS50076"), ("サインイン", "AADSTS50076"),
                ("ログイン", "AADSTS50076"), ("license", "LICENSE_MISSING"),
                ("power bi", "PBI_ACCESS_DENIED"), ("conditional", "CA_BLOCK"),
            ):
                if kw in user_text.lower():
                    symptom_match = code
                    break
            if symptom_match:
                query = symptom_match
            else:
                ticket_id = self._extract_it_ticket_id(user_text)
                if ticket_id:
                    ticket_code = self._ticket_error_code(ticket_id)
                    if ticket_code:
                        # Ticket found with a real error code — go through
                        # the normal KB path (caller will handle 0 hits
                        # below by falling back to a "best guess" based
                        # on the ticket's system/route).
                        query = ticket_code
                    else:
                        return PiAgentResult(
                            reply=(
                                f"**{ticket_id}** は erp_state/tickets.json に見つかりません。\n\n"
                                "**推奨対応:**\n"
                                "- チケット ID を確認 (typo ではないか)\n"
                                "- 該当チケットを先に Employee Portal から作成\n"
                                "- それでも解決しなければ IT 部門にエスカレーション\n\n"
                                "**注**: ステータスの変更はチケット詳細カードのボタンから"
                                "おこなってください。このチャットは分析専用です。"
                            ),
                            events=[PiAgentEvent("it_kb_analysis", "ticket_not_found", ticket_id)],
                        )
                else:
                    query = user_text[:60].strip() or "AADSTS50076"
        hits = self._kb_rg_search(query)
        if not hits:
            # No KB match — fall back to a "best guess" that surfaces
            # the ticket context (if any) and a system-level search.
            # This is the common case for tickets whose error code
            # isn't in the local KB but whose system (Dynamics 365,
            # Power BI, etc.) IS in the KB.
            return self._it_kb_best_guess(query, user_text)
        # Synthesize the structured Japanese response
        parts = [f"**{query}** について、社内 KB を参照した分析結果です。\n"]
        parts.append("**考えられる原因 (上位):**\n")
        for h in hits[:4]:
            path = h.get("path", "")
            snippet = (h.get("snippet", "") or "")[:140].replace("\n", " ")
            short = path.split("/")[-1] if path else "?"
            if snippet:
                parts.append(f"- **{short}** を参照 — {snippet}…")
            else:
                parts.append(f"- **{short}** を参照")
        parts.append("\n**推奨される次の確認手順:**\n")
        parts.append("- チケット詳細で Trace ID / Correlation ID を確認")
        parts.append("- 再現手順をオペレーター本人に確認 (時間帯・ブラウザ・端末)")
        parts.append("- 上記 KB 該当ルールの self_service 項目を参照")
        parts.append(
            "\n**注**: ステータスの変更 (解決 / クローズ / 再分派 / トリアージ) は "
            "チケット詳細カードのボタンからおこなってください。"
            "このチャットは分析専用です。"
        )
        reply = "\n".join(parts)
        return PiAgentResult(
            reply=reply,
            events=[PiAgentEvent("it_kb_analysis", "ok", f"query={query}; hits={len(hits)}")],
        )

    def _it_kb_best_guess(
        self, primary_query: str, user_text: str,
    ) -> "PiAgentResult":
        """When the primary KB search (typically an error code) returns
        no hits, surface a 'best guess' that combines:
          1. The ticket's known state (if a KW-#### was in the text)
          2. A broader search by system name (Dynamics 365, Power BI, …)
          3. The routing matrix hint

        The 1.2B model isn't trusted to synthesize this — we do it in
        Python so the operator always gets a useful, grounded answer.
        """
        import json
        from pathlib import Path
        # 1. Pull ticket context (if any)
        ticket_id = self._extract_it_ticket_id(user_text)
        ticket_ctx = ""
        ticket_system = ""
        if ticket_id:
            ticket_ctx = self._fetch_ticket_context(ticket_id)
            # Look up system for the secondary search
            tickets_path = Path(__file__).resolve().parents[1] / "erp_state" / "tickets.json"
            if tickets_path.exists():
                try:
                    data = json.loads(tickets_path.read_text(encoding="utf-8"))
                except (OSError, json.JSONDecodeError):
                    data = {}
                for t in data.get("tickets", []):
                    if t.get("ticket_id") == ticket_id:
                        ticket_system = (t.get("system") or "").strip()
                        break
        # 2. Broader search by system
        system_hits: list[dict] = []
        if ticket_system:
            system_hits = self._kb_rg_search(ticket_system)[:3]
        parts: list[str] = [
            f"**{primary_query}** について社内 KB を直接検索しましたが、"
            f"該当の規程は見つかりませんでした。\n"
        ]
        if ticket_ctx:
            parts.append(ticket_ctx + "\n")
        if system_hits:
            parts.append("**システムレベルでの参考情報 (KB):**\n")
            for h in system_hits:
                path = h.get("path", "")
                snippet = (h.get("snippet", "") or "")[:140].replace("\n", " ")
                short = path.split("/")[-1] if path else "?"
                if snippet:
                    parts.append(f"- **{short}** を参照 — {snippet}…")
                else:
                    parts.append(f"- **{short}** を参照")
            parts.append("")
        parts.append("**考えられる原因 (ベストエフォート):**\n")
        # Map ticket's system → general troubleshooting axes
        sys_lower = ticket_system.lower() if ticket_system else ""
        axes: list[str] = []
        if "dynamics" in sys_lower or "crm" in sys_lower or "salesforce" in sys_lower:
            axes = [
                "認証情報 (SSO / MFA) — 該当ユーザーの Entra ID 状態",
                "ロール / Business Unit 権限 — セキュリティロール割り当て",
                "ライセンス — Dynamics 365 / Microsoft 365 の利用開始申請",
            ]
        elif "power bi" in sys_lower or "pbi" in sys_lower:
            axes = [
                "ワークスペース / レポート / データセットの権限",
                "ゲートウェイ接続 (オンプレ ソースの場合)",
                "行レベル セキュリティ (RLS) の該当ユーザー設定",
            ]
        elif "sso" in sys_lower or "entra" in sys_lower or "aad" in sys_lower:
            axes = [
                "MFA 状態 (Authenticator アプリ登録済みか)",
                "条件付きアクセス ポリシー適用 (会社支給端末 / VPN)",
                "サインインログ (Entra admin center)",
            ]
        else:
            axes = [
                "再現性 (本人だけか / 部署全員か / 全社か)",
                "最終正常動作からの変更点 (デプロイ / ポリシー変更)",
                "Trace ID / Correlation ID からの根本原因切り分け",
            ]
        for a in axes:
            parts.append(f"- {a}")
        parts.append("\n**推奨される次の確認手順:**\n")
        parts.append("- ルーティングマトリクス (knowledge/helpdesk/ticket-routing-priority-matrix.md) "
                     "で該当システムの担当チームを確認")
        parts.append("- 上記軸についてオペレーター本人に確認")
        parts.append("- それでも解決しなければ該当チームにエスカレーション")
        parts.append(
            "\n**注**: ステータスの変更 (解決 / クローズ / 再分派 / トリアージ) は "
            "チケット詳細カードのボタンからおこなってください。"
            "このチャットは分析専用です。"
        )
        return PiAgentResult(
            reply="\n".join(parts),
            events=[PiAgentEvent(
                "it_kb_analysis", "best_guess",
                f"query={primary_query}; system={ticket_system}; "
                f"system_hits={len(system_hits)}",
            )],
        )

    def _ticket_error_code(self, ticket_id: str) -> str | None:
        """Read erp_state/tickets.json and return the error_code for
        the given ticket id, or None if not found / no error_code set.

        Used by `_direct_it_kb_analysis` to resolve a KW-#### id in
        the user text into the actual error code, so the KB search
        query is meaningful even when the operator doesn't paste
        the error text.
        """
        import json
        from pathlib import Path
        tickets_path = Path(__file__).resolve().parents[1] / "erp_state" / "tickets.json"
        if not tickets_path.exists():
            return None
        try:
            data = json.loads(tickets_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None
        for t in data.get("tickets", []):
            if t.get("ticket_id") == ticket_id:
                code = (t.get("error_code") or "").strip()
                if code and code.upper() not in {"NO_ERROR_CODE", "NONE", "N/A", ""}:
                    return code
                # Ticket exists but no error_code — use system field as fallback
                system = (t.get("system") or "").strip()
                return system or None
        return None

    def _fetch_ticket_context(self, ticket_id: str) -> str:
        """Read tickets.json and return a short Japanese-formatted
        summary of the given ticket id, or '' if not found."""
        import json
        from pathlib import Path
        tickets_path = Path(__file__).resolve().parents[1] / "erp_state" / "tickets.json"
        if not tickets_path.exists():
            return ""
        try:
            data = json.loads(tickets_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return ""
        for t in data.get("tickets", []):
            if t.get("ticket_id") == ticket_id:
                return (
                    f"**{ticket_id} の現在の状態 (erp_state/tickets.json より):**\n"
                    f"- status: {t.get('status', '?')}\n"
                    f"- system: {t.get('system', '?')}\n"
                    f"- error_code: {t.get('error_code', '?')}\n"
                    f"- category: {t.get('category', '?')}\n"
                    f"- risk: {t.get('risk', '?')} / priority: {t.get('priority', '?')}\n"
                    f"- route: {t.get('route', '?')}\n"
                    f"- summary: {t.get('summary', '?')}\n"
                )
        return ""

    def _fetch_kb_context_for_text(self, user_text: str) -> str:
        """If the text contains an error code or a distinctive keyword,
        pre-run kb_rg_search and return a markdown snippet block the
        model can quote. Returns '' if nothing matched.
        """
        m = re.search(r"\b(AADSTS\d{4,6}|PBI_[A-Z_]+|LICENSE_MISSING|CA_BLOCK|MULTI_USER_OUTAGE|VENDOR_MFA_EXCEPTION)\b", user_text)
        if not m:
            return ""
        query = m.group(1)
        hits = self._kb_rg_search(query)
        if not hits:
            return ""
        lines = [f"**社内 KB ヒット (query={query}):**"]
        for h in hits[:3]:
            path = h.get("path", "")
            snippet = (h.get("snippet", "") or "")[:160].replace("\n", " ")
            short = path.split("/")[-1] if path else "?"
            lines.append(f"- **{short}** (line {h.get('line', '?')}): {snippet}")
        return "\n".join(lines)

    def _it_system_prompt(self, today: str) -> str:
        return (
            "You are the IT Operations Agent P (KB Analyst mode) working from "
            "the IT Operations Console. You help the IT operator think through "
            "open tickets: you search the enterprise knowledge base "
            "(SSO / MFA / license / Dynamics / Power BI / routing policies) "
            "and propose all plausible root causes with citations. "
            f"Current local date is {today} in Asia/Tokyo. "
            "LANGUAGE: always respond in Japanese. Keep error codes, product "
            "names, and ticket ids (KW-1234) as-is. "
            "ANALYZE, don't mutate ticket status: when the operator asks "
            "about a ticket or symptom, call kb_rg_search (and optionally "
            "kb_read_knowledge or erp_it_get_ticket) and synthesize a "
            "Japanese answer with candidate causes + KB citations + next "
            "diagnostic steps. Do NOT call erp_it_resolve_ticket / "
            "erp_it_close_ticket / erp_it_reassign_ticket / "
            "erp_it_triage_ticket — those are driven by the UI action "
            "buttons on the ticket detail card. The only write tool you may "
            "use is erp_it_add_comment, and only when the operator "
            "explicitly asks you to leave an analysis note (prefix the "
            "comment with `[Agent P 分析]`). "
            "List every plausible cause (3-5) with a KB citation, not just "
            "one. If the KB has 0 hits, say so verbatim — never invent a "
            "rule. Ask at most 1-2 short follow-up questions if the "
            "symptom / system / impact scope is genuinely unclear. "
            "Do not use employee-side tools (erp_get_current_error, "
            "erp_analyze_pasted_error_with_kb, etc.) — those are for the "
            "Employee Portal Agent P only. "
            "For greetings, identity questions, or date / time queries, "
            "answer in plain Japanese with no tool call."
        )

    def _ensure_followup_questions(self, result: PiAgentResult) -> PiAgentResult:
        """Post-process the model reply so the user ALWAYS gets a Japanese
        response with: (1) brief acknowledgement, (2) follow-up questions,
        (3) recommended next steps from the local knowledge base.

        The 1.2B model is too weak to reliably follow complex instructions,
        so we do this in code rather than relying on the prompt.
        """
        # If the model already produced a good Japanese structure, skip.
        if self._reply_already_structured(result.reply):
            return result
        # If the model called an inspection tool, use its data.
        error_data: dict[str, Any] = {}
        evidence: list[dict[str, Any]] = list(result.evidence or [])
        inspected = any(
            ev.tool in {
                "erp_get_current_error",
                "erp_analyze_pasted_error_with_kb",
                "erp_inspect_current_error_with_kb",
            }
            and ev.status == "ok"
            for ev in result.events
        )
        if inspected:
            error_data = self._extract_error_data(result)
        else:
            # Model didn't call any tool — try to extract the error code
            # directly from the user's pasted text so we can still build
            # a structured response.
            error_data = self._extract_error_from_user_text(self._last_user_text or "")
            # If the message looks like a follow-up answer (dept/role/
            # impact keywords), pull context from active_error.json.
            error_data = self._enrich_with_active_error(error_data)
        if not error_data and not result.reply:
            return result
        # Follow-up reply path: we have user info (dept/role/impact) and
        # pulled the active error context. Do a real KB lookup now and
        # build a recommendation block — DON'T re-ask the same questions.
        if error_data.get("is_followup_reply"):
            kb_hits = self._kb_rg_search(
                error_data.get("error_code")
                or error_data.get("scenario_key")
                or error_data.get("system")
                or ""
            )
            evidence.extend(kb_hits)
            # Acknowledge the user's reply + show what we found in KB.
            ack = self._build_followup_ack(error_data)
            rec_block = self._build_recommendations_block(error_data, evidence)
            result.reply = (result.reply or "").rstrip() + "\n\n" + ack + rec_block
            return result
        # If we have nothing to work with (no error code, no events), just
        # append a generic Japanese followup.
        if not error_data.get("error_code"):
            # At minimum, ask the user to clarify
            block = (
                "**追加でお聞きしたいこと:**\n\n"
                "1. 部署名・役職・業務への影響範囲を教えてください\n"
                "2. 具体的なエラーメッセージ / Trace ID / Correlation ID\n"
                "3. 最後に正常に動作していた時期\n\n"
                "ご回答いただいた上で、社内規程に従った対応をご案内します。"
            )
            result.reply = (result.reply or "").rstrip() + "\n\n" + block
            return result
        block = self._build_response_block(error_data, evidence)
        result.reply = (result.reply or "").rstrip() + "\n\n" + block
        return result

    @staticmethod
    def _kb_rg_search(query: str) -> list[dict[str, Any]]:
        """Real ripgrep-based KB lookup. Used by _ensure_followup_questions
        when the user supplies follow-up answer info — produces real
        evidence instead of letting the model hallucinate."""
        if not query:
            return []
        try:
            from pathlib import Path
            import re as _re
            import subprocess as _sp
            kb_root = Path(__file__).resolve().parents[1] / "knowledge"
            if not kb_root.exists():
                return []
            rg = _sp.run(
                ["rg", "-n", "-i", "--max-count", "5", query, str(kb_root)],
                capture_output=True, text=True, timeout=4,
            )
            hits: list[dict[str, Any]] = []
            for line in (rg.stdout or "").splitlines()[:5]:
                m = _re.match(r"^(.+?):(\d+):(.*)$", line)
                if m:
                    hits.append({
                        "path": m.group(1),
                        "line": int(m.group(2)),
                        "snippet": m.group(3)[:200],
                    })
            return hits
        except Exception:
            return []

    @staticmethod
    def _build_followup_ack(error_data: dict[str, Any]) -> str:
        """Acknowledge the user's follow-up answer (dept/role/etc.) and
        show what context we picked up from active_error.json."""
        name = error_data.get("user_name") or "—"
        dept = error_data.get("department") or "—"
        role = error_data.get("role") or "—"
        system = error_data.get("system") or "ERP"
        code = error_data.get("error_code") or "不明"
        return (
            f"**{name} さん ({dept} / {role}) の情報を受領しました。**\n\n"
            f"状況: {system} で **{code}** が発生中。\n"
        )

    @staticmethod
    def _build_recommendations_block(
        error_data: dict[str, Any],
        evidence: list[dict[str, Any]],
    ) -> str:
        """Build a '推奨される次のステップ' block from real KB evidence and
        scenario-specific recommendations. Used on followup replies —
        differs from _build_response_block in that it does NOT include
        the follow-up question section (we already asked once)."""
        code = str(error_data.get("error_code") or "").strip() or "不明"
        system = str(error_data.get("system") or "").strip() or "ERP"
        symptom = str(error_data.get("symptom") or "").strip()
        rec_lines: list[str] = []
        if evidence:
            for hit in evidence[:2]:
                path = str(hit.get("path") or "").strip()
                snippet = str(hit.get("snippet") or "").strip()
                if not path and not snippet:
                    continue
                if path:
                    short_path = path.split("/")[-1] if "/" in path else path
                    rec_lines.append(f"- **{short_path}** を参照(社内規程)")
                if snippet:
                    snippet = snippet[:120].replace("\n", " ")
                    rec_lines.append(f"  - {snippet}…")
        # Scenario-specific recommendations (kept safe)
        rec_lines.extend(PiAgentRuntime._scenario_recommendations(code, symptom))
        if rec_lines:
            return "**推奨される次のステップ:**\n\n" + "\n".join(rec_lines[:4]) + "\n"
        return (
            "**推奨される次のステップ:**\n\n"
            "- 社内 KB に該当する規程が見つかりませんでした。IT Operations "
            "Agent P に直接お問い合わせください。\n"
        )

    @staticmethod
    def _extract_error_from_user_text(text: str) -> dict[str, Any]:
        """Try to pull error_code / system / symptom out of pasted text.
        Returns a dict (possibly empty) usable by the structured-block
        builder. Pure regex — robust enough for the common paste patterns
        we see in this demo."""
        if not text:
            return {}
        data: dict[str, Any] = {}
        # Error code: AADSTS\d+, NO_ERROR_CODE, PBI_*, LICENSE_*, CA_BLOCK, etc.
        m = re.search(r"\b(AADSTS\d{4,6}|PBI_[A-Z_]+|LICENSE_MISSING|CA_BLOCK|NO_ERROR_CODE)\b", text)
        if m:
            data["error_code"] = m.group(1)
        # Trace ID
        m = re.search(r"Trace\s*ID\s*[:：]?\s*([A-Za-z0-9\-]+)", text)
        if m:
            data["trace_id"] = m.group(1)
        # Correlation ID
        m = re.search(r"Correlation\s*ID\s*[:：]?\s*([A-Za-z0-9\-]+)", text)
        if m:
            data["correlation_id"] = m.group(1)
        # System: looks for "Sign-in failed" → Dynamics 365 / "Sales Hub" → Dynamics 365 Sales
        if re.search(r"sign[- ]?in|Sign[- ]?in", text):
            data["system"] = "Dynamics 365"
            data["symptom"] = "login_failed"
        elif re.search(r"Sales\s*Hub|crm|Customer\s+opportunities", text, re.IGNORECASE):
            data["system"] = "Dynamics 365 Sales"
            data["symptom"] = "menu_missing"
        elif re.search(r"Power\s*BI|report|workspace", text, re.IGNORECASE):
            data["system"] = "Power BI"
            data["symptom"] = "report_permission_denied"
        elif re.search(r"license|License", text):
            data["system"] = "Dynamics 365"
            data["symptom"] = "license_missing"
        # If the text says "additional authentication" or "MFA", set symptom
        if re.search(r"multi[- ]?factor|additional authentication|MFA", text, re.IGNORECASE):
            data.setdefault("symptom", "login_failed")
        # Detect "follow-up answer" patterns — when the user is answering
        # the structured questions (dept/role/impact/timing). If matched,
        # flag the message so the structured-block builder can pull
        # context from the active_error instead of asking the same Q's.
        followup_signals = (
            r"経理部|営業部|人事部|技術部|情報システム|開発部|marketing|sales|"
            r"finance|hr|engineering|legal|operations|"
            r"manager|director|lead|engineer|analyst|"
            r"自分だけ|部署全員|全体|なし|影響.*範囲|"
            r"\d+\s*日前|\d+\s*週間前|昨日|今日|先月"
        )
        if re.search(followup_signals, text, re.IGNORECASE):
            data["looks_like_followup_answer"] = True
        return data

    def _enrich_with_active_error(self, error_data: dict[str, Any]) -> dict[str, Any]:
        """When the user is answering follow-up questions and we can't
        extract an error_code from the message, pull system/error_code/
        trace_id from the active_error.json on disk. This is how the
        chat can produce a real KB-based recommendation instead of
        asking the same three questions again."""
        if not error_data.get("looks_like_followup_answer"):
            return error_data
        try:
            import json
            from pathlib import Path
            err_path = Path(__file__).resolve().parents[1] / "erp_state" / "current_error.json"
            if not err_path.exists():
                return error_data
            state = json.loads(err_path.read_text(encoding="utf-8"))
            if not state.get("active"):
                return error_data
            # Backfill any missing fields from active_error.
            for key in ("error_code", "system", "trace_id", "symptom",
                        "correlation_id", "scenario_key"):
                if not error_data.get(key) and state.get(key):
                    error_data[key] = state[key]
            error_data["user_email"] = state.get("user_email")
            error_data["user_name"] = state.get("user_name")
            error_data["department"] = state.get("department")
            error_data["role"] = state.get("role")
            error_data["scenario_key"] = state.get("scenario_key")
            # Mark as a followup reply so the structured-block builder
            # skips the question block.
            error_data["is_followup_reply"] = True
        except (OSError, json.JSONDecodeError):
            pass
        return error_data

    def _reply_already_structured(self, reply: str) -> bool:
        """Return True if the model already gave a CLEAN Japanese reply
        with follow-up questions AND recommendations, so we don't need
        to post-process. Be strict — a verbose rambling reply that
        happens to contain the words 質問 and 推奨 is NOT structured."""
        if not reply:
            return False
        # The reply must be MOSTLY Japanese (allow error codes / product
        # names which stay in English). If it's mostly English, the model
        # failed the language instruction and we MUST override.
        if self._is_mostly_english(reply):
            return False
        # Reject verbose rambling: structured replies are short. If the
        # reply is more than 800 chars, the model is over-explaining;
        # force our clean block on top.
        if len(reply) > 800:
            return False
        # Must have an explicit follow-up phrasing (not just the word "質問"
        # somewhere). Look for the typical Japanese follow-up patterns.
        has_question = any(
            p in reply
            for p in (
                "教えていただけますか",
                "お聞かせください",
                "確認させてください",
                "以下の点について",
                "追加でお聞きしたい",
            )
        )
        # Must have a recommendations section header.
        has_recommendation = any(
            p in reply
            for p in (
                "推奨される次のステップ",
                "推奨される対応",
                "次のステップ",
                "解決策",
            )
        )
        return has_question and has_recommendation

    @staticmethod
    def _is_mostly_english(text: str, threshold: float = 0.70) -> bool:
        """Rough heuristic: ratio of ASCII letters to total non-space
        characters. Returns True if the text is mostly English (so the
        1.2B model failed to follow the Japanese instruction and we
        need to override).

        Threshold defaults to 0.70 — only flag as "mostly English" if
        the text is overwhelmingly ASCII. This is conservative because
        field-name-style Japanese replies (with English identifiers like
        "AADSTS50076" or "Dynamics 365" mixed in) can easily exceed
        0.45-0.50 even when the spirit of the reply is Japanese."""
        letters = [c for c in text if c.isalpha()]
        if len(letters) < 30:
            return False
        ascii_letters = [c for c in letters if ord(c) < 128]
        return len(ascii_letters) / len(letters) > threshold

    @staticmethod
    def _extract_error_data(result: PiAgentResult) -> dict[str, Any]:
        for ev in reversed(result.events):
            if ev.tool not in {
                "erp_get_current_error",
                "erp_analyze_pasted_error_with_kb",
                "erp_inspect_current_error_with_kb",
            }:
                continue
            if ev.status != "ok":
                continue
            try:
                return json.loads(ev.detail)
            except (json.JSONDecodeError, TypeError):
                continue
        return {}

    def _build_response_block(
        self,
        error_data: dict[str, Any],
        evidence: list[dict[str, Any]],
    ) -> str:
        code = str(error_data.get("error_code") or "").strip() or "不明"
        system = str(error_data.get("system") or "").strip() or "ERP"
        symptom = str(error_data.get("symptom") or "").strip()
        trace = str(error_data.get("trace_id") or "").strip()
        # Build a brief acknowledgement
        ack = f"**{code}** に関するお問い合わせですね。"
        if system:
            ack += f" {system} で発生しているエラーを確認しました。"
        ack += "\n\n"

        # 2-3 follow-up questions — adapt to whether the error is vague.
        questions: list[str] = []
        if not code or code.upper() in {"NO_ERROR_CODE", "NONE", "N/A"}:
            questions.append("1. 正確なエラーコード(Trace ID と共にお知らせください)")
            questions.append("2. 部署名・役職・業務への影響範囲")
        if symptom.lower() in {
            "menu_missing", "access_issue", "access_denied",
            "login_failed", "permission_denied", "unknown",
            "",  # missing symptom
        }:
            questions.append("1. 具体的な症状(グレーアウト / 完全に非表示 / エラーメッセージ)")
            questions.append("2. 影響範囲(あなただけ / 部署全員 / 全体)")
            questions.append("3. 最後に正常に動作していた時期と、その間の変更点")
        if not questions:
            # Even for specific errors, ask a couple of useful questions.
            questions.append("1. このエラーは再現しますか?再現手順を教えてください")
            questions.append("2. 他の同僚も同じエラーが出ていますか?")
        if trace:
            questions.append(f"3. Trace ID **{trace}** を社内サポート担当に共有済みですか?")
        followup = (
            "**追加でお聞きしたいこと:**\n\n"
            + "\n".join(questions)
            + "\n"
        )

        # Recommended next steps: synthesize from KB evidence or generate
        # scenario-specific ones.
        rec_lines: list[str] = []
        if evidence:
            for hit in evidence[:2]:
                path = str(hit.get("path") or "").strip()
                snippet = str(hit.get("snippet") or "").strip()
                if not path and not snippet:
                    continue
                # Use a short reference, not the whole snippet
                if path:
                    short_path = path.split("/")[-1] if "/" in path else path
                    rec_lines.append(f"- **{short_path}** を参照(社内規程に従った対応)")
                if snippet:
                    snippet = snippet[:120].replace("\n", " ")
                    rec_lines.append(f"  - {snippet}…")
        # Scenario-specific recommendations (kept short and safe — never
        # recommend password reset / MFA disable / license assignment).
        rec_lines.extend(self._scenario_recommendations(code, symptom))

        if rec_lines:
            recommendations = (
                "**推奨される次のステップ:**\n\n"
                + "\n".join(rec_lines[:4])
                + "\n"
            )
        else:
            recommendations = ""

        return ack + followup + recommendations

    @staticmethod
    def _scenario_recommendations(code: str, symptom: str) -> list[str]:
        """Return short, safe recommendations based on the error code.
        These are intentionally generic — the real work happens through
        the local KB / IT ticket handoff, not in this chat."""
        out: list[str] = []
        cu = code.upper()
        if "AADSTS50076" in cu or symptom == "login_failed":
            out.append(
                "- Microsoft Authenticator アプリで多要素認証 (MFA) 通知を承認してください"
            )
            out.append(
                "- 別デバイス / シークレットウィンドウで再ログインをお試しください"
            )
            out.append(
                "- 解決しない場合は IT 部門に MFA リセットを依頼してください"
            )
        elif "AADSTS50105" in cu:
            out.append(
                "- 該当システムへのアプリケーション割り当てが、組織側で有効かご確認ください"
            )
            out.append(
                "- アクセス申請フォームから上長承認を取得してください"
            )
        elif "LICENSE" in cu.upper() or symptom == "license_missing":
            out.append(
                "- Dynamics 365 / Microsoft 365 の利用開始申請をご確認ください"
            )
            out.append(
                "- 上長承認後、IT 部門がライセンスを割り当てます"
            )
        elif "CA_BLOCK" in cu or "CONDITIONAL" in cu.upper():
            out.append(
                "- Conditional Access ポリシーが会社支給端末以外をブロックしています"
            )
            out.append(
                "- VPN 接続後、または会社支給端末から再アクセスしてください"
            )
        elif "MENU" in symptom.upper() or symptom == "menu_missing":
            out.append(
                "- 該当システムでの Business Unit / セキュリティロールをご確認ください"
            )
            out.append(
                "- CRM Owner / Dynamics 管理者にロール付与を依頼してください"
            )
        elif "POWERBI" in cu.upper() or "PBI" in cu:
            out.append(
                "- Power BI ワークスペース / レポート / データセットへの権限をご確認ください"
            )
            out.append(
                "- BI 管理者 / Data Platform Team にアクセス権付与を依頼してください"
            )
        return out

    def _run_pi(
        self,
        user_text: str,
        tool_profile: str,
        today: str,
        env: dict[str, str],
        retry_instruction: str | None = None,
        skill_path: Path | None = None,
        system_prompt: str | None = None,
    ) -> PiAgentResult:
        command = [
            str(self.pi_cli),
            "--approve",
            "--offline",
            "--provider",
            self.provider,
            "--model",
            self.model,
            "--thinking",
            "off",
            "--mode",
            "json",
        ]
        if tool_profile == "none":
            command.append("--no-tools")
        elif tool_profile == "erp_analysis":
            command.extend(["--tools", ",".join(ERP_ANALYSIS_TOOLS)])
        elif tool_profile == "erp_current_error":
            command.extend(["--tools", ",".join(ERP_CURRENT_ERROR_TOOLS)])
        elif tool_profile == "erp_ticket":
            command.extend(["--tools", ",".join(ERP_TICKET_TOOLS)])
        elif tool_profile == "erp_it":
            command.extend(["--tools", ",".join(IT_TOOLS)])
        elif tool_profile == "erp_all":
            pass
        command.extend([
            "--extension",
            str(self.extension_path),
            "--skill",
            str(skill_path or self.skill_path),
            "--append-system-prompt",
            system_prompt or self._system_prompt(tool_profile, today, retry_instruction),
            "-p",
            user_text,
        ])

        try:
            result = subprocess.run(
                command,
                cwd=self.app_dir,
                env=env,
                check=False,
                capture_output=True,
                text=True,
                timeout=PI_TIMEOUT_SECONDS,
                encoding="utf-8",
                errors="replace",
            )
        except subprocess.TimeoutExpired:
            return PiAgentResult(
                reply="Agent P timed out while processing the request.",
                events=[PiAgentEvent("pi_agent", "timeout", f">{PI_TIMEOUT_SECONDS}s")],
            )
        except (subprocess.SubprocessError, FileNotFoundError) as exc:
            return PiAgentResult(
                reply="Agent P failed to start.",
                events=[PiAgentEvent("pi_agent", "error", str(exc))],
            )

        parsed = self._parse_json_events(result.stdout)
        if result.returncode != 0 and not parsed.reply:
            detail = result.stderr.strip() or f"exit code {result.returncode}"
            return PiAgentResult(
                reply="Agent P returned an error.",
                events=[*parsed.events, PiAgentEvent("pi_agent", "error", detail)],
                session_file=parsed.session_file,
            )
        return parsed

    def _tool_profile(self, user_text: str) -> str:
        if self._needs_builtin_tools(user_text):
            return "all"
        normalized = user_text.lower()
        if not any(pattern in normalized for pattern in ERP_INTENT_PATTERNS):
            return "none"
        if any(pattern in normalized for pattern in TICKET_INTENT_PATTERNS):
            return "erp_ticket"
        if any(pattern in normalized for pattern in ["今出ている", "現在のエラー", "current error", "current page", "画面", "ログを取得"]):
            return "erp_current_error"
        return "erp_analysis"

    def _profile_instruction(self, tool_profile: str) -> str:
        if tool_profile == "none":
            return (
                "No tools are available. Answer directly in Japanese. "
                "For date/day questions, answer exactly with the current date and weekday "
                "from this system prompt. Do not mention holidays or anniversaries."
            )
        if tool_profile == "erp_analysis":
            return (
                "MUST call erp_analyze_pasted_error_with_kb before answering. Do not create a ticket. "
                "After the tool returns, decide whether the error data has enough context to answer. "
                "If error_code is missing OR symptom is vague OR the user has not provided their "
                "department / role / exact reproduction, you MUST ask 2-3 specific follow-up "
                "questions in Japanese BEFORE giving a final answer. Do not invent missing details. "
                "Reply structure for vague errors: 1) acknowledge briefly, 2) list specific questions, "
                "3) stop. Do not call create_ticket in this profile."
            )
        if tool_profile == "erp_current_error":
            return (
                "MUST call erp_get_current_error before answering. Do not create a ticket. "
                "After the tool returns, classify the error: "
                "(A) SPECIFIC error_code + clear symptom + clear system -> you may give a direct "
                "operational answer based on the local knowledge base. "
                "(B) VAGUE error (error_code is 'NO_ERROR_CODE' or missing, or symptom is generic "
                "like 'menu missing' / 'access issue' / 'cannot see') -> you MUST ask 2-3 specific "
                "follow-up questions in Japanese BEFORE giving any operational answer. "
                "Useful follow-ups to ask: "
                "- 部署・役職 (department / role) "
                "- 具体的な症状 (concrete symptom: hidden vs greyed-out vs error toast) "
                "- 影響範囲 (scope: just you, your team, or everyone) "
                "- 最終正常動作日時 (when did it last work) "
                "Reply structure for vague errors: 1) acknowledge in 1 sentence, "
                "2) numbered list of 2-3 follow-up questions, 3) stop. Do not recommend actions yet."
            )
        if tool_profile == "erp_ticket":
            return (
                "MUST call erp_create_ticket_from_current_error before answering. Return the ticket id. "
                "Only proceed with a ticket if the user explicitly asked to contact IT / create a ticket."
            )
        return "Built-in tools are available because the user asked for file, code, or system operations."

    def _required_tool(self, tool_profile: str) -> str | None:
        if tool_profile == "erp_analysis":
            return "erp_analyze_pasted_error_with_kb"
        if tool_profile == "erp_current_error":
            return "erp_get_current_error"
        if tool_profile == "erp_ticket":
            return "erp_create_ticket_from_current_error"
        return None

    def _has_required_tool(self, result: PiAgentResult, required_tool: str | None) -> bool:
        if not required_tool:
            return True
        return any(event.tool == required_tool and event.status == "ok" for event in result.events)

    def _system_prompt(self, tool_profile: str, today: str, retry_instruction: str | None = None) -> str:
        retry = f" {retry_instruction}" if retry_instruction else ""
        return (
            "You are Agent P, an internal ERP / CRM / SSO support assistant. "
            "You help employees troubleshoot sign-in failures, permission and license requests, "
            "Power BI access, and route unresolved issues to IT as tickets. "
            f"Current local date is {today} in Asia/Tokyo. "
            f"{self._profile_instruction(tool_profile)} "
            "LANGUAGE: this is a Japanese-language internal support tool. "
            "ALWAYS write your explanation, analysis, recommendations, and follow-up questions "
            "in Japanese, even if the user pastes English error text or technical terms. "
            "Keep English error codes and product names (AADSTS50076, Dynamics 365, MFA, etc.) "
            "as-is — only the surrounding prose must be Japanese. "
            "If the user writes in Chinese or English, still reply in Japanese. "
            "Do not mention tool names unless reporting completed tool activity. "
            "INFORMATION GAPS: when the user's question is missing critical context "
            "(department, exact symptom, manager's name, error reproduction, etc.), "
            "ASK 1-3 specific follow-up questions in Japanese BEFORE giving a final answer. "
            "Only give a complete answer when the question has enough context. "
            "If the user asks about your identity or capabilities, answer briefly in 1-2 sentences. "
            "Do not enumerate documentation files, configuration options, or training data. "
            "Do not call any tool for identity or capability questions — answer in plain text."
            f"{retry}"
        )

    def _needs_builtin_tools(self, user_text: str) -> bool:
        normalized = user_text.lower()
        return any(pattern in normalized for pattern in BUILTIN_TOOL_INTENT_PATTERNS)

    def _direct_basic_reply(self, user_text: str) -> str | None:
        # Bypass the LLM for short, deterministic exchanges where a 1.2B model
        # cannot reliably override pi-coding-agent's default "You are an expert
        # coding assistant" identity, and where the answer is not tool-related.
        text = (user_text or "").strip()
        lower = text.lower()

        # Identity questions — answer in the user's input language, never the
        # underlying model's default (which leaks pi-coding-agent identity).
        identity_patterns = (
            "你是谁", "您是谁", "你叫什么", "你是什么", "你是啥", "介绍下自己", "自我介绍一下", "介绍一下你自己",
            "who are you", "what are you", "what's your name", "introduce yourself",
            "お前は誰", "あなたは誰", "誰ですか", "自己紹介",
        )
        if any(p in lower for p in identity_patterns):
            return self._identity_reply(text)

        # Capability questions — short, scannable list, no model call.
        capability_patterns = (
            "你能做什么", "你能干啥", "你会什么", "可以做什么", "你有什么功能",
            "what can you do", "what can you help", "what do you do", "your capabilities",
            "何ができますか", "何ができる", "何を手伝える", "何ができます",
        )
        if any(p in lower for p in capability_patterns):
            return self._capability_reply(text)

        # Date / day-of-week — answer deterministically from the system clock.
        date_patterns = (
            "今天几号", "今天日期", "今天星期", "今天周几", "周几", "星期几",
            "what date", "what day", "today's date", "date today", "what is today",
            "今日は何日", "今日は何曜日", "何日", "何曜日",
        )
        if any(p in lower for p in date_patterns):
            return self._date_reply()

        # Pure greetings — keep these short and in the user's language.
        greeting_patterns = (
            "你好", "您好", "hi", "hello", "hey", "good morning", "good afternoon",
            "こんにちは", "こんばんは", "おはよう",
        )
        if lower in greeting_patterns or any(lower == p for p in greeting_patterns):
            return self._greeting_reply(text)

        return None

    def _identity_reply(self, user_text: str) -> str:
        lang = self._detect_language(user_text)
        if lang == "zh":
            return (
                "我是 Agent P,公司内部的 ERP / CRM / SSO 支持助手。"
                "我可以帮你处理登录失败、权限申请、许可证、Power BI 访问以及开 IT 工单等事务。"
            )
        if lang == "ja":
            return (
                "私は Agent P です。社内 ERP / CRM / SSO サポートのアシスタントとして、"
                "ログイン失敗、権限申請、ライセンス、Power BI アクセス、IT チケット起票などを手伝います。"
            )
        return (
            "I'm Agent P, an internal ERP / CRM / SSO support assistant. "
            "I help with sign-in failures, permission and license requests, "
            "Power BI access, and opening IT tickets."
        )

    def _capability_reply(self, user_text: str) -> str:
        lang = self._detect_language(user_text)
        if lang == "zh":
            return (
                "我可以帮你:\n"
                "• 解读 ERP/CRM/SSO 报错(AADSTS、Salesforce、Power BI、license 等)\n"
                "• 查询当前页面上的错误日志\n"
                "• 检索公司内部知识库(SSO / MFA / 权限 / license / 路由策略)\n"
                "• 起草并提交 IT 工单,自动分派到对应团队"
            )
        if lang == "ja":
            return (
                "私ができること:\n"
                "• ERP / CRM / SSO エラー(AADSTS、Salesforce、Power BI、ライセンスなど)の読み解き\n"
                "• 現在の画面のエラーログの確認\n"
                "• 社内ナレッジ(SSO / MFA / 権限 / ライセンス / ルーティング)の検索\n"
                "• IT チケットの下書きと起票(適切なチームへ自動振り分け)"
            )
        return (
            "I can help with:\n"
            "• Reading ERP/CRM/SSO errors (AADSTS, Salesforce, Power BI, license, ...)\n"
            "• Inspecting the current page error log\n"
            "• Searching the local knowledge base (SSO, MFA, permissions, license, routing)\n"
            "• Drafting and creating IT tickets routed to the right team"
        )

    def _greeting_reply(self, user_text: str) -> str:
        lang = self._detect_language(user_text)
        if lang == "zh":
            return "你好!我是 Agent P,有什么可以帮你的?"
        if lang == "ja":
            return "こんにちは!Agent P です。何かお手伝いできることはありますか?"
        return "Hi! I'm Agent P. How can I help?"

    def _date_reply(self) -> str:
        # Pi runs in Asia/Tokyo; mirror the system prompt's locale so the user
        # sees the same date/weekday we tell the model.
        from datetime import datetime as _dt
        from zoneinfo import ZoneInfo
        now = _dt.now(tz=ZoneInfo("Asia/Tokyo"))
        weekdays_zh = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]
        weekdays_ja = ["月曜日", "火曜日", "水曜日", "木曜日", "金曜日", "土曜日", "日曜日"]
        weekdays_en = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        i = now.weekday()
        return (
            f"今天 {now.strftime('%Y-%m-%d')} "
            f"({weekdays_zh[i]} / {weekdays_ja[i]} / {weekdays_en[i]}), "
            f"Asia/Tokyo 时区。"
        )

    @staticmethod
    def _detect_language(text: str) -> str:
        """Return 'ja', 'zh', or 'en' based on the dominant script in `text`."""
        has_ja = False  # Hiragana / Katakana
        has_zh = False  # CJK Unified Ideographs
        for c in text:
            cp = ord(c)
            if 0x3040 <= cp <= 0x309F or 0x30A0 <= cp <= 0x30FF:
                has_ja = True
            elif 0x4E00 <= cp <= 0x9FFF:
                has_zh = True
        if has_ja:
            return "ja"
        if has_zh:
            return "zh"
        return "en"

    def _parse_json_events(self, output: str) -> PiAgentResult:
        events: list[PiAgentEvent] = []
        evidence: list[dict[str, Any]] = []
        final_reply = ""
        ticket: dict[str, Any] | None = None
        session_file: str | None = None

        for line in output.splitlines():
            if not line.strip():
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                continue

            if payload.get("type") == "session":
                session_file = payload.get("sessionFile") or payload.get("id")
                continue

            if payload.get("type") == "tool_execution_start":
                events.append(PiAgentEvent(payload.get("toolName", "tool"), "start", self._short_json(payload.get("args"))))
            elif payload.get("type") == "tool_execution_end":
                tool_name = payload.get("toolName", "tool")
                status = "error" if payload.get("isError") else "ok"
                result = payload.get("result")
                events.append(PiAgentEvent(tool_name, status, self._tool_detail(result)))
                if tool_name in {"kb_rg_search", "erp_inspect_current_error_with_kb", "erp_analyze_pasted_error_with_kb", "erp_create_ticket_from_current_error"}:
                    evidence = self._extract_evidence(result) or evidence
                if tool_name in {"erp_create_ticket", "erp_create_ticket_from_current_error"}:
                    ticket = self._extract_ticket(result)
            elif payload.get("type") == "agent_end":
                messages = payload.get("messages", [])
                for message in reversed(messages):
                    if message.get("role") == "assistant":
                        final_reply = self._message_text(message)
                        if final_reply:
                            break
            elif payload.get("type") == "message_end":
                message = payload.get("message", {})
                if message.get("role") == "assistant":
                    text = self._message_text(message)
                    if text:
                        final_reply = text

        return PiAgentResult(
            reply=final_reply or "Agent P did not produce a text response.",
            events=events,
            evidence=evidence,
            ticket=ticket,
            session_file=session_file,
        )

    def _message_text(self, message: dict[str, Any]) -> str:
        parts = []
        for item in message.get("content", []):
            if isinstance(item, dict) and item.get("type") == "text":
                parts.append(str(item.get("text", "")))
        return "\n".join(part for part in parts if part).strip()

    def _tool_detail(self, result: Any) -> str:
        if isinstance(result, dict):
            content = result.get("content")
            if isinstance(content, list) and content:
                first = content[0]
                if isinstance(first, dict) and first.get("text"):
                    return str(first["text"])[:240]
            if result.get("details"):
                return self._short_json(result["details"])
        return self._short_json(result)

    def _extract_ticket(self, result: Any) -> dict[str, Any] | None:
        if not isinstance(result, dict):
            return None
        details = result.get("details")
        if isinstance(details, dict) and details.get("ticket_id"):
            return details
        if isinstance(details, dict) and isinstance(details.get("ticket"), dict) and details["ticket"].get("ticket_id"):
            return details["ticket"]
        content = result.get("content")
        if isinstance(content, list) and content:
            text = content[0].get("text") if isinstance(content[0], dict) else None
            if text:
                try:
                    parsed = json.loads(text)
                except json.JSONDecodeError:
                    return None
                return parsed if isinstance(parsed, dict) and parsed.get("ticket_id") else None
        return None

    def _extract_evidence(self, result: Any) -> list[dict[str, Any]]:
        details = self._result_details(result)
        hits = details.get("hits") if isinstance(details, dict) else None
        if isinstance(hits, list):
            return [hit for hit in hits if isinstance(hit, dict)]
        evidence = details.get("evidence") if isinstance(details, dict) else None
        if isinstance(evidence, list):
            return [hit for hit in evidence if isinstance(hit, dict)]
        ticket = details.get("ticket") if isinstance(details, dict) else None
        if isinstance(ticket, dict) and isinstance(ticket.get("evidence"), list):
            return [hit for hit in ticket["evidence"] if isinstance(hit, dict)]
        return []

    def _result_details(self, result: Any) -> dict[str, Any]:
        if not isinstance(result, dict):
            return {}
        details = result.get("details")
        if isinstance(details, dict):
            return details
        content = result.get("content")
        if isinstance(content, list) and content:
            first = content[0]
            text = first.get("text") if isinstance(first, dict) else None
            if isinstance(text, str):
                try:
                    parsed = json.loads(text)
                except json.JSONDecodeError:
                    return {}
                return parsed if isinstance(parsed, dict) else {}
        return {}

    def _short_json(self, value: Any) -> str:
        try:
            text = json.dumps(value, ensure_ascii=False)
        except TypeError:
            text = str(value)
        return text[:240]

    def _user_wants_ticket(self, user_text: str) -> bool:
        """Return True if the user is asking to create a ticket / contact IT."""
        if not user_text:
            return False
        normalized = user_text.lower()
        return any(p in normalized for p in TICKET_INTENT_PATTERNS)

    def _create_ticket_directly(self, user_text: str) -> PiAgentResult:
        """Build a real ticket from current_error.json + local KB — bypass
        the model entirely. The 1.2B model hallucinates ticket IDs and
        content (e.g. 'ERC20260117-001' with placeholder text), so we
        read the structured state and emit a real KW-#### ticket in the
        same format the TypeScript extension would produce.
        """
        from pathlib import Path as _Path
        # Locate the active error state. The app.py writes it to
        # erp_state/current_error.json relative to the project root.
        err_path = _Path(__file__).resolve().parents[1] / "erp_state" / "current_error.json"
        if not err_path.exists():
            return PiAgentResult(
                reply="申し訳ありません、現在アクティブなエラー情報がありません。先にシナリオを選択してください。",
            )
        try:
            state = json.loads(err_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            return PiAgentResult(
                reply=f"エラー状態の読み込みに失敗しました: {exc}",
            )
        if not state.get("active"):
            return PiAgentResult(
                reply="現在、ERP画面にアクティブなエラーはありません。先に「Sign in」を実行してください。",
            )

        # Look up scenario defaults (risk / priority / route / category / etc.)
        scenarios = getattr(self, "_scenarios", None) or self._load_scenarios()
        scenario_key = state.get("scenario_key") or "AADSTS50076"
        scn = scenarios.get(scenario_key, scenarios.get("AADSTS50076", {}))

        # Build the ticket fields, falling back to scenario defaults.
        system = state.get("system") or scn.get("system", "unknown-system")
        error_code = state.get("error_code") or scn.get("error_code", "NO_ERROR_CODE")
        category = scn.get("category", "Agent P ticket")
        risk = scn.get("risk", "Medium")
        priority = scn.get("priority", "P3")
        route = scn.get("route", "IT Operations")
        impact = scn.get("impact", "single_user")
        requester = state.get("user_email") or "demo.user@demo.local"
        trace = state.get("trace_id") or ""
        summary = f"{user_text} / {system} / {error_code} / trace {trace}"

        # Generate a KW-#### ticket id matching the TypeScript algorithm.
        def make_ticket_id(seed: str) -> str:
            h = 0
            for ch in seed:
                h = (h * 31 + ord(ch)) & 0xFFFFFFFF
            return f"KW-{(h % 9000) + 1000:04d}"
        ticket_id = make_ticket_id(f"{summary}:{route}")

        # Optional: pull a few KB evidence lines via ripgrep.
        evidence: list[dict[str, Any]] = []
        try:
            kb_root = _Path(__file__).resolve().parents[1] / "knowledge"
            if kb_root.exists():
                query = error_code or system
                if query:
                    rg = subprocess.run(
                        ["rg", "-n", "-i", "--max-count", "5", query, str(kb_root)],
                        capture_output=True, text=True, timeout=4,
                    )
                    for line in (rg.stdout or "").splitlines()[:5]:
                        m = re.match(r"^(.+?):(\d+):(.*)$", line)
                        if m:
                            evidence.append({
                                "path": m.group(1),
                                "line": int(m.group(2)),
                                "snippet": m.group(3)[:200],
                            })
        except (subprocess.TimeoutExpired, OSError):
            pass

        ticket = {
            "ticket_id": ticket_id,
            "status": "New",
            "requester": requester,
            "system": system,
            "error_code": error_code,
            "category": category,
            "risk": risk,
            "priority": priority,
            "route": route,
            "impact": impact,
            "summary": summary,
            "evidence": evidence,
            "evidence_summary": "current ERP error and local KB evidence",
            "blocked_actions": scn.get("blocked_actions", []),
        }

        # Friendly Japanese reply. Quote the real ticket id so the user can
        # see it in the chat and in the IT Operations view.
        reply = (
            f"**IT チケットを作成しました**\n\n"
            f"- **チケットID:** `{ticket_id}`\n"
            f"- **担当:** {route}\n"
            f"- **優先度:** {priority} · リスク: {risk}\n"
            f"- **影響範囲:** {impact}\n"
            f"- **システム:** {system}\n"
            f"- **エラーコード:** {error_code}\n"
            f"- **依頼者:** {requester}\n"
            f"- **参照トレースID:** {trace or 'なし'}\n\n"
            f"エビデンス {len(evidence)} 件を添付しました。\n"
            f"左メニューの **IT Operations** から進捗を確認できます。"
        )
        return PiAgentResult(
            reply=reply,
            ticket=ticket,
            evidence=evidence,
            events=[PiAgentEvent("erp_create_ticket_from_current_error", "ok", json.dumps(ticket, ensure_ascii=False)[:240])],
        )

    # ── IT-side action short-circuit (mirror of _create_ticket_directly) ──
    # The 1.2B model hallucinates ticket IDs and resolution notes when the
    # user asks the IT Agent to resolve / close / reassign / comment on a
    # ticket. We detect the intent (Japanese verb + optional KW-#### in
    # text), pick the ticket id, and call the Python mutator from app.py
    # directly. Same rationale as _create_ticket_directly on the Employee
    # side: code-level enforcement of state transitions.

    # Match KW-#### where #### is exactly 4 digits, not followed by
    # another digit. The previous pattern used \b which doesn't
    # transition between ASCII digits and Japanese characters, so
    # "KW-5511エラーの原因" failed to match.
    _IT_TICKET_ID_RE = re.compile(r"KW-\d{4}(?!\d)")

    def _extract_it_ticket_id(self, user_text: str) -> str | None:
        """Pull a KW-#### ticket id out of the user's chat text, or return
        None if none is present."""
        if not user_text:
            return None
        m = self._IT_TICKET_ID_RE.search(user_text)
        return m.group(0) if m else None

    def _user_wants_it_action(self, user_text: str) -> str | None:
        """Detect the IT-side action the user is asking for. Returns one
        of: "resolve", "close", "reassign", "triage", "comment", or None."""
        if not user_text:
            return None
        lower = user_text.lower()
        if any(p in lower for p in IT_RESOLVE_PATTERNS):
            return "resolve"
        if any(p in lower for p in IT_CLOSE_PATTERNS):
            return "close"
        if any(p in lower for p in IT_REASSIGN_PATTERNS):
            return "reassign"
        if any(p in lower for p in IT_TRIAGE_PATTERNS):
            return "triage"
        if any(p in lower for p in IT_COMMENT_PATTERNS):
            return "comment"
        return None

    def _get_app_mutators(self):
        """Lazy-fetch the ticket mutators from app.py via sys.modules.
        Cached after first call. Using sys.modules avoids re-importing
        app.py inside an active streamlit rerun (which can re-trigger
        UI rendering and cause "duplicate radio" warnings)."""
        if getattr(self, "_app_mutators", None) is not None:
            return self._app_mutators
        import sys as _sys
        app_mod = _sys.modules.get("app")
        if app_mod is None:
            # Fallback: not loaded yet (e.g. running tests). Import it.
            import importlib
            app_mod = importlib.import_module("app")
        self._app_mutators = (
            app_mod.resolve_ticket,
            app_mod.close_ticket,
            app_mod.reassign_ticket,
            app_mod.triage_ticket,
            app_mod.add_comment_to_ticket,
        )
        return self._app_mutators

    def _direct_it_action(self, user_text: str) -> PiAgentResult | None:
        """If user_text expresses a ticket-mutating intent
        (resolve/close/reassign/triage), redirect the operator to the
        UI action buttons instead of executing the mutation from chat.

        Returns None if the message is not an action request (caller
        falls through to the LLM). Returns a redirect PiAgentResult
        when the user clearly wants a status mutation — that result
        is rendered in the IT chat without invoking the model.

        Ticket comments via `erp_it_add_comment` are still permitted
        from chat (they're informational, not status-mutating); we
        let those fall through to the LLM path so the model can
        choose to add a `[Agent P 分析]` note or refuse.
        """
        action = self._user_wants_it_action(user_text)
        if action is None:
            return None
        # Comment is the only "soft" action — let the LLM handle it.
        if action == "comment":
            return None
        verb_jp = {
            "resolve": "解決",
            "close": "クローズ",
            "reassign": "再分派",
            "triage": "トリアージ",
        }[action]
        ticket_id = self._extract_it_ticket_id(user_text) or "—"
        reply = (
            f"**{ticket_id} の {verb_jp}はチャットからは実行しません**\n\n"
            f"IT Operations コンソールのチケット詳細カードの "
            f"「{verb_jp}」ボタンからおこなってください。\n\n"
            "代わりに、このチケットについて KB を参照した分析を"
            "お出しできます。エラーコード、症状、再現手順などを"
            "お教えいただければ、考えられる原因をリストアップします。"
        )
        return PiAgentResult(
            reply=reply,
            events=[PiAgentEvent("it_action_shortcut", "redirect_to_ui", f"{action}:{ticket_id}")],
        )

    def _load_scenarios(self) -> dict[str, dict[str, Any]]:
        """Lazy-load the SCENARIOS dict from app.py so we don't duplicate it."""
        if getattr(self, "_scenarios", None) is None:
            try:
                import importlib
                app_mod = importlib.import_module("app")
                self._scenarios = getattr(app_mod, "SCENARIOS", {})
            except Exception:
                self._scenarios = {}
        return self._scenarios
