# Modal Training Pipeline for Agent P LoRA

Fine-tunes `LiquidAI/LFM2-1.2B-Tool` on the Agent P v1 dataset (311 SFT + 186 DPO + 42 eval rows) and converts the result to GGUF Q4_K_M, matching the deployed `lfm2-1.2b-tool-q4_k_m.gguf`.

## One-time setup

```bash
# 1. Modal account + CLI (already installed in .venv)
.venv/bin/modal token new

# 2. HuggingFace read token (https://huggingface.co/settings/tokens)
.venv/bin/modal secret create hf-token HF_TOKEN=hf_xxxxxxxxxxxxxxxx

# 3. Build the data once
make data
```

## Run the pipeline

```bash
# Stage 1 — upload data to a Modal Volume (~30s)
.venv/bin/modal run scripts/modal/upload_data.py

# Stage 2 — train (SFT 3 epochs + DPO 1 epoch, A100-40GB, ~25-45 min)
.venv/bin/modal run --detach scripts/modal/train_lora.py
# Optional: stream logs at https://modal.com/apps/

# Stage 3 — convert LoRA → GGUF Q4_K_M (~5-10 min)
.venv/bin/modal run scripts/modal/convert_to_gguf.py

# Stage 4 — download the GGUF (~30s for 700 MB)
.venv/bin/modal run scripts/modal/download_gguf.py

# Stage 5 — verify
make serve && make test-runtime
```

Or use the chained Makefile targets: `make modal-upload`, `make modal-train`, `make modal-convert`, `make modal-download`, `make modal-pipeline`.

## Cost estimate

| Stage | GPU | Duration | Cost |
|---|---|---|---|
| upload | CPU | 30s | $0.00 |
| train (SFT 3ep + DPO 1ep, 311+186 rows) | A100-40GB | 25-45 min | **$1.50–3.00** |
| convert (merge + GGUF + quantize) | A100-40GB | 5-10 min | **$0.30–0.60** |
| download | CPU | 30s | $0.00 |
| **Total** | | **~30-55 min** | **~$2.00–3.50** |

Modal pricing: https://modal.com/pricing (A100-40GB ≈ $0.001004/秒 as of 2026-06).

## Output layout (in `models/`)

```
models/
├── lfm2-1.2b-tool-q4_k_m.original.gguf     # backup of the pre-LoRA model
├── lfm2-1.2b-tool-q4_k_m.gguf              # promoted v1 model (llama-server picks this up)
├── lfm2-1.2b-tool-q4_k_m.v1.Q4_K_M.gguf    # explicit v1 (same content as above)
├── lora_v1/                                # PEFT adapter (for reference / re-merging)
│   ├── adapter_config.json
│   └── adapter_model.safetensors
```

## Troubleshooting

| Error | Fix |
|---|---|
| `SecretNotFound: hf-token` | `modal secret create hf-token HF_TOKEN=hf_xxx` |
| `OSError: [Errno 28] No space left` | Volumes are 10 GB by default. Re-run upload to clean stale files, or `modal volume rm agent-p-data --force` then re-upload. |
| `RuntimeError: CUDA out of memory` | Reduce `per_device_train_batch_size` in train_lora.py (8 → 4) or pick `A100-80GB` |
| `JSONDecodeError` in convert | The merged HF dir is corrupted. Re-run train_lora.py and try convert again. |
| Model produces garbage after deployment | Lower LoRA scaling: pass `--lora-scaled 0.5` to llama-server, OR re-train with smaller `lora_alpha` (32 → 16) |

## Iterating

To re-train with different hyper-params:

```bash
# Clear old outputs
.venv/bin/modal volume rm agent-p-out --force

# Tweak scripts/modal/train_lora.py (r, alpha, lr, epochs)
# Then re-run the pipeline
make modal-pipeline
```

To push the dataset toward README's 800-row SFT target:

```bash
# Add more synthetic scenarios
# Edit scripts/synthesize_scenario_demos.py to emit 3 rejected per row instead of 1
make data
make modal-upload
make modal-train
```