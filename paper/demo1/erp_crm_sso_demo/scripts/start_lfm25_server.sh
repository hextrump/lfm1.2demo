#!/usr/bin/env bash
# Start llama.cpp server with the local LFM2.5 1.2B Instruct model.
#
# Looks for the GGUF in this order:
#   1. $LFM25_GGUF_PATH env var (or .env LFM25_GGUF_PATH)
#   2. ../lfm2.5-1.2b-instruct-q4_k_m.gguf (repo root)
#   3. ./lfm2.5-1.2b-instruct-q4_k_m.gguf
#   4. ./models/lfm2.5-1.2b-instruct-q4_k_m.gguf
# Falls back to a Hugging Face download if no local copy is found.

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../../.." && pwd)"
LLAMA_SERVER="${LLAMA_SERVER:-${ROOT_DIR}/llama-server}"
PORT="${LLAMA_PORT:-8080}"
CTX_SIZE="${LLAMA_CTX:-32768}"
MODEL_ALIAS="lfm2.5-1.2b-instruct-q4_k_m.gguf"

if [ -z "${LLAMA_SERVER:-}" ] || [ ! -x "${LLAMA_SERVER}" ]; then
  if command -v llama-server >/dev/null 2>&1; then
    LLAMA_SERVER="$(command -v llama-server)"
  else
    echo "llama-server not found. Set LLAMA_SERVER or put the binary in ${ROOT_DIR}." >&2
    exit 1
  fi
fi

if [ -n "${LFM25_GGUF_PATH:-}" ] && [ -f "${LFM25_GGUF_PATH}" ]; then
  MODEL_FILE="${LFM25_GGUF_PATH}"
else
  for candidate in \
    "${ROOT_DIR}/lfm2.5-1.2b-instruct-q4_k_m.gguf" \
    "./lfm2.5-1.2b-instruct-q4_k_m.gguf" \
    "./models/lfm2.5-1.2b-instruct-q4_k_m.gguf"; do
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
  -hf "LiquidAI/LFM2.5-1.2B-Instruct-GGUF:Q4_K_M" \
  --host 127.0.0.1 \
  --port "${PORT}" \
  -c "${CTX_SIZE}" \
  --alias "${MODEL_ALIAS}"
