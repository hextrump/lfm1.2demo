# Training data

Seed datasets for SFT and DPO LoRA fine-tuning of LFM 2.5 1.2B Instruct.

## Files

- `agent_p_sft.jsonl` — chat-style supervised fine-tuning examples.
- `agent_p_dpo.jsonl` — preference examples with `prompt`, `chosen`, and `rejected`.

## Format

SFT rows use the standard chat-message format:

```json
{
  "messages": [
    {"role": "system", "content": "You are Agent P. ..."},
    {"role": "user", "content": "<user prompt>"},
    {"role": "assistant", "content": "<tool_call>...</tool_call>"}
  ]
}
```

DPO rows use the TRL preference format:

```json
{
  "prompt": [
    {"role": "system", "content": "You are Agent P. ..."},
    {"role": "user", "content": "<user prompt>"}
  ],
  "chosen": [{"role": "assistant", "content": "<tool_call>...</tool_call>"}],
  "rejected": [{"role": "assistant", "content": "<tool_call>...</tool_call>"}]
}
```

## Generate from session logs

```bash
make build-data
# or
python3 scripts/build_agent_training_data.py
```

This reads Pi session JSONL files from
`.pi-agent/sessions/--*-erp_crm_sso_demo--/*.jsonl` and turns observed
failures into behavior-tuning data:

- Greeting / date prompts — `chosen` is a direct reply, no tool call.
- Pasted ERP/SSO errors — `chosen` calls `erp_analyze_pasted_error_with_kb`.
- Current ERP page requests — `chosen` calls `erp_get_current_error`.
- Explicit IT/ticket requests — `chosen` calls `erp_create_ticket_from_current_error`.
- Misuse of `read` / direct `erp_create_ticket` / empty text — DPO `rejected`.

## Train

```bash
make install-train
make train
```

Outputs LoRA adapters to `training_data/lora_agent_p/sft/` and
`training_data/lora_agent_p/dpo/`. Wire the adapter into llama.cpp via
`--lora` or convert to GGUF with `scripts/convert_lora_to_gguf.py`
(not included yet — contribute if you write it).

## Target scale

The seed datasets here are pilot examples (24 SFT, 25 DPO at last build).
For a real fine-tuning run, aim for:

- 300-800 SFT examples across multiple languages, error codes, and tools.
- 100-300 DPO pairs, weighted toward the known failure modes.
- 30+ fixed eval cases in `scripts/eval_agent_p.py`.

## References

- Liquid AI fine-tuning guide: <https://docs.liquid.ai/lfm/fine-tuning/datasets>
- TRL: <https://huggingface.co/docs/trl>
