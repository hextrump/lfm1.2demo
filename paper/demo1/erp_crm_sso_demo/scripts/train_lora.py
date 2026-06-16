from __future__ import annotations

import argparse
import json
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
SFT_PATH = APP_DIR / "training_data" / "agent_p_sft.jsonl"
DPO_PATH = APP_DIR / "training_data" / "agent_p_dpo.jsonl"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="SFT + DPO LoRA training for Agent P (LFM2.5 1.2B).")
    parser.add_argument("--base-model", default="LiquidAI/LFM2.5-1.2B-Instruct", help="HF model id or local path")
    parser.add_argument("--output-dir", default=str(APP_DIR / "training_data" / "lora_agent_p"), help="Where to save adapters")
    parser.add_argument("--sft-epochs", type=float, default=2.0)
    parser.add_argument("--dpo-epochs", type=float, default=1.0)
    parser.add_argument("--lora-r", type=int, default=16)
    parser.add_argument("--lora-alpha", type=int, default=32)
    parser.add_argument("--lora-dropout", type=float, default=0.05)
    parser.add_argument("--learning-rate", type=float, default=2e-4)
    parser.add_argument("--batch-size", type=int, default=1)
    parser.add_argument("--grad-accum", type=int, default=8)
    parser.add_argument("--max-seq-len", type=int, default=2048)
    parser.add_argument("--skip-sft", action="store_true", help="Skip SFT stage and run DPO only")
    parser.add_argument("--skip-dpo", action="store_true", help="Skip DPO stage and run SFT only")
    parser.add_argument("--use-4bit", action="store_true", help="Use bitsandbytes 4-bit quantization (QLoRA)")
    return parser.parse_args()


def load_jsonl(path: Path) -> list[dict]:
    rows: list[dict] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            rows.append(json.loads(line))
    return rows


def build_model_and_tokenizer(base_model: str, use_4bit: bool):
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

    quant_config = None
    if use_4bit:
        quant_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.bfloat16,
            bnb_4bit_use_double_quant=True,
        )

    tokenizer = AutoTokenizer.from_pretrained(base_model, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    model = AutoModelForCausalLM.from_pretrained(
        base_model,
        quantization_config=quant_config,
        torch_dtype=torch.bfloat16 if quant_config is None else None,
        device_map="auto",
        trust_remote_code=True,
    )
    model.config.use_cache = False
    return model, tokenizer


def build_lora(model, args: argparse.Namespace):
    from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training

    if args.use_4bit:
        model = prepare_model_for_kbit_training(model)

    target_modules = ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"]
    config = LoraConfig(
        r=args.lora_r,
        lora_alpha=args.lora_alpha,
        lora_dropout=args.lora_dropout,
        bias="none",
        task_type="CAUSAL_LM",
        target_modules=target_modules,
    )
    return get_peft_model(model, config)


def run_sft(model, tokenizer, args: argparse.Namespace, output_dir: Path) -> None:
    from trl import SFTConfig, SFTTrainer

    sft_rows = load_jsonl(SFT_PATH)
    if not sft_rows:
        print("[SFT] no SFT data found, skipping")
        return

    sft_dir = output_dir / "sft"
    config = SFTConfig(
        output_dir=str(sft_dir),
        num_train_epochs=args.sft_epochs,
        per_device_train_batch_size=args.batch_size,
        gradient_accumulation_steps=args.grad_accum,
        learning_rate=args.learning_rate,
        bf16=True,
        max_length=args.max_seq_len,
        logging_steps=5,
        save_strategy="epoch",
        report_to=[],
        gradient_checkpointing=True,
        dataset_text_field=None,
    )
    trainer = SFTTrainer(
        model=model,
        args=config,
        train_dataset=sft_rows,
        processing_class=tokenizer,
    )
    trainer.train()
    trainer.save_model(str(sft_dir))
    tokenizer.save_pretrained(str(sft_dir))
    print(f"[SFT] adapter saved to {sft_dir}")


def run_dpo(model, tokenizer, args: argparse.Namespace, output_dir: Path) -> None:
    from trl import DPOConfig, DPOTrainer

    dpo_rows = load_jsonl(DPO_PATH)
    if not dpo_rows:
        print("[DPO] no DPO data found, skipping")
        return

    dpo_dir = output_dir / "dpo"
    config = DPOConfig(
        output_dir=str(dpo_dir),
        num_train_epochs=args.dpo_epochs,
        per_device_train_batch_size=args.batch_size,
        gradient_accumulation_steps=args.grad_accum,
        learning_rate=args.learning_rate / 2,
        bf16=True,
        max_length=args.max_seq_len,
        max_prompt_length=args.max_seq_len // 2,
        logging_steps=5,
        save_strategy="epoch",
        report_to=[],
        gradient_checkpointing=True,
        beta=0.1,
    )
    trainer = DPOTrainer(
        model=model,
        ref_model=None,
        args=config,
        train_dataset=dpo_rows,
        processing_class=tokenizer,
    )
    trainer.train()
    trainer.save_model(str(dpo_dir))
    tokenizer.save_pretrained(str(dpo_dir))
    print(f"[DPO] adapter saved to {dpo_dir}")


def main() -> None:
    args = parse_args()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    model, tokenizer = build_model_and_tokenizer(args.base_model, args.use_4bit)
    model = build_lora(model, args)

    if not args.skip_sft:
        run_sft(model, tokenizer, args, output_dir)
        if not args.skip_dpo:
            from peft import PeftModel
            sft_dir = output_dir / "sft"
            model = PeftModel.from_pretrained(model, str(sft_dir), is_trainable=True)

    if not args.skip_dpo:
        run_dpo(model, tokenizer, args, output_dir)


if __name__ == "__main__":
    main()
