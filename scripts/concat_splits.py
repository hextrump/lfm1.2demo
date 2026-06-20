#!/usr/bin/env python3
"""Concatenate all generated + seed JSONL files into the final v1 training sets.

Inputs (in order):
  - <seed-dir>/agent_p_sft.jsonl      (33 rows, GitHub schema authority)
  - <seed-dir>/agent_p_dpo.jsonl      (76 rows)
  - <generated-glob>                   (every data/_*.jsonl we produced)
Outputs:
  - <out-sft>     : all SFT rows concatenated, deduped by (system[:100], user[:100])
  - <out-dpo>     : all DPO rows concatenated, deduped by (system[:100], user[:100])
  - <manifest>    : JSON describing what we did (per-source counts, schema version, SHA256)
"""

from __future__ import annotations

import argparse
import datetime as _dt
import glob
import hashlib
import json
import sys
from pathlib import Path


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--seed", required=True, type=Path, help="Dir containing agent_p_{sft,dpo}.jsonl")
    p.add_argument("--generated-glob", required=True, help="Shell glob of data/_*.jsonl")
    p.add_argument("--out-sft", required=True, type=Path)
    p.add_argument("--out-dpo", required=True, type=Path)
    p.add_argument("--manifest", type=Path, default=None,
                   help="Optional path for the build manifest JSON")
    return p.parse_args()


def _is_sft_row(row: dict) -> bool:
    return "messages" in row and isinstance(row["messages"], list)


def _is_dpo_row(row: dict) -> bool:
    return (
        isinstance(row.get("prompt"), list)
        and isinstance(row.get("chosen"), list)
        and isinstance(row.get("rejected"), list)
    )


def _dedup_key_sft(row: dict) -> tuple[str, str, str]:
    """Dedupe SFT rows by (system_prefix, user_prefix, assistant_prefix).

    Including the assistant prefix matters because session-derived SFT rows
    often share the same (system, user) — what differentiates them is the
    tool the model should call (or the structured reply it should emit)."""
    msgs = row.get("messages", [])
    sys_ = next((m.get("content", "") for m in msgs if m.get("role") == "system"), "")
    usr = next((m.get("content", "") for m in msgs if m.get("role") == "user"), "")
    # The LAST assistant message is the model's reply (may follow tool messages)
    asst_msgs = [m.get("content", "") for m in msgs if m.get("role") == "assistant"]
    asst = asst_msgs[-1] if asst_msgs else ""
    return (sys_[:80], usr[:80], asst[:80])


