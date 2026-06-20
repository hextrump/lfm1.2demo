"""Shared parser for pi-coding-agent session JSONL files.

Each session file is a sequence of JSON lines with the following shape:
  {"type":"session", "id":..., "timestamp":...}
  {"type":"model_change", "id":..., "parentId":..., "provider":..., "modelId":...}
  {"type":"thinking_level_change", "id":..., "parentId":...}
  {"type":"message", "id":..., "parentId":..., "message":{...}}

Messages have `message.role` ∈ {"user", "assistant", "toolResult"} and
`message.content` is an array of typed parts:
  - {"type":"text", "text":"..."}              # user, assistant text reply, toolResult text
  - {"type":"toolCall", "id":"...", "name":"...", "arguments":{...}}   # assistant only

This module reconstructs a session as a chronological list of turns:

  Turn(kind="user",        text="...")
  Turn(kind="tool_call",   tool_name=..., arguments=..., tool_call_id=...)
  Turn(kind="tool_result", tool_name=..., text=..., tool_call_id=..., is_error=...)
  Turn(kind="assistant_text", text="...")

…and exposes helpers to render those turns into:
  - ChatML messages arrays (for SFT and eval rows)
  - DPO prompt/chosen/rejected pairs (for the build_agent_training_data script)
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


@dataclass
class Turn:
    kind: str  # "user" | "tool_call" | "tool_result" | "assistant_text"
    text: str = ""
    tool_name: str = ""
    arguments: dict[str, Any] | None = None
    tool_call_id: str = ""
    is_error: bool = False


def _safe_json(line: str) -> dict[str, Any] | None:
    try:
        return json.loads(line)
    except json.JSONDecodeError:
        return None


def _text_of(parts: list[dict[str, Any]]) -> str:
    out = []
    for p in parts:
        if isinstance(p, dict) and p.get("type") == "text" and isinstance(p.get("text"), str):
            out.append(p["text"])
    return "\n".join(out)


def parse_session(path: Path) -> list[Turn]:
    """Read one session JSONL and return its turns in chronological order.

    Skips the session/model_change/thinking_level_change headers and starts
    from the first user or tool message. Linear parentId chains are the norm;
    if a session has a branch we follow the first one we see at each depth.
    """
    events: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        ev = _safe_json(line)
        if ev is not None:
            events.append(ev)

    if not events:
        return []

    # Build id -> event map + children map
    children: dict[str | None, list[dict[str, Any]]] = {}
    message_ids: set[str] = set()
    for ev in events:
        pid = ev.get("parentId")
        children.setdefault(pid, []).append(ev)
        if ev.get("type") == "message" and ev.get("id"):
            message_ids.add(ev["id"])

    # Find the first MESSAGE event — that's where the conversation starts.
    # A session typically starts with: session → model_change → thinking_level_change
    # → user → assistant(toolCall) → toolResult → assistant(text). The user
    # message is the first event whose parentId points to a NON-message event.
    first_message: dict[str, Any] | None = None
    for ev in events:
        if ev.get("type") != "message":
            continue
        pid = ev.get("parentId")
        if pid not in message_ids:
            first_message = ev
            break
    if first_message is None:
        # Fallback: pick the first message event of any kind
        for ev in events:
            if ev.get("type") == "message":
                first_message = ev
                break
    if first_message is None:
        return []

    turns: list[Turn] = []
    cur: dict[str, Any] | None = first_message
    while cur is not None:
        if cur.get("type") == "message":
            m = cur.get("message", {})
            role = m.get("role")
            parts = m.get("content", [])
            if role == "user":
                turns.append(Turn(kind="user", text=_text_of(parts)))
            elif role == "assistant":
                tool_calls = [p for p in parts if isinstance(p, dict) and p.get("type") == "toolCall"]
                text_parts = [p for p in parts if isinstance(p, dict) and p.get("type") == "text"]
                if tool_calls:
                    for tc in tool_calls:
                        turns.append(
                            Turn(
                                kind="tool_call",
                                tool_name=str(tc.get("name", "")),
                                arguments=tc.get("arguments") if isinstance(tc.get("arguments"), dict) else {},
                                tool_call_id=str(tc.get("id", "")),
                            )
                        )
                if text_parts:
                    turns.append(Turn(kind="assistant_text", text=_text_of(text_parts)))
            elif role == "toolResult":
                turns.append(
                    Turn(
                        kind="tool_result",
                        tool_name=str(m.get("toolName", "")),
                        text=_text_of(parts),
                        tool_call_id=str(m.get("toolCallId", "")),
                        is_error=bool(m.get("isError", False)),
                    )
                )
        # advance to first child (linear chain)
        kids = children.get(cur.get("id"), [])
        cur = kids[0] if kids else None

    return turns


# ── ChatML rendering ────────────────────────────────────────────────────

CANONICAL_TOOLS: set[str] = {
    "erp_analyze_pasted_error_with_kb",
    "erp_inspect_current_error_with_kb",
    "erp_get_current_error",
    "erp_create_ticket_from_current_error",
    "kb_rg_search",
    "kb_read_knowledge",
    "erp_query_state",
    "erp_handoff_to_it_agent",
    "erp_it_list_tickets",
    "erp_it_get_ticket",
    "erp_it_triage_ticket",
    "erp_it_resolve_ticket",
    "erp_it_close_ticket",
    "erp_it_reassign_ticket",
    "erp_it_add_comment",
}


def _tool_call_envelope(tool_name: str, arguments: dict[str, Any]) -> str:
    return f"<tool_call>\n{json.dumps({'name': tool_name, 'arguments': arguments}, ensure_ascii=False)}\n</tool_call>"


def render_sft_rows(turns: list[Turn], system_prompt: str) -> list[dict[str, Any]]:
    """Convert a parsed session into 0+ ChatML SFT rows.

    One SFT row per (user, tool_call, [tool_result, ...], assistant_text)
    subsequence. If the assistant emits a tool call whose name is NOT in
    CANONICAL_TOOLS we skip that turn — it teaches the wrong behavior.

    For sessions where the assistant emits multiple tool calls before a final
    text, we walk in order so the model learns the full pattern.
    """
    rows: list[dict[str, Any]] = []
    # Walk in windows of (user, optional tool_call + tool_result chain, assistant_text)
    i = 0
    while i < len(turns):
        t = turns[i]
        if t.kind != "user":
            i += 1
            continue
        user_text = t.text
        messages: list[dict[str, str]] = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_text},
        ]
        # Advance past user
        j = i + 1
        saw_tool_call = False
        while j < len(turns) and turns[j].kind in ("tool_call", "tool_result"):
            tc = turns[j]
            if tc.kind == "tool_call":
                if tc.tool_name not in CANONICAL_TOOLS:
                    # skip the rest of this turn window — model hallucinated a tool name
                    break
                messages.append(
                    {
                        "role": "assistant",
                        "content": _tool_call_envelope(tc.tool_name, tc.arguments or {}),
                    }
                )
                saw_tool_call = True
            else:  # tool_result
                messages.append(
                    {
                        "role": "tool",
                        "content": tc.text[:4000],  # truncate pathological tool payloads
                    }
                )
            j += 1
        # Optionally append the closing assistant_text
        if j < len(turns) and turns[j].kind == "assistant_text" and saw_tool_call:
            messages.append(
                {
                    "role": "assistant",
                    "content": turns[j].text[:4000],
                }
            )
            j += 1
        elif j < len(turns) and turns[j].kind == "assistant_text" and not saw_tool_call:
            # Plain-text reply (no tool call) — still useful as SFT signal
            messages.append(
                {
                    "role": "assistant",
                    "content": turns[j].text[:4000],
                }
            )
            saw_tool_call = True  # mark so we emit the row
            j += 1
        # Emit only if we observed at least one assistant message
        if any(m["role"] == "assistant" for m in messages):
            rows.append({"messages": messages})
        i = j if j > i else i + 1
    return rows


def iter_sessions(dir_: Path) -> Iterable[tuple[Path, list[Turn]]]:
    """Yield (path, parsed_turns) for every .jsonl in `dir_`. Skips files that
    fail to parse, yielding an empty list instead."""
    for path in sorted(dir_.glob("*.jsonl")):
        try:
            yield path, parse_session(path)
        except Exception:
            yield path, []