import csv
import io
import json
import uuid
from datetime import date
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.agent import PipelineResult, process_application
from app.models import LlamaServer, get_server

DATA_DIR = Path(__file__).parent.parent / "data"
LEDGER_FILE = DATA_DIR / "ledger_db.json"

app = FastAPI(title="ローカルAI申請受付支援 Demo")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5174", "http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory store + JSON file persistence
_results: dict[str, PipelineResult] = {}


def _load_ledger():
    if LEDGER_FILE.exists():
        with open(LEDGER_FILE) as f:
            data = json.load(f)
        for rid, d in data.items():
            r = PipelineResult()
            r.id = d.get("id", rid)
            r.extracted = d.get("extracted", {})
            r.deficiency = d.get("deficiency", {})
            r.risk = d.get("risk", {})
            r.decision = d.get("decision", {})
            r.ledger = d.get("ledger", {})
            r.is_unclear = d.get("is_unclear", False)
            r.unclear_reason = d.get("unclear_reason", "")
            r.unclear_suggestion = d.get("unclear_suggestion", "")
            _results[rid] = r


def _save_ledger():
    LEDGER_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LEDGER_FILE, "w") as f:
        json.dump(
            {rid: r.to_dict() for rid, r in _results.items()},
            f, ensure_ascii=False, indent=2,
        )


def _flatten(rid: str, r: PipelineResult) -> dict:
    return {
        "id": rid,
        "ledger_id": r.ledger.get("ledger_id", ""),
        "applicant_name": r.extracted.get("applicant_name", ""),
        "applicant_dept": r.extracted.get("applicant_dept", ""),
        "application_type": r.extracted.get("application_type", ""),
        "application_date": r.extracted.get("application_date", ""),
        "application_summary": r.extracted.get("application_summary", ""),
        "estimated_cost": r.extracted.get("estimated_cost", ""),
        "priority_level": r.extracted.get("priority_level", ""),
        "risk_level": r.risk.get("risk_level", ""),
        "decision": r.decision.get("decision", ""),
        "status": r.ledger.get("status", ""),
        "confidence_score": r.ledger.get("confidence_score", 0),
        "entry_date": r.ledger.get("entry_date", ""),
        "is_unclear": r.is_unclear,
        "unclear_reason": r.unclear_reason,
    }


_load_ledger()


class ProcessRequest(BaseModel):
    application_text: str


class ConfirmRequest(BaseModel):
    result_id: str
    modifications: dict | None = None


class LedgerWriteRequest(BaseModel):
    applicant_name: str = ""
    applicant_dept: str = ""
    application_type: str = ""
    application_date: str = ""
    application_summary: str = ""
    estimated_cost: str = ""
    priority_level: str = ""
    risk_level: str = ""
    decision: str = ""
    status: str = "審査中"


@app.post("/api/process")
async def api_process(req: ProcessRequest):
    server = get_server()
    if not server.is_ready():
        try:
            server.start()
        except Exception as e:
            raise HTTPException(500, f"llama-server 起動失敗: {e}")

    result = await process_application(req.application_text)
    _results[result.id] = result
    _save_ledger()
    return result.to_dict()


@app.post("/api/confirm")
async def api_confirm(req: ConfirmRequest):
    result = _results.get(req.result_id)
    if not result:
        raise HTTPException(404, "結果が見つかりません")

    if req.modifications:
        for key, value in req.modifications.items():
            for section in ("extracted", "deficiency", "risk", "decision", "ledger"):
                if key in getattr(result, section):
                    getattr(result, section)[key] = value
                    break

    result.ledger["status"] = "受付済"
    _save_ledger()
    return result.to_dict()