def _dedup_key_dpo(row: dict) -> tuple[str, str, str]:
    """Dedupe DPO rows by (system_prefix, user_prefix, rejected_prefix).

    Unlike SFT, the same (system, user) prompt can have many valid `rejected`
    examples — each one teaches the model to reject a different bad pattern
    (e.g. `erp_draft_ticket` vs `erp_create_ticket` vs English reply). The
    seed `agent_p_dpo.jsonl` has 49 such rows sharing one prompt. Including
    `rejected_prefix` keeps all of them.
    """
    prompt = row.get("prompt", [])
    sys_ = next((m.get("content", "") for m in prompt if m.get("role") == "system"), "")
    usr = next((m.get("content", "") for m in prompt if m.get("role") == "user"), "")
    rej_list = row.get("rejected", [])
    rej = rej_list[0].get("content", "") if rej_list else ""
    return (sys_[:80], usr[:80], rej[:80])


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    args = _parse_args()
    args.out_sft.parent.mkdir(parents=True, exist_ok=True)
    args.out_dpo.parent.mkdir(parents=True, exist_ok=True)

    # Collect input files in deterministic order
    seed_sft = args.seed / "agent_p_sft.jsonl"
    seed_dpo = args.seed / "agent_p_dpo.jsonl"
    if not seed_sft.exists() or not seed_dpo.exists():
        print(f"missing seed files in {args.seed}", file=sys.stderr)
        return 2

    generated_files = sorted(glob.glob(args.generated_glob))

    # Per-source tallies
    sft_sources: list[tuple[Path, int, int]] = []  # (path, in_rows, out_rows)
    dpo_sources: list[tuple[Path, int, int]] = []

    seen_sft: set[tuple[str, str]] = set()
    seen_dpo: set[tuple[str, str]] = set()

    with args.out_sft.open("w", encoding="utf-8") as sft_out, \
         args.out_dpo.open("w", encoding="utf-8") as dpo_out:

        # 1. Seed SFT (must come first — schema authority)
        in_n = 0
        out_n = 0
        with seed_sft.open(encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                in_n += 1
                try:
                    row = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if not _is_sft_row(row):
                    continue
                key = _dedup_key_sft(row)
                if key in seen_sft:
                    continue
                seen_sft.add(key)
                sft_out.write(json.dumps(row, ensure_ascii=False) + "\n")
                out_n += 1
        sft_sources.append((seed_sft, in_n, out_n))

        # 2. Generated SFT files (in glob order)
        for path_str in generated_files:
            path = Path(path_str)
            # SFT files match pattern *_sft.jsonl; DPO files match *_dpo.jsonl
            is_sft = path.name.endswith("_sft.jsonl")
            is_dpo = path.name.endswith("_dpo.jsonl")
            if not (is_sft or is_dpo):
                continue
            in_n = 0
            out_n = 0
            with path.open(encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    in_n += 1
                    try:
                        row = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    if is_sft and _is_sft_row(row):
                        key = _dedup_key_sft(row)
                        if key in seen_sft:
                            continue
                        seen_sft.add(key)
                        sft_out.write(json.dumps(row, ensure_ascii=False) + "\n")
                        out_n += 1
                    elif is_dpo and _is_dpo_row(row):
                        key = _dedup_key_dpo(row)
                        if key in seen_dpo:
                            continue
                        seen_dpo.add(key)
                        dpo_out.write(json.dumps(row, ensure_ascii=False) + "\n")
                        out_n += 1
            if is_sft:
                sft_sources.append((path, in_n, out_n))
            else:
                dpo_sources.append((path, in_n, out_n))

        # 3. Seed DPO (must come last so seed SFT takes priority on dedup)
        in_n = 0
        out_n = 0
        with seed_dpo.open(encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                in_n += 1
                try:
                    row = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if not _is_dpo_row(row):
                    continue
                key = _dedup_key_dpo(row)
                if key in seen_dpo:
                    continue
                seen_dpo.add(key)
                dpo_out.write(json.dumps(row, ensure_ascii=False) + "\n")
                out_n += 1
        dpo_sources.append((seed_dpo, in_n, out_n))

    # Manifest
    if args.manifest is not None:
        args.manifest.parent.mkdir(parents=True, exist_ok=True)
        project_root = Path(__file__).resolve().parents[1]

        def _rel(p: Path) -> str:
            try:
                return str(p.relative_to(project_root))
            except ValueError:
                return str(p)

        manifest = {
            "schema_version": "v1",
            "built_at": _dt.datetime.now().isoformat(timespec="seconds"),
            "sft": {
                "total_rows": len(seen_sft),
                "sources": [
                    {"path": _rel(p), "in_rows": a, "out_rows": b, "sha256": _sha256(p)}
                    for (p, a, b) in sft_sources
                ],
            },
            "dpo": {
                "total_rows": len(seen_dpo),
                "sources": [
                    {"path": _rel(p), "in_rows": a, "out_rows": b, "sha256": _sha256(p)}
                    for (p, a, b) in dpo_sources
                ],
            },
        }
        args.manifest.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"wrote manifest: {args.manifest}", file=sys.stderr)

    print(
        f"concat_splits: sft_rows={len(seen_sft)} dpo_rows={len(seen_dpo)} "
        f"sft_sources={len(sft_sources)} dpo_sources={len(dpo_sources)}",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())