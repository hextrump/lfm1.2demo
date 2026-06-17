SHELL := /usr/bin/env bash

PY ?= python3
UV ?= uv
LLAMA_PORT ?= 8080
STREAMLIT_PORT ?= 8501

ifeq ($(OS),Windows_NT)
VENV_PY := .venv/Scripts/python.exe
else
VENV_PY := .venv/bin/python
endif

.PHONY: help install install-py install-node serve run test clean

help:
	@echo "Targets:"
	@echo "  install  Install Python and Node dependencies"
	@echo "  serve    Start llama.cpp server with LFM2.5 1.2B"
	@echo "  run      Start the Streamlit demo"
	@echo "  test     Run the mocked smoke test"
	@echo "  clean    Remove local caches"

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

run:
	@$(VENV_PY) -m streamlit run app.py --server.address 127.0.0.1 --server.port $(STREAMLIT_PORT)

test:
	@$(VENV_PY) tests/test_eval_with_mock.py

clean:
	@find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@rm -rf .pytest_cache
