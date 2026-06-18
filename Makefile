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

.PHONY: help install install-py install-node serve live-tail run test test-unit test-runtime test-ui test-all clean

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
