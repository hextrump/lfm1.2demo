SHELL := /usr/bin/env bash

PY ?= python3
PIP ?= $(PY) -m pip
UV ?= uv

LLAMA_PORT ?= 8080
LLAMA_CTX ?= 32768
STREAMLIT_PORT ?= 8501

ROOT_DIR := $(shell pwd)

.PHONY: help install install-py install-node install-train serve run eval train smoke test clean reset-model

help:
	@echo "Targets:"
	@echo "  install       Install Python and Node deps"
	@echo "  install-train Install SFT/DPO training deps (peft, trl, bitsandbytes)"
	@echo "  serve         Start llama.cpp server with the local LFM2.5 model"
	@echo "  run           Start the Streamlit demo"
	@echo "  eval          Run the offline eval suite against the local model"
	@echo "  test          Run the mocked unit tests (no LFM server needed)"
	@echo "  train         SFT + DPO LoRA training"
	@echo "  build-data    Rebuild training data from Pi session logs"
	@echo "  smoke         End-to-end smoke (mock Pi, no LFM server)"
	@echo "  clean         Remove caches and training outputs"
	@echo "  reset-model   Remove the local LFM model file"

install: install-py install-node
install-py:
	@if command -v $(UV) >/dev/null 2>&1; then \
		$(UV) venv .venv --python 3.12; \
		$(UV) pip install -r requirements.txt; \
	else \
		$(PY) -m venv .venv; \
		.venv/Scripts/python.exe -m pip install -r requirements.txt; \
	fi
install-node:
	@command -v npm >/dev/null 2>&1 || { echo "npm is required"; exit 1; }
	@if [ ! -x node_modules/.bin/pi ]; then \
		echo "Installing Node deps..."; \
		npm install --no-audit --no-fund; \
	else \
		echo "node_modules already present"; \
	fi
install-train:
	@if command -v $(UV) >/dev/null 2>&1; then \
		$(UV) pip install -r requirements-train.txt; \
	else \
		.venv/Scripts/python.exe -m pip install -r requirements-train.txt; \
	fi

serve:
	@bash scripts/start_lfm25_server.sh

run:
	@.venv/Scripts/python.exe -m streamlit run app.py --server.port $(STREAMLIT_PORT)

eval:
	@.venv/Scripts/python.exe scripts/eval_agent_p.py

test:
	@.venv/Scripts/python.exe tests/test_eval_with_mock.py

train:
	@.venv/Scripts/python.exe scripts/train_lora.py --base-model LiquidAI/LFM2.5-1.2B-Instruct --use-4bit

build-data:
	@.venv/Scripts/python.exe scripts/build_agent_training_data.py

smoke:
	@.venv/Scripts/python.exe tests/test_eval_with_mock.py

clean:
	@find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@rm -rf training_data/lora_agent_p .pytest_cache

reset-model:
	@rm -f ../lfm2.5-1.2b-instruct-q4_k_m.gguf
