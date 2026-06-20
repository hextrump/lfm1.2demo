"""Merge LoRA adapter → GGUF Q4_K_M on Modal (A100).

Pipeline:
  1. PEFT merge: /out/lora_final + LiquidAI/LFM2-1.2B-Tool → /out/merged_hf
  2. llama.cpp convert_hf_to_gguf.py (vendored as a single file) → F16 GGUF
  3. llama-quantize via llama-cpp-python → Q4_K_M
  4. Persist Volume 'agent-p-out'.

Run from the project root (after train_lora.py):
    modal run scripts/modal/convert_to_gguf.py

This takes ~3-5 min on A100-40GB. The final GGUF is ~700 MB.

NOTES:
  - We do NOT build llama.cpp from source (the heavy `make` step often fails
    on Modal's small container build context). Instead we vendor only the
    single-file `convert_hf_to_gguf.py` script (no compilation needed) and
    use `llama-cpp-python`'s prebuilt quantizer.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import urllib.request

import modal

app = modal.App("agent-p-convert")

# Lightweight image: just torch + transformers/peft + llama-cpp-python (for the
# prebuilt llama-quantize binary). No heavy llama.cpp build.
LLAMA_CPP_CONVERTER_URL = (
    "https://raw.githubusercontent.com/ggml-org/llama.cpp/"
    "master/convert_hf_to_gguf.py"
)

image = (
    modal.Image.debian_slim(python_version="3.11")
    .apt_install("git", "build-essential", "cmake", "curl")
    .pip_install(
        "torch",
        "transformers",
        "peft",
        "huggingface_hub",
        "gguf",
        "numpy",
    )
    # Build llama-quantize AND install convert_hf_to_gguf.py with its
    # `gguf-conversion` package sibling. The vendoring is needed because
    # the script imports a sibling module that we can't curl as a single file.
    .run_commands(
        "git clone --depth 1 https://github.com/ggml-org/llama.cpp /llama.cpp && "
        "cd /llama.cpp && cmake -B build -DGGML_NATIVE=OFF -DLLAMA_CURL=OFF && "
        "cmake --build build --target llama-quantize -j$(nproc) && "
        "cp build/bin/llama-quantize /usr/local/bin/llama-quantize && "
        "chmod +x /usr/local/bin/llama-quantize && "
        "ls /llama.cpp/gguf-conversion 2>&1 | head -3"
    )
)

out_volume = modal.Volume.from_name("agent-p-out")


@app.function(
    image=image,
    gpu="A100-40GB",
    timeout=60 * 60,
    volumes={"/out": out_volume},
    secrets=[modal.Secret.from_name("hf-token")],
)
def convert() -> dict[str, str]:
    """Merge LoRA → HF → GGUF F16 → GGUF Q4_K_M."""
    import torch
    from peft import PeftModel
    from transformers import AutoModelForCausalLM, AutoTokenizer

    base_id = "LiquidAI/LFM2-1.2B-Tool"
    lora_dir = "/out/lora_final"
    merged_dir = "/out/merged_hf"
    f16_gguf = "/out/lfm2-1.2b-tool-q4_k_m.v1.f16.gguf"
    q4_gguf = "/out/lfm2-1.2b-tool-q4_k_m.v1.Q4_K_M.gguf"

    # ── 1) PEFT merge ──
    print("step 1/3: merging LoRA into base…", flush=True)
    base = AutoModelForCausalLM.from_pretrained(
        base_id, torch_dtype=torch.bfloat16, trust_remote_code=True
    )
    merged = PeftModel.from_pretrained(base, lora_dir).merge_and_unload()
    merged.save_pretrained(merged_dir, safe_serialization=True)
    AutoTokenizer.from_pretrained(base_id, trust_remote_code=True).save_pretrained(
        merged_dir
    )
    del base, merged
    torch.cuda.empty_cache()
    print(f"  merged HF dir: {merged_dir}", flush=True)

    # ── 2) HF → GGUF F16 (via convert_hf_to_gguf.py from llama.cpp repo) ──
    print("step 2/3: HF → GGUF F16…", flush=True)
    # The script and its sibling `gguf-conversion/` package both live in
    # the llama.cpp repo we cloned at image build time. Running with cwd
    # set there lets the relative `from gguf_conversion import …` succeed.
    proc = subprocess.run(
        ["python3", "/llama.cpp/convert_hf_to_gguf.py", merged_dir, "--outfile", f16_gguf],
        capture_output=True, text=True, cwd="/llama.cpp",
    )
    if proc.returncode != 0:
        print("=== convert_hf_to_gguf.py FAILED ===", flush=True)
        print("STDOUT:", proc.stdout[-3000:], flush=True)
        print("STDERR:", proc.stderr[-3000:], flush=True)
        raise SystemExit(f"convert_hf_to_gguf.py exited {proc.returncode}")

    # ── 3) F16 → Q4_K_M (via llama-quantize built above) ──
    print("step 3/3: quantize F16 → Q4_K_M…", flush=True)
    subprocess.check_call(["/usr/local/bin/llama-quantize", f16_gguf, q4_gguf, "Q4_K_M"])

    # Clean up intermediates
    Path_ = __import__("pathlib").Path
    Path_(f16_gguf).unlink(missing_ok=True)
    shutil.rmtree(merged_dir, ignore_errors=True)

    out_volume.commit()
    print(f"\n✓ GGUF saved to Volume 'agent-p-out' at {q4_gguf}", flush=True)
    return {"q4_gguf_path": q4_gguf}


@app.local_entrypoint()
def main() -> None:
    print("Merging LoRA + converting to GGUF Q4_K_M on A100…")
    print("  Estimated cost: ~$0.30-0.60 (~3-5 min)")
    print()
    result = convert.remote()
    print(f"\n✓ {result}")
    print("  next step: modal run scripts/modal/download_gguf.py")
    print("    OR: modal volume get agent-p-out <file> models/")