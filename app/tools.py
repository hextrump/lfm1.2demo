TOOL_SCHEMAS = {
    "extract_application_fields": {
        "type": "function",
        "function": {
            "name": "extract_application_fields",
            "description": "申請書から構造化フィールドを抽出する。自由テキストから申請者名、申請種別、申請日、申請内容、関連部署などを抽出する。",
            "parameters": {
                "type": "object",
                "properties": {
                    "applicant_name": {
                        "type": "string",
                        "description": "申請者氏名",
                    },
                    "applicant_dept": {
                        "type": "string",
                        "description": "申請者所属部署",
                    },
                    "application_type": {
                        "type": "string",
                        "description": "申請種別 (設備変更/人事異動/予算申請/契約更新/その他)",
                    },
                    "application_date": {
                        "type": "string",
                        "description": "申請日 (YYYY-MM-DD形式)",
                    },
                    "application_summary": {
                        "type": "string",
                        "description": "申請内容の要約",
                    },
                    "related_systems": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "関連システム名のリスト",
                    },
                    "priority_level": {
                        "type": "string",
                        "description": "緊急度 (高/中/低)",
                    },
                    "estimated_cost": {
                        "type": "string",
                        "description": "推定費用 (金額または'不明')",
                    },
                },
            },
        },
    },
    "check_deficiency": {
        "type": "function",
        "function": {
            "name": "check_deficiency",
            "description": "申請内容に不備（欠落、矛盾、不正確）があるかチェックする。",
            "parameters": {
                "type": "object",
                "properties": {
                    "deficiency_found": {
                        "type": "boolean",
                        "description": "不備が見つかったかどうか",
                    },
                    "deficiency_fields": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "不備のある項目名のリスト",
                    },
                    "deficiency_issues": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "各不備項目の問題内容のリスト（deficiency_fieldsと同じ順序）",
                    },
                    "deficiency_severities": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "各不備項目の重要度リスト (致命/警告/注意)（deficiency_fieldsと同じ順序）",
                    },
                    "missing_documents": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "不足している添付書類のリスト",
                    },
                    "completeness_score": {
                        "type": "integer",
                        "description": "申請完全性スコア (0-100)",
                    },
                },
            },
        },
    },
    "assess_risk": {
        "type": "function",
        "function": {
            "name": "assess_risk",
            "description": "申請のリスクレベルを評価する。業務影響、コンプライアンス、セキュリティ、金額等を考慮して判定する。",
            "parameters": {
                "type": "object",
                "properties": {
                    "risk_level": {
                        "type": "string",
                        "description": "リスクレベル (低/中/高/致命)",
                    },
                    "risk_categories": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "リスクカテゴリのリスト (業務影響/コンプライアンス/セキュリティ/財務)",
                    },
                    "risk_descriptions": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "各リスク内容の説明リスト（risk_categoriesと同じ順序）",
                    },
                    "risk_scores": {
                        "type": "array",
                        "items": {"type": "integer"},
                        "description": "各リスクスコア (1-5) のリスト（risk_categoriesと同じ順序）",
                    },
                    "requires_manual_review": {
                        "type": "boolean",
                        "description": "人工審査が必要かどうか",
                    },
                    "approval_chain": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "推奨承認フロー（承認者部署のリスト）",
                    },
                },
            },
        },
    },
    "suggest_decision": {
        "type": "function",
        "function": {
            "name": "suggest_decision",
            "description": "申請の受付可否を判定し、受付または差戻の提案を行う。",
            "parameters": {
                "type": "object",
                "properties": {
                    "decision": {
                        "type": "string",
                        "description": "判定結果 (受付/差戻/要確認)",
                    },
                    "reason": {
                        "type": "string",
                        "description": "判定理由",
                    },
                    "conditions": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "受付条件（差戻の場合は改善事項）",
                    },
                    "next_action": {
                        "type": "string",
                        "description": "次のアクション (台帳登録/差戻通知/保留)",
                    },
                    "assign_to": {
                        "type": "string",
                        "description": "担当部署",
                    },
                },
            },
        },
    },
    "generate_ledger_entry": {
        "type": "function",
        "function": {
            "name": "generate_ledger_entry",
            "description": "台帳記載用のJSONデータを生成する。抽出フィールドと判定結果を台帳形式に変換する。",
            "parameters": {
                "type": "object",
                "properties": {
                    "ledger_id": {
                        "type": "string",
                        "description": "台帳ID (LDG-YYYYMMDD-XXXX形式で自動生成)",
                    },
                    "entry_date": {
                        "type": "string",
                        "description": "記載日 (YYYY-MM-DD形式)",
                    },
                    "status": {
                        "type": "string",
                        "description": "台帳ステータス (受付済/差戻/審査中)",
                    },
                    "fields": {
                        "type": "object",
                        "description": "台帳フィールド値（申請者/種別/内容/金額等の辞書）",
                    },
                    "audit_log": {
                        "type": "string",
                        "description": "処理履歴 (AI抽出→不備チェック→リスク評価→判定)",
                    },
                    "confidence_score": {
                        "type": "integer",
                        "description": "AI処理信頼度スコア (0-100)",
                    },
                },
            },
        },
    },
    "intent_unclear": {
        "type": "function",
        "function": {
            "name": "intent_unclear",
            "description": "申請内容が不明確、不完全、または処理不可能な場合に呼び出す。",
            "parameters": {
                "type": "object",
                "properties": {
                    "reason": {
                        "type": "string",
                        "description": "不明確な理由 (入力不足/内容矛盾/申請種別不明/言語不明)",
                    },
                    "suggestion": {
                        "type": "string",
                        "description": "改善提案",
                    },
                },
            },
        },
    },
}

