import json
import re
import uuid
from datetime import date

from app.models import LlamaServer, get_server
from app.tools import get_tools_for_step, parse_tool_call

SYSTEM_PROMPT = """あなたは社内申請受付支援AIです。必ず提供されたツールを呼び出して構造化データを返してください。自由テキストで回答しないでください。

重要: 必ずツールを呼び出してください。ツール以外の形式で回答しないでください。"""


class PipelineResult:
    def __init__(self):
        self.id = str(uuid.uuid4())[:8]
        self.extracted: dict = {}
        self.deficiency: dict = {}
        self.risk: dict = {}
        self.decision: dict = {}
        self.ledger: dict = {}
        self.is_unclear: bool = False
        self.unclear_reason: str = ""
        self.unclear_suggestion: str = ""

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "extracted": self.extracted,
            "deficiency": self.deficiency,
            "risk": self.risk,
            "decision": self.decision,
            "ledger": self.ledger,
            "is_unclear": self.is_unclear,
            "unclear_reason": self.unclear_reason,
            "unclear_suggestion": self.unclear_suggestion,
        }


async def _extract_fields(
    server: LlamaServer, application_text: str
) -> dict:
    tools = get_tools_for_step("extract")
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"以下の申請内容からフィールドを抽出してください:\n\n{application_text}"},
    ]
    response = await server.chat_completion(
        messages=messages, tools=tools, max_tokens=600
    )
    parsed = parse_tool_call(response)
    if parsed is None:
        choices = response.get("choices", [])
        if choices:
            content = choices[0].get("message", {}).get("content", "")
            return _regex_extract(application_text, content)
    if parsed and parsed.get("tool_name") == "intent_unclear":
        return {
            "_unclear": True,
            "reason": parsed.get("args", {}).get("reason", ""),
            "suggestion": parsed.get("args", {}).get("suggestion", ""),
        }
    if parsed:
        result = parsed["args"]
        # Fill gaps from regex if model missed fields
        fallback = _regex_extract(application_text, "")
        for key in ("applicant_name", "applicant_dept", "application_type",
                    "application_date", "application_summary", "estimated_cost",
                    "priority_level", "related_systems"):
            if not result.get(key) and fallback.get(key):
                result[key] = fallback[key]
        return result
    return {}


def _regex_extract(application_text: str, raw_model_output: str = "") -> dict:
    """Extract fields from text using regex when model fails to call tool."""
    text = application_text
    combined = f"{text}\n{raw_model_output}"

    def _find(pattern: str, source: str) -> str:
        m = re.search(pattern, source)
        return m.group(1).strip() if m else ""

    # ── Applicant name ──
    name = _find(r"申請者[：:]\s*([^\n（(（）\s]+)", combined)
    if not name:
        name = _find(r"申請者名[：:]\s*([^\n,，\s]+)", combined)

    # ── Department ──
    dept = ""
    m = re.search(r"申請者[：:]\s*[^\n（(（）]+[（(]([^)）]+)[)）]", combined)
    if m:
        dept = m.group(1).strip()
    if not dept:
        dept = _find(r"所属部署[：:]\s*([^\n,，\s]+)", combined)

    # ── Application type ──
    type_patterns = [
        (r"設備変更", "設備変更"), (r"人事異動", "人事異動"),
        (r"予算申請", "予算申請"), (r"契約更新", "契約更新"),
    ]
    app_type = ""
    for pat, label in type_patterns:
        if re.search(pat, combined):
            app_type = label
            break
    if not app_type:
        app_type = _find(r"申請種別[：:]\s*([^\n,，\s]+)", combined)
    if not app_type:
        app_type = _find(r"種別[：:]\s*([^\n,，\s]+)", combined)

    # ── Date ──
    date_val = ""
    m = re.search(r"(\d{4})[年/\-](\d{1,2})[月/\-](\d{1,2})", combined)
    if m:
        date_val = f"{m.group(1)}-{m.group(2).zfill(2)}-{m.group(3).zfill(2)}"
    if not date_val:
        date_val = _find(r"日付[：:]\s*(\S+)", combined)

    # ── Summary ──
    summary_lines = []
    for line in text.split("\n"):
        line = line.strip()
        if line and not re.match(r"(申請者|日付|種別|添付|※)", line) and len(line) > 10:
            summary_lines.append(line)
    summary = summary_lines[0] if summary_lines else text[:100].strip()

    # ── Cost ──
    cost = _find(r"費用[：:]\s*([^\n]+)", combined)
    if not cost:
        cost = _find(r"金額[：:]\s*([^\n]+)", combined)
    if not cost:
        m = re.search(r"(\d{1,3}(?:,\d{3})*万円?|\d+(?:\.\d+)?億円)", combined)
        if m:
            cost = m.group(1)

    # ── Priority ──
    priority = "中"
    for pat, label in [(r"緊急|至急|急ぎ", "高"), (r"同一条件|定期|更新", "低")]:
        if re.search(pat, combined):
            priority = label
            break

    # ── Related systems ──
    systems = []
    m = re.search(r"対象システム[：:]\s*([^\n]+)", combined)
    if m:
        systems = [s.strip() for s in re.split(r"[、，,、]", m.group(1)) if s.strip()]
    if not systems:
        m = re.search(r"関連システム[：:]\s*([^\n]+)", combined)
        if m:
            systems = [s.strip() for s in re.split(r"[、，,、]", m.group(1)) if s.strip()]

    return {
        "applicant_name": name,
        "applicant_dept": dept,
        "application_type": app_type,
        "application_date": date_val,
        "application_summary": summary,
        "related_systems": systems,
        "priority_level": priority,
        "estimated_cost": cost,
    }


