"""Upload the v1 training datasets to a Modal Volume.

Run from the project root:
    modal run scripts/modal/upload_data.py

This creates the `agent-p-data` Volume on first run and copies:
    data/sft_v1.jsonl        — 311 ChatML rows (SFT)
    data/dpo_v1.jsonl        — 186 TRL rows (DPO)
    data/eval_sessions.jsonl — 42 held-out ChatML rows
    data/manifest.json       — build provenance

Re-running is safe: each file is overwritten via Volume.write_file().
"""

from __future__ import annotations

import sys
from pathlib import Path

import modal

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
LOCAL_FILES = ["sft_v1.jsonl", "dpo_v1.jsonl", "eval_sessions.jsonl", "manifest.json"]

app = modal.App("agent-p-data-upload")
data_volume = modal.Volume.from_name("agent-p-data", create_if_missing=True)


@app.local_entrypoint()
def main() -> None:
    """Read files locally and push bytes to the Modal Volume via the SDK."""
    sizes: dict[str, int] = {}
    with data_volume.batch_upload() as batch:
        for name in LOCAL_FILES:
            src = DATA_DIR / name
            if not src.exists():
                print(f"  missing local file: {src}", file=sys.stderr)
                continue
            # batch_upload does not overwrite — remove existing file first.
            try:
                data_volume.remove_file(f"/{name}")
                print(f"  removed stale {name}", file=sys.stderr)
            except Exception:
                # File probably didn't exist; ignore.
                pass
            batch.put_file(src, f"/{name}")
            sizes[name] = src.stat().st_size
            print(f"  uploaded {name}: {sizes[name]:,} bytes", file=sys.stderr)

    total = sum(sizes.values())
    print(f"\n✓ uploaded {len(sizes)} files ({total:,} bytes) to Modal Volume 'agent-p-data'")
    print("  next step: modal run --detach scripts/modal/train_lora.py")