# Pipeline step → available tools mapping
STEP_TOOLS = {
    "extract": ["extract_application_fields", "intent_unclear"],
    "deficiency": ["check_deficiency", "intent_unclear"],
    "risk": ["assess_risk", "intent_unclear"],
    "decision": ["suggest_decision", "intent_unclear"],
    "ledger": ["generate_ledger_entry", "intent_unclear"],
}


def get_tools_for_step(step: str) -> list[dict]:
    tool_names = STEP_TOOLS.get(step, [])
    return [TOOL_SCHEMAS[name] for name in tool_names]


def _repair_json_args(s: str) -> dict:
    """Try to extract key-value pairs from a truncated/malformed JSON string."""
    args = {}
    # Try to find completed key-value pairs
    for m in re.finditer(r'"(\w+)"\s*:\s*"((?:[^"\\]|\\.)*)"', s):
        args[m.group(1)] = m.group(2).replace('\\"', '"')
    for m in re.finditer(r'"(\w+)"\s*:\s*(\d+)', s):
        if m.group(1) not in args:
            args[m.group(1)] = int(m.group(2))
    for m in re.finditer(r'"(\w+)"\s*:\s*(true|false)', s, re.IGNORECASE):
        if m.group(1) not in args:
            args[m.group(1)] = m.group(2).lower() == "true"
    for m in re.finditer(r'"(\w+)"\s*:\s*(\[[^\]]*\])', s):
        if m.group(1) not in args:
            try:
                args[m.group(1)] = json.loads(m.group(2))
            except json.JSONDecodeError:
                args[m.group(1)] = m.group(2)
    return args


def parse_tool_call(response: dict) -> dict | None:
    """Parse a tool call from llama-server OpenAI-compatible response."""
    choices = response.get("choices", [])
    if not choices:
        return None

    message = choices[0].get("message", {})
    tool_calls = message.get("tool_calls", [])

    if tool_calls:
        tc = tool_calls[0]
        raw_args = tc["function"]["arguments"]
        if isinstance(raw_args, dict):
            args = raw_args
        else:
            try:
                args = json.loads(raw_args)
            except (json.JSONDecodeError, TypeError):
                args = _repair_json_args(raw_args)
        return {
            "tool_name": tc["function"]["name"],
            "args": args,
        }

    # Fallback: check for content with tool call pattern (LFM2 special tokens)
    content = message.get("content", "")
    if content and "<|tool_call_start|>" in content:
        return _parse_special_token_call(content)

    return None


import json
import re


def _parse_special_token_call(content: str) -> dict | None:
    """Parse LFM2 tool call from <|tool_call_start|>...<|tool_call_end|> pattern."""
    match = re.search(
        r"<\|tool_call_start\|>(.*?)<\|tool_call_end\|>", content, re.DOTALL
    )
    if not match:
        return None

    call_text = match.group(1).strip()
    # Pattern: function_name(param1="value1", param2="value2")
    func_match = re.match(r"(\w+)\((.*)\)", call_text)
    if not func_match:
        return None

    tool_name = func_match.group(1)
    args_text = func_match.group(2)

    # Parse Pythonic kwargs
    args = {}
    for arg_match in re.finditer(
        r'(\w+)\s*=\s*"([^"]*)"', args_text
    ):
        args[arg_match.group(1)] = arg_match.group(2)
    for arg_match in re.finditer(
        r'(\w+)\s*=\s*(\[[^\]]*\])', args_text
    ):
        key = arg_match.group(1)
        val = arg_match.group(2)
        try:
            args[key] = json.loads(val)
        except json.JSONDecodeError:
            args[key] = val
    for arg_match in re.finditer(
        r'(\w+)\s*=\s*(true|false)', args_text, re.IGNORECASE
    ):
        args[arg_match.group(1)] = arg_match.group(2).lower() == "true"
    for arg_match in re.finditer(
        r'(\w+)\s*=\s*(\d+)', args_text
    ):
        args[arg_match.group(1)] = int(arg_match.group(2))

    return {"tool_name": tool_name, "args": args}