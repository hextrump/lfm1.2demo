SHELL := /usr/bin/env bash

PY ?= python3
UV ?= uv
LLAMA_PORT ?= 8080
STREAMLIT_PORT ?= 8501
LIVE_TAIL_PORT ?= 8765
LIVE_TAIL_LOG ?= /tmp/demo1_live_tail.log

ifeq ($(OS),Windows_NT)
VENV_PY := .venv/Scripts/python.exe
else
VENV_PY := .venv/bin/python
endif

.PHONY: help install install-py install-node serve live-tail run test test-unit test-runtime test-ui test-all clean data data-fetch data-split data-build-sessions data-build-tests data-build-scenarios data-build-kb data-concat data-validate modal-setup modal-upload modal-train modal-convert modal-download modal-pipeline

help:
	@echo "Targets:"
	@echo "  install     Install Python and Node dependencies"
	@echo "  serve       Start llama.cpp server with LFM2 1.2B Tool"
	@echo "  live-tail   Start the Live Tail SSE server (terminal feed above chat)"
	@echo "  run         Start the Streamlit demo"
	@echo "  test        Run the legacy mocked smoke test"
	@echo "  test-unit   Run unit tests only (no services needed, ~1s)"
	@echo "  test-runtime Run runtime tests (needs llama-server, ~5-10 min)"
	@echo "  test-ui     Run UI/Playwright tests (needs Streamlit + llama, ~3 min)"
	@echo "  test-all    Run unit + runtime + UI + generate HTML report"
	@echo "  clean       Remove local caches"

install: install-py install-node

install-py:
	@if command -v $(UV) >/dev/null 2>&1; then \
		$(UV) venv .venv --python 3.12 || $(UV) venv .venv; \
		$(UV) pip install -r requirements.txt; \
	else \
		$(PY) -m venv .venv; \
		$(VENV_PY) -m pip install --upgrade pip; \
		$(VENV_PY) -m pip install -r requirements.txt; \
	fi

install-node:
	@command -v npm >/dev/null 2>&1 || { echo "npm is required"; exit 1; }
	@npm install --no-audit --no-fund
	@chmod +x node_modules/.bin/pi 2>/dev/null || true

serve:
	@bash scripts/start_lfm25_server.sh

live-tail:
	@if pgrep -f "live_tail_server.py" >/dev/null 2>&1; then \
		echo "live tail already running on :$(LIVE_TAIL_PORT)"; \
	else \
		$(VENV_PY) scripts/live_tail_server.py --host 127.0.0.1 --port $(LIVE_TAIL_PORT) --log $(LIVE_TAIL_LOG); \
	fi

run:
	@LIVE_TAIL_SSE_URL=http://127.0.0.1:$(LIVE_TAIL_PORT)/sse?log=$(LIVE_TAIL_LOG) $(VENV_PY) -m streamlit run app.py --server.address 127.0.0.1 --server.port $(STREAMLIT_PORT)

test:
	@$(VENV_PY) tests/test_eval_with_mock.py

# ── pytest suites ──────────────────────────────────────────────────────
# Each suite auto-skips if its required services are not running.
#   test-unit   : no services needed, runs in < 1 second
#   test-runtime: needs llama-server running on :8080
#   test-ui     : needs Streamlit on :8501 AND llama-server on :8080
#   test-all    : runs all three suites, generates tests/reports/report.html
test-unit:
	@echo "==> Running unit tests (no services required)..."
	@$(VENV_PY) -m pytest tests/unit/ -v --tb=short

test-runtime:
	@echo "==> Running runtime tests (needs llama-server on :8080)..."
	@$(VENV_PY) -m pytest tests/runtime/ -v --tb=short

test-ui:
	@echo "==> Running UI tests (needs Streamlit :8501 + llama :8080)..."
	@$(VENV_PY) -m pytest tests/ui/ -v --tb=short

test-all:
	@echo "==> Running full test suite + generating report..."
	@mkdir -p tests/reports
	@$(VENV_PY) -m pytest tests/ \
		--html=tests/reports/report.html --self-contained-html \
		-v
	@echo ""
	@echo "Report: tests/reports/report.html"

clean:
	@find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@rm -rf .pytest_cache
	@rm -f $(LIVE_TAIL_LOG)