def _extract_cost_yen(cost_str: str) -> int:
    """Extract estimated cost in yen from a string like '350万円', '1,500万円', '50万円'."""
    if not cost_str:
        return 0
    s = cost_str.replace(",", "")
    if "億" in s:
        m = re.search(r"(\d+(?:\.\d+)?)", s)
        return int(float(m.group(1)) * 100000000) if m else 0
    if "万" in s:
        m = re.search(r"(\d+(?:\.\d+)?)", s)
        return int(float(m.group(1)) * 10000) if m else 0
    m = re.search(r"(\d+)", s)
    return int(m.group(1)) if m else 0


def _check_deficiency(application_text: str, extracted: dict) -> dict:
    """Deterministic deficiency check based on keywords and field completeness."""
    text = application_text
    deficiency_fields = []
    deficiency_issues = []
    deficiency_severities = []
    missing_documents = []

    # ── Check for explicit missing markers in text ──
    missing_patterns = [
        ("未提出", "業務引き継ぎ計画等の未提出書類", "警告"),
        ("未確定", "契約書等が未確定", "警告"),
        ("未完了", "必要手続きが未完了", "注意"),
        ("不足", "必要書類が不足", "注意"),
    ]
    for pattern, issue_desc, severity in missing_patterns:
        if pattern in text:
            deficiency_fields.append(pattern)
            deficiency_issues.append(issue_desc)
            deficiency_severities.append(severity)

    # ── Check for ※ markers ──
    if "※" in text:
        after_star = text[text.index("※"):]
        if any(kw in after_star for kw in ["未", "不明", "不足"]):
            deficiency_fields.append("注記事項")
            deficiency_issues.append("申請書内に不備の注記あり")
            deficiency_severities.append("警告")

    # ── Detect missing documents by checking keywords ──
    doc_keywords = {
        "契約書": ["契約書", "契約書案"],
        "仕様書": ["仕様書", "機器仕様書"],
        "計画書": ["計画書", "移行計画書", "引き継ぎ計画"],
        "実績報告": ["実績報告書", "前年度実績"],
        "ROI分析": ["ROI", "投資効果分析", "費用対効果"],
    }
    for doc_name, kws in doc_keywords.items():
        has_doc = any(kw in text for kw in kws)
        has_missing = any(kw in text for kw in ["未提出", "未確定", "未添付", "不足"] + [f"※{kw}" for kw in kws])
        if has_missing and has_doc:
            missing_documents.append(doc_name)
        elif doc_name == "ROI分析" and any(kw in text for kw in ["ROI未提出", "ROI分析未提出"]):
            missing_documents.append(doc_name)
        elif doc_name == "契約書" and "未確定" in text:
            missing_documents.append(doc_name)

    if "引き継ぎ計画" in text and "未提出" in text:
        if "引き継ぎ計画" not in missing_documents:
            missing_documents.append("引き継ぎ計画")

    # ── Field completeness ──
    important_fields = ["applicant_name", "application_type", "application_date", "application_summary"]
    for field in important_fields:
        val = str(extracted.get(field, "")).strip()
        if not val or val in ("不明", "その他", "?") or field not in extracted:
            deficiency_fields.append(field)
            deficiency_issues.append(f"{field}が未記載または不明")
            deficiency_severities.append("注意")

    # ── Completeness score ──
    base_fields = ["applicant_name", "applicant_dept", "application_type",
                    "application_date", "application_summary", "estimated_cost"]
    filled = sum(1 for f in base_fields if extracted.get(f) and str(extracted[f]).strip() not in ("", "不明", "?"))
    completeness_score = min(100, int(filled / len(base_fields) * 100))
    if missing_documents:
        completeness_score = max(20, completeness_score - 15 * len(missing_documents))
    if deficiency_issues:
        completeness_score = max(20, completeness_score - 10)

    deficiency_found = bool(deficiency_fields or missing_documents or deficiency_issues)
    if isinstance(extracted.get("deficiency_found"), str):
        pass

    return {
        "deficiency_found": deficiency_found,
        "deficiency_fields": deficiency_fields,
        "deficiency_issues": deficiency_issues,
        "deficiency_severities": deficiency_severities,
        "missing_documents": missing_documents,
        "completeness_score": completeness_score,
    }


