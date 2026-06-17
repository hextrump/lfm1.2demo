from __future__ import annotations

import json
import os
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
PI_PROVIDER = "local-lfm"
PI_MODEL = "lfm2-1.2b-tool-q4_k_m.gguf"
PI_TIMEOUT_SECONDS = 90
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
            return parsed
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
                return retry
            last = retry
        last.events.insert(
            0,
            PiAgentEvent("pi_agent", "error", f"required tool was not called: {required_tool}; local model returned text only"),
        )
        return last

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

    def _system_prompt(self, tool_profile: str, today: str, retry_instruction: str | None = None) -> str:
        retry = f" {retry_instruction}" if retry_instruction else ""
        return (
            "You are Agent P, an internal ERP / CRM / SSO support assistant. "
            "You help employees troubleshoot sign-in failures, permission and license requests, "
            "Power BI access, and route unresolved issues to IT as tickets. "
            f"Current local date is {today} in Asia/Tokyo. "
            f"{self._profile_instruction(tool_profile)} "
            "LANGUAGE: reply in the same language the user wrote in. "
            "Japanese input -> Japanese. Chinese input -> Chinese. English input -> English. "
            "Do not default to Japanese unless the user wrote in Japanese. "
            "Do not mention tool names unless reporting completed tool activity. "
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
            "你是谁", "你叫什么", "你是什么", "你是啥", "介绍下自己", "自我介绍一下", "介绍一下你自己",
            "who are you", "what are you", "what's your name", "introduce yourself",
            "お前は誰", "あなたは誰", "誰ですか", "自己紹介",
        )
        if any(p in lower for p in identity_patterns):
            return self._identity_reply(text)

        # Capability questions — short, scannable list, no model call.
        capability_patterns = (
            "你能做什么", "你能干啥", "你会什么", "可以做什么", "你有什么功能",
            "what can you do", "what can you help", "what do you do", "your capabilities",
            "何ができますか", "何ができる", "何を手伝える",
        )
        if any(p in lower for p in capability_patterns):
            return self._capability_reply(text)

        # Date / day-of-week — answer deterministically from the system clock.
        date_patterns = (
            "今天几号", "今天日期", "今天星期", "今天周几", "周几", "星期几",
            "what date", "what day", "today's date", "what is today",
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
