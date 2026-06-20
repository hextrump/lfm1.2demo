"""Two-stage LoRA fine-tuning on Modal (A100).

Pipeline:
  Stage 1 — SFT (3 epochs) on data/sft_v1.jsonl  (311 ChatML rows)
  Stage 2 — DPO (1 epoch)  on data/dpo_v1.jsonl  (186 TRL rows)

Reads data from Volume 'agent-p-data' (see upload_data.py).
Writes the merged LoRA adapter to Volume 'agent-p-out'.

Base model: LiquidAI/LFM2-1.2B-Tool  (matches lfm2-1.2b-tool-q4_k_m.gguf)

Run from the project root:
    modal run --detach scripts/modal/train_lora.py        # background, returns log URL
    modal run scripts/modal/train_lora.py                  # foreground (~25-45 min on A100)

The `--detach` flag is recommended — Modal will email you when it finishes.

REQUIREMENTS:
  - modal secret create hf-token HF_TOKEN=hf_xxxxxxxx    (one-time)
  - data already uploaded via upload_data.py
"""

from __future__ import annotations

import modal

app = modal.App("agent-p-train")

# ── Image: CUDA + transformers/peft/trl/bitsandbytes/accelerate/datasets ──
# torch==2.3.1 is required because TRL 0.13 imports `FSDPModule` from
# torch.distributed.fsdp, which was removed/moved in torch 2.4+. accelerate
# 0.34.x is required because TRL/peft call `unwrap_model(keep_torch_compile=)`
# which was added in accelerate 0.34.0. transformers 4.44.x is the matching
# era (TRL 0.13 requires <4.47).
image = (
    modal.Image.debian_slim(python_version="3.11")
    .apt_install("git")
    .pip_install(
        "torch==2.3.1",                    # has FSDPModule (TRL 0.13)
        "peft==0.13.2",
        "trl==0.13.0",
        "accelerate==1.10.1",              # has unwrap_model(keep_torch_compile=)
        "datasets==3.1.0",
        "huggingface_hub",
    )
    # Install transformers from main AFTER torch so it sees torch as installed.
    # Main has lfm2 support that no released version of transformers has yet.
    .run_commands(
        "pip install --no-deps "
        "git+https://github.com/huggingface/transformers.git@main"
    )
)

data_volume = modal.Volume.from_name("agent-p-data")
out_volume = modal.Volume.from_name("agent-p-out", create_if_missing=True)


