"""Download the trained GGUF from Modal Volume to local models/.

Run from the project root (after convert_to_gguf.py):
    .venv/bin/modal run scripts/modal/download_gguf.py
    # OR (equivalent — just uses the local Python interpreter)
    .venv/bin/python scripts/modal/download_gguf.py

Downloads the Q4_K_M GGUF (~700 MB) to <project>/models/.
The script handles the original-GGUF rename so llama-server can pick up
the new model without further config changes.

Implementation: this is a LOCAL-only script. It uses the modal SDK
(importable from .venv) to read files from the Volume directly, no
subprocess to the `modal` CLI required.
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

import modal

PROJECT_ROOT = Path(__file__).resolve().parents[2]
MODELS_DIR = PROJECT_ROOT / "models"

app = modal.App("agent-p-download")
out_volume = modal.Volume.from_name("agent-p-out")


@app.local_entrypoint()
def main() -> None:
    # Enumerate top-level entries in /out via the SDK.
    # `listdir("/")` returns only direct children (not recursive).
    entries = out_volume.listdir("/")
    files = [e for e in entries if e.type.name == "FILE"]
    if not files:
        print("Volume 'agent-p-out' has no top-level files. Run train_lora.py + convert_to_gguf.py first.")
        sys.exit(1)

    print(f"Found {len(files)} top-level files in Volume 'agent-p-out':")
    for e in files:
        print(f"  {e.path.lstrip('/')}  ({e.size:,} bytes)")
    print()

    MODELS_DIR.mkdir(parents=True, exist_ok=True)

    for entry in files:
        remote_name = entry.path.lstrip("/")
        if not remote_name.endswith((".gguf", ".safetensors")):
            continue
        local_path = MODELS_DIR / Path(remote_name).name
        print(f"  downloading {remote_name} → {local_path}")
        payload_chunks = list(out_volume.read_file(remote_name))
        payload = b"".join(payload_chunks)
        local_path.write_bytes(payload)
        print(f"    saved {local_path.stat().st_size:,} bytes")

    # Promote the v1 GGUF so llama-server picks it up automatically.
    q4_v1 = MODELS_DIR / "lfm2-1.2b-tool-q4_k_m.v1.Q4_K_M.gguf"
    q4_orig = MODELS_DIR / "lfm2-1.2b-tool-q4_k_m.gguf"
    if q4_v1.exists() and not q4_orig.exists():
        shutil.copy(q4_v1, q4_orig)
        print(f"\n✓ promoted {q4_v1.name} → {q4_orig.name}")
    elif q4_v1.exists() and q4_orig.exists() and q4_v1.resolve() != q4_orig.resolve():
        backup = MODELS_DIR / "lfm2-1.2b-tool-q4_k_m.original.gguf"
        if not backup.exists():
            shutil.move(q4_orig, backup)
            print(f"  backed up original → {backup.name}")
        shutil.copy(q4_v1, q4_orig)
        print(f"✓ promoted {q4_v1.name} → {q4_orig.name}")

    print("\n✓ all artifacts downloaded to models/")
    print("  next step: make serve && make test-runtime")