def _assess_risk(application_text: str, extracted: dict, deficiency: dict) -> dict:
    """Deterministic risk assessment using scoring system (0-9)."""
    risk_categories = []
    risk_descriptions = []
    risk_scores = []
    total_score = 0

    # ── Cost risk (0-3) ──
    cost_yen = _extract_cost_yen(str(extracted.get("estimated_cost", "")))
    if cost_yen >= 10000000:
        score = 3
        risk_categories.append("財務")
        risk_descriptions.append(f"高額申請（{_format_cost(cost_yen)}）")
        risk_scores.append(3)
    elif cost_yen >= 3000000:
        score = 2
        risk_categories.append("財務")
        risk_descriptions.append(f"中額申請（{_format_cost(cost_yen)}）")
        risk_scores.append(2)
    elif cost_yen >= 1000000:
        score = 1
        risk_categories.append("財務")
        risk_descriptions.append(f"低額申請（{_format_cost(cost_yen)}）")
        risk_scores.append(1)
    else:
        score = 0
    total_score += score

    # ── Deficiency risk (0-2) ──
    if deficiency.get("deficiency_found"):
        score = min(len(deficiency.get("deficiency_issues", [])) + len(deficiency.get("missing_documents", [])), 2)
        if score > 0:
            risk_categories.append("コンプライアンス")
            risk_descriptions.append("不備項目あり")
            risk_scores.append(score)
        total_score += score

    # ── Type risk (0-2) ──
    app_type = str(extracted.get("application_type", ""))
    type_risk_map = {"予算申請": 2, "設備変更": 1, "人事異動": 1, "契約更新": 0, "その他": 1}
    score = type_risk_map.get(app_type, 1)
    if score > 0:
        risk_categories.append("業務影響")
        type_name = app_type if app_type else "不明"
        risk_descriptions.append(f"{type_name}に伴う業務影響リスク")
        risk_scores.append(score)
    total_score += score

    # ── Clarity risk (0-2) ──
    meaningful_kw = ["申請", "依頼", "変更", "異動", "更新", "契約", "予算", "設備", "人事"]
    text_lower = application_text.lower()
    has_meaningful = any(kw in text_lower for kw in meaningful_kw)
    applicant_real = bool(extracted.get("applicant_name") and str(extracted["applicant_name"]) not in ("不明", "前申請者", ""))
    if not has_meaningful or not applicant_real:
        score = 2
        risk_categories.append("セキュリティ")
        risk_descriptions.append("申請内容が不明確")
        risk_scores.append(2)
    elif len(application_text.strip()) < 50:
        score = 1
        risk_categories.append("セキュリティ")
        risk_descriptions.append("申請内容が簡略")
        risk_scores.append(1)
    else:
        score = 0
    total_score += score

    # ── Map total to risk level ──
    if total_score >= 6:
        risk_level = "高"
    elif total_score >= 3:
        risk_level = "中"
    else:
        risk_level = "低"

    requires_manual_review = total_score >= 3 or bool(deficiency.get("deficiency_found"))

    approval_chain = []
    if cost_yen >= 10000000:
        approval_chain.append("経営層")
    if risk_level == "高":
        approval_chain.append("管理部門")
    if not approval_chain and requires_manual_review:
        approval_chain.append("担当部署長")

    return {
        "risk_level": risk_level,
        "risk_categories": risk_categories,
        "risk_descriptions": risk_descriptions,
        "risk_scores": risk_scores,
        "requires_manual_review": requires_manual_review,
        "approval_chain": approval_chain,
    }


def _format_cost(yen: int) -> str:
    if yen >= 100000000:
        return f"{yen // 100000000}億円"
    if yen >= 10000:
        return f"{yen // 10000}万円"
    return f"{yen}円"