@app.function(
    image=image,
    gpu="A100-40GB",                 # 40GB VRAM is plenty for 1.2B + QLoRA
    timeout=2 * 60 * 60,             # 2 hours ceiling
    volumes={
        "/data": data_volume,
        "/out":  out_volume,
    },
    secrets=[modal.Secret.from_name("hf-token")],
)
def train() -> dict[str, str]:
    """Run SFT then DPO; save the final LoRA adapter to /out/lora_final."""
    import os
    import torch

    # ── Compat shim: newer transformers (>=4.55) calls
    # `torch.utils._pytree.register_pytree_node`, which only exists in
    # torch >= 2.2. We pinned torch==2.1.2 to keep `FSDPModule` available
    # for TRL 0.13. Alias the new name to the old pytree registration.
    try:
        import torch.utils._pytree as _pytree
        if not hasattr(_pytree, "register_pytree_node"):
            from torch.utils import _pytree as _p
            _pytree.register_pytree_node = _p.register_pytree_node
    except Exception:
        pass  # fall through; some torch versions just don't need it

    from datasets import load_dataset
    from peft import LoraConfig
    from transformers import (
        AutoModelForCausalLM,
        AutoTokenizer,
    )
    # Import SFT first (used in stage 1)
    from trl import SFTConfig, SFTTrainer
    # DPO import is wrapped so we can fail gracefully if TRL/torch have an
    # FSDP API mismatch on this image. If DPOTrainer import fails we still
    # produce a usable SFT-only adapter and log a clear warning.
    try:
        from trl import DPOConfig, DPOTrainer  # noqa: F401
    except Exception as exc:
        print(f"WARNING: DPO trainer unavailable ({exc}); producing SFT-only adapter.", flush=True)
        DPOTrainer = None
        DPOConfig = None

    base_id = "LiquidAI/LFM2-1.2B-Tool"

    # Debug: print installed versions
    import transformers, peft, trl, accelerate, torch
    print(f"torch={torch.__version__} transformers={transformers.__version__} "
          f"peft={peft.__version__} trl={trl.__version__} "
          f"accelerate={accelerate.__version__}", flush=True)

    # Load base model in pure bf16 — A100 40GB has plenty of memory for
    # 1.2B params (~2.4 GB) + LoRA adapters + activations. We avoid QLoRA
    # because TRL 0.13's DPOTrainer with ref_model=None can't take gradients
    # through a 4-bit base model.
    print(f"loading {base_id} in bf16…", flush=True)
    tok = AutoTokenizer.from_pretrained(base_id, trust_remote_code=True)
    if tok.pad_token is None:
        tok.pad_token = tok.eos_token
    model = AutoModelForCausalLM.from_pretrained(
        base_id,
        torch_dtype=torch.bfloat16,
        device_map="auto",
        trust_remote_code=True,
    )
    model.config.use_cache = False
    model.gradient_checkpointing_enable()
    model.enable_input_require_grads()
    print("base model loaded", flush=True)

    lora_cfg = LoraConfig(
        r=16,
        lora_alpha=64,            # doubled from 32 → stronger persona
        target_modules=[
            "q_proj", "k_proj", "v_proj", "o_proj",
            "gate_proj", "up_proj", "down_proj",
        ],
        lora_dropout=0.05,
        bias="none",
        task_type="CAUSAL_LM",
    )

    # ── Stage 1: SFT ──
    print("\n=== Stage 1: SFT ===", flush=True)
    sft_ds = load_dataset(
        "json", data_files="/data/sft_v1.jsonl", split="train"
    )
    print(f"sft rows: {len(sft_ds)}", flush=True)
    # NB: TRL renames the seq-length field between minor versions
    # (`max_seq_length` in 0.12, `max_length` in 0.13+). We omit it here
    # and rely on TRL's default (1024); all our SFT rows fit comfortably.
    sft_cfg = SFTConfig(
        output_dir="/out/lora_sft",
        num_train_epochs=8,            # 8 epochs (was 3) — deeper persona imprint
        per_device_train_batch_size=8,    # A100 40GB has plenty
        gradient_accumulation_steps=2,    # effective batch = 16
        learning_rate=1e-4,             # halved from 2e-4 for stability
        lr_scheduler_type="cosine",
        warmup_ratio=0.05,
        bf16=True,
        optim="paged_adamw_8bit",
        logging_steps=10,
        save_strategy="epoch",
        save_total_limit=1,
        report_to="none",
        dataset_text_field="messages",    # TRL auto-applies chat template
    )
    sft_trainer = SFTTrainer(
        model=model,
        train_dataset=sft_ds,
        peft_config=lora_cfg,
        args=sft_cfg,
        processing_class=tok,
    )
    sft_trainer.train()
    print("SFT done", flush=True)

    # ── Stage 2: DPO (continues from SFT-trained LoRA) ──
    if DPOTrainer is None:
        print("\n=== Stage 2: DPO SKIPPED (TRL/DPOTrainer unavailable) ===", flush=True)
    else:
        print("\n=== Stage 2: DPO ===", flush=True)
        dpo_ds = load_dataset(
            "json", data_files="/data/dpo_v1.jsonl", split="train"
        )
        print(f"dpo rows: {len(dpo_ds)}", flush=True)
        dpo_cfg = DPOConfig(
            output_dir="/out/lora_dpo",
            num_train_epochs=2,                  # 2 epochs of DPO
            per_device_train_batch_size=2,
            gradient_accumulation_steps=8,       # effective batch = 16
            learning_rate=5e-6,                  # DPO wants a small LR
            bf16=True,
            optim="paged_adamw_8bit",
            logging_steps=5,
            save_strategy="epoch",
            save_total_limit=1,
            max_length=2048,
            max_prompt_length=1024,
            beta=0.1,
            report_to="none",
        )
        # ref_model=None + PEFT → TRL auto-disables adapter for the reference forward pass
        dpo_trainer = DPOTrainer(
            model=model,
            ref_model=None,
            train_dataset=dpo_ds,
            args=dpo_cfg,
            processing_class=tok,
        )
        dpo_trainer.train()
        print("DPO done", flush=True)

    # ── Save final adapter ──
    # The SFT/DPO trainers wrap `model` in a PEFT model. Save from the trainer's
    # PEFT wrapper so we get `adapter_model.safetensors` + `adapter_config.json`
    # rather than the full merged weights.
    print("\nsaving final LoRA to /out/lora_final…", flush=True)
    peft_model = sft_trainer.model
    peft_model.save_pretrained("/out/lora_final")
    tok.save_pretrained("/out/lora_final")

    # CRITICAL: persist the Volume so the next function (convert_to_gguf) can see it
    out_volume.commit()
    print("\n✓ training complete. LoRA saved to Volume 'agent-p-out' at /lora_final", flush=True)

    return {"adapter_path": "/out/lora_final", "base_id": base_id}


@app.local_entrypoint()
def main() -> None:
    print("Starting LoRA fine-tuning on Modal (A100-40GB)…")
    print("  SFT: 3 epochs on 311 rows")
    print("  DPO: 1 epoch on 186 rows (skipped if DPOTrainer unavailable)")
    print("  Estimated cost: ~$1.50-3.00 on A100-40GB (~25-45 min)")
    print("  Use --detach to run in background.")
    print()
    result = train.remote()
    print(f"\n✓ {result}")
    print("  next step: modal run scripts/modal/convert_to_gguf.py")