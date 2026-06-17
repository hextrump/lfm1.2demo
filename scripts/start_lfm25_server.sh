#!/usr/bin/env bash
# Start llama.cpp server with LFM2 1.2B Tool (Q4_K_M).
# This is the Tool variant — chosen over the Instruct variant because Agent P
# relies on reliable function/tool calling from a 1.2B model.

set -euo pipefail

DEMO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PORT="${LLAMA_PORT:-8080}"
CTX_SIZE="${LLAMA_CTX:-8192}"
MODEL_ALIAS="lfm2-1.2b-tool-q4_k_m.gguf"

if [ -f "${DEMO_DIR}/.env" ]; then
  set -a
  # shellcheck disable=SC1091
  source "${DEMO_DIR}/.env"
  set +a
fi

LLAMA_SERVER="${LLAMA_SERVER:-${DEMO_DIR}/llama-server}"
if [ ! -x "${LLAMA_SERVER}" ]; then
  if command -v llama-server >/dev/null 2>&1; then
    LLAMA_SERVER="$(command -v llama-server)"
  else
    echo "llama-server not found. Set LLAMA_SERVER in .env or put the binary in demo1-final/." >&2
    exit 1
  fi
fi

if [ -n "${LFM25_GGUF_PATH:-}" ] && [ -f "${LFM25_GGUF_PATH}" ]; then
  MODEL_FILE="${LFM25_GGUF_PATH}"
else
  for candidate in \
    "${DEMO_DIR}/lfm2-1.2b-tool-q4_k_m.gguf" \
    "${DEMO_DIR}/models/lfm2-1.2b-tool-q4_k_m.gguf" \
    "${DEMO_DIR}/../lfm2-1.2b-tool-q4_k_m.gguf"; do
    if [ -f "${candidate}" ]; then
      MODEL_FILE="${candidate}"
      break
    fi
  done
fi

if pgrep -f "llama-server.*--port ${PORT}" >/dev/null 2>&1; then
  echo "llama-server already listening on ${PORT}, reusing it"
  exit 0
fi

if [ -n "${MODEL_FILE:-}" ] && [ -f "${MODEL_FILE}" ]; then
  echo "Starting llama-server with local model: ${MODEL_FILE}"
  exec "${LLAMA_SERVER}" -m "${MODEL_FILE}" --host 127.0.0.1 --port "${PORT}" -c "${CTX_SIZE}" --alias "${MODEL_ALIAS}"
fi

echo "No local GGUF found. Downloading from Hugging Face..."
exec "${LLAMA_SERVER}" \
  -hf "LiquidAI/LFM2-1.2B-Tool-GGUF:Q4_K_M" \
  --host 127.0.0.1 \
  --port "${PORT}" \
  -c "${CTX_SIZE}" \
  --alias "${MODEL_ALIAS}"