def _make_decision(extracted: dict, deficiency: dict, risk: dict) -> dict:
    """Deterministic decision based on risk score and deficiency."""
    risk_level = risk.get("risk_level", "中")
    has_deficiency = bool(deficiency.get("deficiency_found"))
    missing_docs = deficiency.get("missing_documents", [])

    if risk_level == "高":
        decision = "差戻"
        reason = "高リスク申請のため、差戻とします。"
        conditions = ["リスク評価結果の再確認", "管理部門の承認"]
        next_action = "差戻通知"
    elif has_deficiency:
        decision = "要確認"
        reason = "不備ありのため、確認後に受付可否を判定します。"
        conditions = missing_docs if missing_docs else ["不備事項の確認・修正"]
        next_action = "保留"
    elif risk_level == "中":
        decision = "受付"
        reason = "中リスクですが不備なしのため受付します。"
        conditions = ["審査員による最終確認"]
        next_action = "台帳登録"
    else:
        decision = "受付"
        reason = "低リスク・不備なしのため受付します。"
        conditions = []
        next_action = "台帳登録"

    dept_map = {
        "設備変更": "情報システム部",
        "人事異動": "人事部",
        "予算申請": "財務部",
        "契約更新": "法務部",
    }
    assign_to = dept_map.get(str(extracted.get("application_type", "")), "担当部署")

    return {
        "decision": decision,
        "reason": reason,
        "conditions": conditions,
        "next_action": next_action,
        "assign_to": assign_to,
    }


def _generate_ledger(result_id: str, extracted: dict, deficiency: dict,
                     risk: dict, decision: dict) -> dict:
    """Generate ledger entry from all collected data."""
    today = date.today().isoformat()

    confidence = 80
    if bool(deficiency.get("deficiency_found")):
        confidence -= 20
    if risk.get("risk_level") in ("高",):
        confidence -= 20
    if any(k.startswith("_raw_text") for k in extracted.keys()):
        confidence -= 15

    return {
        "ledger_id": f"LDG-{today.replace('-', '')}-{result_id}",
        "entry_date": today,
        "status": "差戻" if decision.get("decision") == "差戻" else "審査中",
        "fields": {
            "applicant_name": extracted.get("applicant_name", ""),
            "applicant_dept": extracted.get("applicant_dept", ""),
            "application_type": extracted.get("application_type", ""),
            "application_date": extracted.get("application_date", ""),
            "application_summary": extracted.get("application_summary", ""),
            "estimated_cost": extracted.get("estimated_cost", ""),
        },
        "audit_log": f"AI抽出→不備チェック(deficiency={deficiency.get('deficiency_found')})→リスク評価(level={risk.get('risk_level')})→判定({decision.get('decision')})",
        "confidence_score": max(confidence, 20),
    }


async def process_application(application_text: str) -> PipelineResult:
    server = get_server()
    result = PipelineResult()

    # ── Step 1: Extract fields (model) ──
    extracted = await _extract_fields(server, application_text)

    if "_unclear" in extracted:
        result.is_unclear = True
        result.unclear_reason = extracted.get("reason", "")
        result.unclear_suggestion = extracted.get("suggestion", "")
        return result

    # Check for raw_text fallback — try to extract what we can
    if "_raw_text" in extracted:
        raw = extracted.pop("_raw_text")
        for key in ["applicant_name", "applicant_dept", "application_type",
                     "application_date", "estimated_cost"]:
            if key not in extracted:
                extracted[key] = ""

    # Check if input is too vague
    meaningful_kw = ["申請", "依頼", "申込", "変更", "異動", "更新", "契約", "予算", "設備", "人事"]
    applicant_real = bool(
        extracted.get("applicant_name") and str(extracted["applicant_name"]) not in ("不明", "前申請者", "")
        and extracted.get("application_type") and str(extracted["application_type"]) not in ("", "その他")
    )
    has_meaningful = any(kw in application_text for kw in meaningful_kw)

    if not has_meaningful and not applicant_real:
        result.is_unclear = True
        result.unclear_reason = "申請内容が不足または不明確です。具体的な申請者名、種別、内容を記載してください。"
        result.unclear_suggestion = "申請書のひな形に沿って、申請者・種別・目的・期間・金額を明記して再提出してください。"
        return result

    result.extracted = extracted

    # ── Step 2: Deficiency check (program) ──
    result.deficiency = _check_deficiency(application_text, extracted)

    # ── Step 3: Risk assessment (program) ──
    result.risk = _assess_risk(application_text, extracted, result.deficiency)

    # ── Step 4: Decision (program) ──
    result.decision = _make_decision(extracted, result.deficiency, result.risk)

    # ── Step 5: Ledger generation (program) ──
    result.ledger = _generate_ledger(
        result.id, extracted, result.deficiency, result.risk, result.decision
    )

    return result