# ── data pipeline (Agent P fine-tuning) ─────────────────────────────────
# `make data` runs the full v1 dataset build:
#   1. fetch GitHub seed (schema authority)
#   2. split 207 session JSONLs into 80/20 train/eval
#   3. mine sessions → SFT + DPO
#   4. extract tests → SFT (using runtime/pi_agent.py as oracle)
#   5. synthesize 8 scenarios × 6 templates → SFT + DPO
#   6. synthesize KB citation demos → SFT (live ripgrep)
#   7. concat + dedupe all sources → data/sft_v1.jsonl + data/dpo_v1.jsonl
#   8. validate schema / canonical tools / KB paths / no eval leakage
# See scripts/_session_parser.py for the canonical tool set.
data-fetch:
	@mkdir -p data/seed
	@curl -sSL -o data/seed/agent_p_sft.jsonl \
		https://raw.githubusercontent.com/hextrump/lfm1.2demo/main/paper/demo1/erp_crm_sso_demo/training_data/agent_p_sft.jsonl
	@curl -sSL -o data/seed/agent_p_dpo.jsonl \
		https://raw.githubusercontent.com/hextrump/lfm1.2demo/main/paper/demo1/erp_crm_sso_demo/training_data/agent_p_dpo.jsonl
	@cd data/seed && sha256sum agent_p_sft.jsonl agent_p_dpo.jsonl > SHA256SUMS

data-split:
	@$(VENV_PY) scripts/split_sessions.py \
		--sessions-dir .pi-agent/sessions/--home-heyas-wslcode-demo1-final--/ \
		--ratio 0.8 \
		--train-list data/sessions_train.txt \
		--eval-list data/sessions_eval.txt \
		--eval-out data/eval_sessions.jsonl

data-build-sessions:
	@$(VENV_PY) scripts/build_agent_training_data.py \
		--sessions-list data/sessions_train.txt \
		--out-sft data/_sessions_sft.jsonl \
		--out-dpo data/_sessions_dpo.jsonl

data-build-tests:
	@$(VENV_PY) scripts/extract_tests_to_sft.py \
		--tests tests/unit tests/runtime \
		--out data/_tests_sft.jsonl

data-build-scenarios:
	@$(VENV_PY) scripts/synthesize_scenario_demos.py \
		--scenarios tests/fixtures/scenarios.py \
		--out data/_scenarios_sft.jsonl \
		--out-dpo data/_scenarios_dpo.jsonl

data-build-kb:
	@$(VENV_PY) scripts/synthesize_kb_citations.py \
		--kb knowledge \
		--out data/_kb_sft.jsonl

data-concat:
	@$(VENV_PY) scripts/concat_splits.py \
		--seed data/seed \
		--generated-glob "data/_*.jsonl" \
		--out-sft data/sft_v1.jsonl \
		--out-dpo data/dpo_v1.jsonl \
		--manifest data/manifest.json

data-validate:
	@$(VENV_PY) scripts/validate_training_data.py \
		data/sft_v1.jsonl data/dpo_v1.jsonl data/eval_sessions.jsonl \
		--kb knowledge --seed data/seed

data: data-fetch data-split data-build-sessions data-build-tests data-build-scenarios data-build-kb data-concat data-validate
	@echo ""
	@echo "data: built $(shell wc -l < data/sft_v1.jsonl 2>/dev/null || echo 0) SFT + $(shell wc -l < data/dpo_v1.jsonl 2>/dev/null || echo 0) DPO + $(shell wc -l < data/eval_sessions.jsonl 2>/dev/null || echo 0) eval rows"

# ── Modal Training Pipeline ─────────────────────────────────────────────
# Fine-tune LiquidAI/LFM2-1.2B-Tool on the v1 dataset (A100-40GB).
# See scripts/modal/README.md for the full guide and cost estimate.
MODAL ?= .venv/bin/modal

modal-setup:
	@echo "1) Make sure you have a Modal account:"
	@echo "   https://modal.com/signup"
	@echo ""
	@echo "2) Authenticate the CLI:"
	@echo "   $(MODAL) token new"
	@echo ""
	@echo "3) Create the HF token secret (one-time):"
	@echo "   $(MODAL) secret create hf-token HF_TOKEN=hf_xxxxxxxxxxxxxxxx"
	@echo ""
	@echo "4) Build the dataset if you haven't:"
	@echo "   make data"

modal-upload:
	@$(MODAL) run scripts/modal/upload_data.py

# --detach so the shell doesn't 2-minute-timeout; check status at modal.com/apps/
modal-train:
	@$(MODAL) run --detach scripts/modal/train_lora.py

modal-convert:
	@$(MODAL) run scripts/modal/convert_to_gguf.py

modal-download:
	@$(MODAL) run scripts/modal/download_gguf.py

modal-pipeline: modal-upload modal-train modal-convert modal-download
	@echo ""
	@echo "✓ Modal pipeline complete. Next: make serve && make test-runtime"
