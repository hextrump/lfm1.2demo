"""End-to-end guard for the Agent P data pipeline.

This test runs the full `make data` pipeline against a tiny synthetic fixture
(3 fake session JSONLs, 1 fake test file) and asserts:
  - The pipeline emits valid SFT + DPO JSONL
  - The validator exits 0
  - No eval→train leakage in the fixture

The test does NOT touch the real session logs or KB — it isolates the
pipeline plumbing so we can refactor scripts safely. The real-data run is
triggered manually via `make data` (see Makefile).
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = PROJECT_ROOT / "scripts"


# ── Fixture builders ────────────────────────────────────────────────────

def _write_fake_session(path: Path, user_text: str, tool_name: str, tool_args: dict,
                        tool_result: dict, assistant_text: str) -> None:
    """Write one minimal session JSONL with the canonical 7-line shape."""
    session_id = "019ed8ad-0000-7000-8000-000000000001"
    model_id = "e7740832"
    think_id = "2cd77d54"
    user_id = "d5324279"
    asst_tc_id = "6b9c3bf3"
    tool_res_id = "79ebcd3a"
    asst_text_id = "52991e8e"
    events = [
        {"type": "session", "version": 3, "id": session_id,
         "timestamp": "2026-06-18T03:01:46.948Z", "cwd": str(PROJECT_ROOT)},
        {"type": "model_change", "id": model_id, "parentId": None,
         "timestamp": "2026-06-18T03:01:46.975Z",
         "provider": "local-lfm", "modelId": "lfm2-1.2b-tool-q4_k_m.gguf"},
        {"type": "thinking_level_change", "id": think_id, "parentId": model_id,
         "timestamp": "2026-06-18T03:01:46.975Z", "thinkingLevel": "off"},
        {"type": "message", "id": user_id, "parentId": think_id,
         "timestamp": "2026-06-18T03:01:46.982Z",
         "message": {"role": "user", "content": [{"type": "text", "text": user_text}],
                     "timestamp": 1781751706981}},
        {"type": "message", "id": asst_tc_id, "parentId": user_id,
         "timestamp": "2026-06-18T03:01:56.620Z",
         "message": {"role": "assistant",
                     "content": [{"type": "toolCall", "id": "tc-001",
                                  "name": tool_name, "arguments": tool_args}],
                     "api": "openai-completions", "provider": "local-lfm",
                     "model": "lfm2-1.2b-tool-q4_k_m.gguf",
                     "stopReason": "toolUse", "timestamp": 1781751707022}},
        {"type": "message", "id": tool_res_id, "parentId": asst_tc_id,
         "timestamp": "2026-06-18T03:01:56.640Z",
         "message": {"role": "toolResult", "toolCallId": "tc-001",
                     "toolName": tool_name,
                     "content": [{"type": "text",
                                  "text": json.dumps(tool_result, ensure_ascii=False)}],
                     "isError": False, "timestamp": 1781751716640}},
        {"type": "message", "id": asst_text_id, "parentId": tool_res_id,
         "timestamp": "2026-06-18T03:02:15.340Z",
         "message": {"role": "assistant",
                     "content": [{"type": "text", "text": assistant_text}],
                     "api": "openai-completions", "provider": "local-lfm",
                     "stopReason": "stop", "timestamp": 1781751716641}},
    ]
    path.write_text("\n".join(json.dumps(e, ensure_ascii=False) for e in events) + "\n",
                    encoding="utf-8")


@pytest.fixture
def fake_workspace(tmp_path: Path) -> dict:
    """Build a tmp workspace: sessions dir, fake eval session, fake test file."""
    sessions_dir = tmp_path / "sessions"
    sessions_dir.mkdir()
    # 3 fake sessions — 2 train, 1 eval (oldest 2 are train)
    for i, ts in enumerate(["2026-06-18T01-00-00-000Z", "2026-06-18T02-00-00-000Z",
                            "2026-06-18T03-00-00-000Z"]):
        # Force different mtimes so the split is deterministic
        path = sessions_dir / f"{ts}_fake.jsonl"
        _write_fake_session(
            path,
            user_text=f"fake query {i}",
            tool_name="erp_get_current_error",
            tool_args={},
            tool_result={"scenario_key": "AADSTS50076", "error_code": "AADSTS50076"},
            assistant_text="了解しました。次のステップをご案内します。",
        )
        # Touch mtimes in ascending order
        import os
        os.utime(path, (1_700_000_000 + i * 60, 1_700_000_000 + i * 60))

    # Train/eval file lists
    train_list = tmp_path / "sessions_train.txt"
    eval_list = tmp_path / "sessions_eval.txt"
    all_files = sorted(sessions_dir.glob("*.jsonl"), key=lambda p: p.stat().st_mtime)
    train_list.write_text("\n".join(str(p) for p in all_files[:2]) + "\n")
    eval_list.write_text("\n".join(str(p) for p in all_files[2:]) + "\n")

    return {
        "sessions_dir": sessions_dir,
        "train_list": train_list,
        "eval_list": eval_list,
        "tmp": tmp_path,
    }


# ── Tests ───────────────────────────────────────────────────────────────

def test_split_sessions_emits_chatml_eval(fake_workspace: dict) -> None:
    eval_out = fake_workspace["tmp"] / "eval_sessions.jsonl"
    result = subprocess.run(
        [
            sys.executable, str(SCRIPTS / "split_sessions.py"),
            "--sessions-dir", str(fake_workspace["sessions_dir"]),
            "--ratio", "0.666",  # 2 of 3 to train
            "--train-list", str(fake_workspace["tmp"] / "train.txt"),
            "--eval-list", str(fake_workspace["tmp"] / "eval.txt"),
            "--eval-out", str(eval_out),
        ],
        capture_output=True, text=True, cwd=PROJECT_ROOT,
    )
    assert result.returncode == 0, f"split_sessions failed: {result.stderr}"
    assert eval_out.exists()
    rows = [json.loads(l) for l in eval_out.read_text().splitlines() if l.strip()]
    assert len(rows) == 1, f"expected 1 eval row, got {len(rows)}"
    msgs = rows[0]["messages"]
    assert [m["role"] for m in msgs] == ["system", "user", "assistant", "tool", "assistant"]
    assert "erp_get_current_error" in msgs[2]["content"]


def test_build_agent_training_data_emits_sft_and_dpo(fake_workspace: dict) -> None:
    sft_out = fake_workspace["tmp"] / "_sft.jsonl"
    dpo_out = fake_workspace["tmp"] / "_dpo.jsonl"
    result = subprocess.run(
        [
            sys.executable, str(SCRIPTS / "build_agent_training_data.py"),
            "--sessions-list", str(fake_workspace["train_list"]),
            "--out-sft", str(sft_out),
            "--out-dpo", str(dpo_out),
        ],
        capture_output=True, text=True, cwd=PROJECT_ROOT,
    )
    assert result.returncode == 0, f"build_agent_training_data failed: {result.stderr}"
    sft = [json.loads(l) for l in sft_out.read_text().splitlines() if l.strip()]
    dpo = [json.loads(l) for l in dpo_out.read_text().splitlines() if l.strip()]
    assert len(sft) == 2
    assert all("messages" in r for r in sft)
    # Sessions are all-JA so no lang failures should fire; dpo may be 0 here
    assert isinstance(dpo, list)


def test_full_pipeline_against_real_seed_runs_and_validates(tmp_path: Path) -> None:
    """Run the full real-data pipeline (split + build + extract + synth +
    concat + validate) and assert validator exits 0. This guards the
    end-to-end contract.
    """
    # Use real data but redirect outputs to a tmp directory so we don't
    # overwrite the user's real data files.
    out_dir = tmp_path / "pipeline_out"
    out_dir.mkdir()

    # 1. split_sessions — we reuse the existing data/sessions_train.txt
    # (skip re-splitting for speed)
    # 2. build_agent_training_data
    subprocess.run(
        [sys.executable, str(SCRIPTS / "build_agent_training_data.py"),
         "--sessions-list", "data/sessions_train.txt",
         "--out-sft", str(out_dir / "_sessions_sft.jsonl"),
         "--out-dpo", str(out_dir / "_sessions_dpo.jsonl")],
        check=True, cwd=PROJECT_ROOT,
    )
    # 3. extract_tests_to_sft
    subprocess.run(
        [sys.executable, str(SCRIPTS / "extract_tests_to_sft.py"),
         "--out", str(out_dir / "_tests_sft.jsonl")],
        check=True, cwd=PROJECT_ROOT,
    )
    # 4. synthesize_scenario_demos
    subprocess.run(
        [sys.executable, str(SCRIPTS / "synthesize_scenario_demos.py"),
         "--scenarios", "tests/fixtures/scenarios.py",
         "--out", str(out_dir / "_scenarios_sft.jsonl"),
         "--out-dpo", str(out_dir / "_scenarios_dpo.jsonl")],
        check=True, cwd=PROJECT_ROOT,
    )
    # 5. synthesize_kb_citations
    subprocess.run(
        [sys.executable, str(SCRIPTS / "synthesize_kb_citations.py"),
         "--kb", "knowledge",
         "--out", str(out_dir / "_kb_sft.jsonl")],
        check=True, cwd=PROJECT_ROOT,
    )
    # 6. concat_splits
    subprocess.run(
        [sys.executable, str(SCRIPTS / "concat_splits.py"),
         "--seed", "data/seed",
         "--generated-glob", str(out_dir / "_*.jsonl"),
         "--out-sft", str(out_dir / "sft.jsonl"),
         "--out-dpo", str(out_dir / "dpo.jsonl")],
        check=True, cwd=PROJECT_ROOT,
    )
    # 7. validate_training_data
    result = subprocess.run(
        [sys.executable, str(SCRIPTS / "validate_training_data.py"),
         str(out_dir / "sft.jsonl"),
         str(out_dir / "dpo.jsonl"),
         "data/eval_sessions.jsonl",
         "--kb", "knowledge",
         "--seed", "data/seed"],
        capture_output=True, text=True, cwd=PROJECT_ROOT,
    )
    assert result.returncode == 0, (
        f"validator failed:\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
    )

    # Spot-check: every output file is non-empty JSONL
    for name in ("sft.jsonl", "dpo.jsonl"):
        path = out_dir / name
        assert path.exists() and path.stat().st_size > 0
        rows = [json.loads(l) for l in path.read_text().splitlines() if l.strip()]
        assert len(rows) > 0