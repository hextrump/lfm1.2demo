from __future__ import annotations

import json
import os
import subprocess
import re
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
KNOWLEDGE_DIR = APP_DIR / "knowledge"
CURRENT_ERROR_PATH = APP_DIR / "erp_state" / "current_error.json"
PI_PROVIDER = "local-lfm"
PI_MODEL = "lfm2.5-1.2b-instruct"
PI_TIMEOUT_SECONDS = 90
PI_TOOL_RETRY_LIMIT = 2

SCENARIOS: dict[str, dict[str, Any]] = {
    "AADSTS50076": {
        "system": "Dynamics 365",
        "symptom": "login_failed",
        "error_code": "AADSTS50076",
        "category": "Microsoft Entra ID / MFA / Conditional Access",
        "risk": "Medium",
        "priority": "P3",
        "route": "Identity / Entra ID 管理チーム",
        "impact": "single_user",
        "knowledge_query": "AADSTS50076",
        "blocked_actions": ["password_reset", "mfa_disable", "permission_grant", "conditional_access_change"],
    },
    "AADSTS50105": {
        "system": "Salesforce",
        "symptom": "app_assignment_missing",
        "error_code": "AADSTS50105",
        "category": "Application Assignment / Permission",
        "risk": "Medium",
        "priority": "P3",
        "route": "業務システム権限管理チーム",
        "impact": "single_user",
        "knowledge_query": "AADSTS50105",
        "blocked_actions": ["permission_grant", "license_assignment"],
    },
    "LICENSE_MISSING": {
        "system": "Dynamics 365",
        "symptom": "license_missing",
        "error_code": "LICENSE_MISSING",
        "category": "License / Microsoft 365",
        "risk": "Medium",
        "priority": "P3",
        "route": "Microsoft 365 ライセンス管理チーム",
        "impact": "single_user",
        "knowledge_query": "License missing",
        "blocked_actions": ["license_assignment"],
    },
    "CA_BLOCK": {
        "system": "社内ERP",
        "symptom": "conditional_access_block",
        "error_code": "CA_BLOCK",
        "category": "Security / Conditional Access",
        "risk": "High",
        "priority": "P2",
        "route": "Security / Conditional Access チーム",
        "impact": "single_user",
        "knowledge_query": "Conditional Access blocked",
        "blocked_actions": ["conditional_access_change", "mfa_disable"],
    },
    "CRM_MENU_MISSING": {
        "system": "Dynamics 365 Sales",
        "symptom": "menu_missing",
        "error_code": "NO_ERROR_CODE",
        "category": "CRM Role / Business Unit Permission",
        "risk": "Medium",
        "priority": "P3",
        "route": "CRM Owner / Dynamics 管理者",
        "impact": "single_user",
        "knowledge_query": "Dynamics 365 Sales Security role missing",
        "blocked_actions": ["permission_grant"],
    },
    "POWERBI_DENIED": {
        "system": "Power BI",
        "symptom": "report_permission_denied",
        "error_code": "PBI_ACCESS_DENIED",
        "category": "Power BI Workspace / Dataset Permission",
        "risk": "Low",
        "priority": "P3",
        "route": "BI 管理者 / Data Platform Team",
        "impact": "single_user",
        "knowledge_query": "Power BI Workspace permission denied",
        "blocked_actions": ["permission_grant"],
    },
    "MULTI_USER_OUTAGE": {
        "system": "社内ERP",
        "symptom": "multi_user_outage",
        "error_code": "MULTI_USER_OUTAGE",
        "category": "IT Ops / Service Incident",
        "risk": "High",
        "priority": "P2",
        "route": "IT Ops / Incident Manager",
        "impact": "multiple_users",
        "knowledge_query": "Multiple users incident",
        "blocked_actions": ["user_specific_reset"],
    },
    "VENDOR_MFA_EXCEPTION": {
        "system": "Integration Account",
        "symptom": "vendor_mfa_exception",
        "error_code": "VENDOR_MFA_EXCEPTION",
        "category": "Security Exception / Vendor Access",
        "risk": "High",
        "priority": "P2",
        "route": "Security Team + IAM Approval Board",
        "impact": "privileged_account",
        "knowledge_query": "Integration Account MFA exception request",
        "blocked_actions": ["mfa_disable", "conditional_access_change", "privilege_grant"],
    },
}

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
        if self._has_required_tool(parsed, required_tool):
            return self._normalize_tool_result(user_text, tool_profile, parsed)
        if not required_tool:
            return parsed

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
                return self._normalize_tool_result(user_text, tool_profile, retry)
            last = retry
        fallback = self._erp_fallback(user_text, tool_profile, required_tool)
        fallback.events = [
            PiAgentEvent("pi_agent", "error", f"required tool was not called: {required_tool}"),
            *last.events,
            *fallback.events,
        ]
        return fallback

    def _run_pi(
        self,
        user_text: str,
        tool_profile: str,
        today: str,
        env: dict[str, str],
        retry_instruction: str | None = None,
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
        elif tool_profile == "erp_all":
            pass
        command.extend([
            "--extension",
            str(self.extension_path),
            "--skill",
            str(self.skill_path),
            "--append-system-prompt",
            self._system_prompt(tool_profile, today, retry_instruction),
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
            return "No tools are available. Answer directly. For date/day questions, answer exactly with the current date and weekday from this system prompt. Do not mention holidays or anniversaries."
        if tool_profile == "erp_analysis":
            return "MUST call erp_analyze_pasted_error_with_kb before answering. Do not create a ticket."
        if tool_profile == "erp_current_error":
            return "MUST call erp_get_current_error before answering."
        if tool_profile == "erp_ticket":
            return "MUST call erp_create_ticket_from_current_error before answering. Return the ticket id."
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

    def _normalize_tool_result(self, user_text: str, tool_profile: str, result: PiAgentResult) -> PiAgentResult:
        if tool_profile == "erp_analysis":
            details = self._analyze_pasted_error(user_text)
            result.reply = self._format_analysis_reply(details)
            result.evidence = details.get("evidence", result.evidence)
        return result

    def _erp_fallback(self, user_text: str, tool_profile: str, required_tool: str) -> PiAgentResult:
        if tool_profile == "erp_analysis":
            details = self._analyze_pasted_error(user_text)
            return PiAgentResult(
                reply=self._format_analysis_reply(details),
                events=[PiAgentEvent(required_tool, "fallback", "runtime executed ERP analysis because Pi did not call the required tool")],
                evidence=details.get("evidence", []),
            )
        if tool_profile == "erp_current_error":
            return self._current_error_fallback(user_text, required_tool)
        if tool_profile == "erp_ticket":
            ticket = self._create_ticket_from_current_error(user_text)
            return PiAgentResult(
                reply=f"チケットを作成しました: {ticket['ticket_id']}。担当キュー: {ticket['route']}、優先度: {ticket['priority']}。",
                events=[PiAgentEvent(required_tool, "fallback", "runtime created simulated ERP ticket because Pi did not call the required tool")],
                evidence=ticket.get("evidence", []),
                ticket=ticket,
            )
        return PiAgentResult(
            reply="Agent P could not complete the required ERP tool action.",
            events=[PiAgentEvent(required_tool, "fallback_error", f"no fallback for {tool_profile}")],
        )

    def _current_error_fallback(self, user_text: str, required_tool: str) -> PiAgentResult:
        error = self._read_current_error()
        if not error.get("active"):
            return PiAgentResult(
                reply="ERP 画面にアクティブなエラーはありません。",
                events=[PiAgentEvent(required_tool, "fallback", "runtime checked current ERP error and found none")],
            )
        scenario_key = str(error.get("scenario_key", ""))
        state = SCENARIOS[scenario_key] if scenario_key in SCENARIOS else None
        query = str(error.get("error_code") or error.get("system") or "")
        evidence = self._search_knowledge(query, 5) if query else []
        if not evidence and state is not None:
            evidence = self._search_knowledge(str(state["system"]), 5)
        details = {
            "scenario_key": scenario_key,
            **(state or {}),
            "trace_id": str(error.get("trace_id", "")),
            "correlation_id": str(error.get("correlation_id", "")),
            "user_email": str(error.get("user_email", "")),
            "evidence": evidence,
        }
        return PiAgentResult(
            reply=self._format_analysis_reply(details),
            events=[PiAgentEvent(required_tool, "fallback", "runtime read current ERP error and searched KB because Pi did not call the required tool")],
            evidence=evidence,
        )

    def _analyze_pasted_error(self, user_text: str) -> dict[str, Any]:
        scenario_key = self._detect_scenario(user_text)
        state = SCENARIOS[scenario_key]
        trace_match = re.search(r"Trace ID:\s*([^\s]+)", user_text, re.I)
        correlation_match = re.search(r"Correlation ID:\s*([^\s]+)", user_text, re.I)
        evidence = self._search_knowledge(str(state.get("knowledge_query") or state["error_code"]), 8)
        if not any(hit.get("path") for hit in evidence):
            evidence = self._search_knowledge(str(state["system"]), 8)
        return {
            "scenario_key": scenario_key,
            **state,
            "trace_id": trace_match.group(1) if trace_match else "",
            "correlation_id": correlation_match.group(1) if correlation_match else "",
            "pasted_text": user_text,
            "evidence": evidence,
            "ticket_created": False,
        }

    def _create_ticket_from_current_error(self, user_text: str) -> dict[str, Any]:
        error = self._read_current_error()
        current_key = str(error.get("scenario_key", ""))
        scenario_key = current_key if current_key in SCENARIOS else self._detect_scenario(json.dumps(error, ensure_ascii=False) + " " + user_text)
        state = SCENARIOS[scenario_key]
        evidence = self._search_knowledge(str(state.get("knowledge_query") or error.get("error_code") or state["error_code"]), 5)
        if not any(hit.get("path") for hit in evidence):
            evidence = self._search_knowledge(str(error.get("system") or state["system"]), 5)
        title = str(error.get("title") or state["symptom"])
        error_text = str(error.get("error_text") or "")
        summary = (
            f"{title}: {error_text} "
            f"System={error.get('system', state['system'])}; "
            f"Code={error.get('error_code', state['error_code'])}; "
            f"Trace={error.get('trace_id', '')}; "
            f"Requester={error.get('user_email', 'demo.user@demo.local')}"
        ).strip()
        return {
            "ticket_id": self._make_ticket_id(f"{summary}:{state['route']}"),
            "status": "New",
            "requester": error.get("user_email", "demo.user@demo.local"),
            "system": error.get("system", state["system"]),
            "error_code": error.get("error_code", state["error_code"]),
            "category": state["category"],
            "risk": state["risk"],
            "priority": state["priority"],
            "route": state["route"],
            "impact": state["impact"],
            "title": title,
            "trace_id": error.get("trace_id", ""),
            "correlation_id": error.get("correlation_id", ""),
            "summary": summary,
            "evidence": evidence,
            "evidence_summary": "current ERP error and local KB evidence",
            "blocked_actions": state["blocked_actions"],
        }

    def _next_steps_for(self, details: dict[str, Any]) -> str:
        scenario_key = details.get("scenario_key")
        if scenario_key == "VENDOR_MFA_EXCEPTION":
            return "MFA 無効化や条件付きアクセス除外は自動実行できません。サービスプリンシパル、証明書認証、最小権限設計を検討し、Security Team + IAM Approval Board へ承認付きでチケットを作成します。"
        if scenario_key in {"AADSTS50076", "CA_BLOCK"}:
            return "会社支給端末、許可されたネットワーク、MFA 状態を確認してください。解決しない場合は IT 連絡またはチケット作成を依頼してください。"
        if scenario_key == "AADSTS50105":
            return "利用申請、所属グループ、アプリ割当、上長承認の有無を確認してください。必要であれば業務システム権限管理チームへチケットを作成します。"
        if scenario_key == "CRM_MENU_MISSING":
            return "所属チーム、業務ロール、上長承認済みの権限申請番号を確認してください。必要であれば CRM Owner / Dynamics 管理者へチケットを作成します。"
        if scenario_key == "POWERBI_DENIED":
            return "対象レポート名、ワークスペース名、業務上の利用理由、承認者を確認してください。必要であれば BI 管理者 / Data Platform Team へチケットを作成します。"
        if scenario_key == "LICENSE_MISSING":
            return "利用開始申請、対象業務、利用開始日、承認者を確認してください。必要であれば Microsoft 365 ライセンス管理チームへチケットを作成します。"
        if scenario_key == "MULTI_USER_OUTAGE":
            return "影響人数、発生開始時刻、対象機能を確認してください。複数ユーザー影響のため IT Ops / Incident Manager に連絡してください。"
        return "必要情報を確認し、解決しない場合は担当チームへチケットを作成してください。"

    def _format_analysis_reply(self, details: dict[str, Any]) -> str:
        refs = ""
        evidence = details.get("evidence", [])
        first = next((hit for hit in evidence if hit.get("path") and hit.get("line")), None)
        if first:
            refs = f"\n根拠: {first.get('path')}:{first.get('line')}"
        next_steps = self._next_steps_for(details)
        return (
            f"エラーを分析しました。\n"
            f"分類: {details['category']}\n"
            f"対象システム: {details['system']}\n"
            f"エラーコード: {details['error_code']}\n"
            f"Trace ID: {details.get('trace_id', '')}\n"
            f"推奨ルート: {details['route']}\n"
            f"優先度: {details['priority']}\n\n"
            f"{next_steps}"
            f"{refs}"
        )

    def _detect_scenario(self, text: str) -> str:
        lower = text.lower()
        for key in SCENARIOS:
            if key.lower() in lower:
                return key
        if "aadsts50105" in lower:
            return "AADSTS50105"
        if "license" in lower or "ライセンス" in lower:
            return "LICENSE_MISSING"
        if "conditional" in lower or "ca_block" in lower or "条件付き" in lower:
            return "CA_BLOCK"
        if "power bi" in lower or "pbi" in lower:
            return "POWERBI_DENIED"
        if "複数" in lower or "multiple" in lower or "outage" in lower:
            return "MULTI_USER_OUTAGE"
        if "vendor" in lower or "ベンダー" in lower or "mfa を無効" in lower:
            return "VENDOR_MFA_EXCEPTION"
        if "sales hub" in lower or "sales menu" in lower or "menu" in lower or "メニュー" in lower or "営業案件" in lower:
            return "CRM_MENU_MISSING"
        return "AADSTS50076"

    def _read_current_error(self) -> dict[str, Any]:
        try:
            return json.loads(CURRENT_ERROR_PATH.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {"active": False}

    def _search_knowledge(self, query: str, limit: int) -> list[dict[str, Any]]:
        try:
            result = subprocess.run(
                ["rg", "-n", "-i", "--context", "1", query, str(KNOWLEDGE_DIR)],
                cwd=self.app_dir,
                check=False,
                capture_output=True,
                text=True,
                timeout=4,
            )
        except (subprocess.SubprocessError, FileNotFoundError):
            return []
        hits: list[dict[str, Any]] = []
        for line in result.stdout.splitlines():
            if not line or line == "--":
                continue
            match = re.match(r"^(.+?):(\d+)[:-](.*)$", line)
            if match:
                path = str(Path(match.group(1)).resolve().relative_to(self.app_dir))
                hits.append({"path": path, "line": int(match.group(2)), "snippet": match.group(3).strip()})
            else:
                hits.append({"raw": line})
            if len(hits) >= limit:
                break
        return hits

    def _make_ticket_id(self, text: str) -> str:
        value = 0
        for char in text:
            value = (value * 31 + ord(char)) & 0xFFFFFFFF
        return f"KW-{((value % 9000) + 1000):04d}"

    def _system_prompt(self, tool_profile: str, today: str, retry_instruction: str | None = None) -> str:
        retry = f" {retry_instruction}" if retry_instruction else ""
        return (
            "You are Agent P. "
            f"Current local date is {today} in Asia/Tokyo. "
            f"{self._profile_instruction(tool_profile)} "
            "Use Japanese for Japanese input. Do not mention tool names unless reporting completed tool activity."
            f"{retry}"
        )

    def _needs_builtin_tools(self, user_text: str) -> bool:
        normalized = user_text.lower()
        return any(pattern in normalized for pattern in BUILTIN_TOOL_INTENT_PATTERNS)

    def _direct_basic_reply(self, user_text: str) -> str | None:
        text = user_text.strip()
        normalized = text.lower()
        if any(pattern in normalized for pattern in ERP_INTENT_PATTERNS):
            return None
        if text in {"こんにちは", "你好", "您好", "hello", "hi"}:
            return "こんにちは。"
        if any(pattern in text for pattern in ["あなたは誰", "あなたはだ誰", "君は誰", "あなたは何者"]):
            return "私はAgent Pです。社内ERPの操作支援とITサポートを行うローカルAIエージェントです。"
        if any(pattern in text for pattern in ["你是谁", "你在干什么", "你能做什么", "你是什么"]):
            return "我是 Agent P，一个连接本地 LFM 模型和模拟 ERP 工具的企业内部支援 agent。平时可以对话；遇到 ERP、SSO、权限、工单问题时会读取错误日志、检索知识库或创建工单。"
        if "今日は何の日" in text or "今日何日" in text or "何曜日" in text:
            today = datetime.now().strftime("%Y-%m-%d")
            weekday = ["月曜日", "火曜日", "水曜日", "木曜日", "金曜日", "土曜日", "日曜日"][datetime.now().weekday()]
            return f"今日は{today}、{weekday}です。"
        return None

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