@app.get("/api/export/{result_id}")
async def api_export(result_id: str, format: str = "json"):
    result = _results.get(result_id)
    if not result:
        raise HTTPException(404, "結果が見つかりません")

    if format == "csv":
        output = io.StringIO()
        writer = csv.DictWriter(
            output,
            fieldnames=["ledger_id", "entry_date", "status", "applicant_name", "application_type", "application_summary", "estimated_cost", "decision", "reason"],
        )
        flat = {
            "ledger_id": result.ledger.get("ledger_id", ""),
            "entry_date": result.ledger.get("entry_date", ""),
            "status": result.ledger.get("status", ""),
            "applicant_name": result.extracted.get("applicant_name", ""),
            "application_type": result.extracted.get("application_type", ""),
            "application_summary": result.extracted.get("application_summary", ""),
            "estimated_cost": result.extracted.get("estimated_cost", ""),
            "decision": result.decision.get("decision", ""),
            "reason": result.decision.get("reason", ""),
        }
        writer.writeheader()
        writer.writerow(flat)
        return JSONResponse({"csv": output.getvalue()})

    return result.to_dict()


@app.get("/api/sample")
async def api_sample():
    samples_file = DATA_DIR / "sample_applications.jsonl"
    if not samples_file.exists():
        raise HTTPException(404, "サンプルデータが見つかりません")

    samples = []
    with open(samples_file) as f:
        for line in f:
            line = line.strip()
            if line:
                samples.append(json.loads(line))
    return {"samples": samples}


@app.get("/api/status")
async def api_status():
    server = get_server()
    return {
        "llama_server_ready": server.is_ready(),
        "model": server.model_name,
    }


# ─── Ledger CRUD ────────────────────────────────────────────

@app.get("/api/ledger")
async def api_list_ledger():
    entries = [_flatten(rid, r) for rid, r in _results.items()]
    entries.sort(key=lambda e: e.get("entry_date") or "", reverse=True)
    return {"entries": entries}


@app.get("/api/ledger/{result_id}")
async def api_get_ledger(result_id: str):
    r = _results.get(result_id)
    if not r:
        raise HTTPException(404, "結果が見つかりません")
    return _flatten(result_id, r)


@app.post("/api/ledger")
async def api_create_ledger(req: LedgerWriteRequest):
    pid = str(uuid.uuid4())[:8]
    today = date.today().isoformat()
    entry = PipelineResult()
    entry.id = pid
    entry.extracted = {
        "applicant_name": req.applicant_name,
        "applicant_dept": req.applicant_dept,
        "application_type": req.application_type,
        "application_date": req.application_date,
        "application_summary": req.application_summary,
        "estimated_cost": req.estimated_cost,
        "priority_level": req.priority_level,
    }
    entry.decision = {"decision": req.decision or "受付"}
    entry.risk = {"risk_level": req.risk_level or "低"}
    entry.ledger = {
        "ledger_id": f"LDG-{today.replace('-', '')}-{pid}",
        "entry_date": today,
        "status": req.status,
        "confidence_score": 0,
    }
    _results[pid] = entry
    _save_ledger()
    return _flatten(pid, entry)


@app.put("/api/ledger/{result_id}")
async def api_update_ledger(result_id: str, req: LedgerWriteRequest):
    r = _results.get(result_id)
    if not r:
        raise HTTPException(404, "結果が見つかりません")

    updates = {
        "extracted": {
            "applicant_name": req.applicant_name,
            "applicant_dept": req.applicant_dept,
            "application_type": req.application_type,
            "application_date": req.application_date,
            "application_summary": req.application_summary,
            "estimated_cost": req.estimated_cost,
            "priority_level": req.priority_level,
        },
        "decision": {"decision": req.decision},
        "risk": {"risk_level": req.risk_level},
        "ledger": {"status": req.status},
    }
    for section, fields in updates.items():
        for k, v in fields.items():
            if v:
                getattr(r, section)[k] = v

    _save_ledger()
    return _flatten(result_id, r)


@app.delete("/api/ledger/{result_id}")
async def api_delete_ledger(result_id: str):
    if result_id not in _results:
        raise HTTPException(404, "結果が見つかりません")
    del _results[result_id]
    _save_ledger()
    return {"deleted": result_id}