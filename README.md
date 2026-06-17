# ERP / CRM / SSO Agent P Demo

Local enterprise support agent demo using:

- LFM2 1.2B Tool running locally through llama.cpp
- Pi agent runtime
- Simulated ERP / CRM / SSO tools
- Local enterprise knowledge search with ripgrep
- Streamlit web UI

The demo shows how a small local model can help users troubleshoot ERP login,
permission, license, Power BI, and support ticket workflows without sending
business data to an external API.

## Why the Tool variant

This demo uses [LiquidAI/LFM2-1.2B-Tool](https://huggingface.co/LiquidAI/LFM2-1.2B-Tool-GGUF)
(Q4_K_M quantisation, ~728 MB) rather than the pure-Instruct variant. The Tool
variant is fine-tuned for function/tool calling, which is the core of this
demo (Agent P must call `erp_get_current_error`, `kb_rg_search`,
`erp_create_ticket_from_current_error`, etc.). The 1.2B Instruct model is not
reliable at emitting tool calls for this workflow.

## Prerequisites

- Python 3.10+; Python 3.12 is recommended.
- Node.js 20+ and npm.
- `ripgrep` on PATH. Install with `sudo apt install ripgrep`, `brew install ripgrep`, or `winget install BurntSushi.ripgrep.MSVC`.
- `llama-server` from llama.cpp on PATH, or copied into this folder.
- About 2 GB free disk space for the GGUF model.

## Quickstart

```bash
cd demo1-final
make install
```

Start the local model server:

```bash
make serve
```

Start the Live Tail SSE server (powers the terminal-style feed above the chat):

```bash
make live-tail
```

In a second terminal, start the web demo:

```bash
make run
```

Open:

```text
http://127.0.0.1:8501
```

The **Live Tail Console** sits above the chat on the right side. It shows a
terminal-style feed of all agent activity (model / tool calls / args / KB
matches) interleaved with the underlying llama-server log, refreshing in
real time over Server-Sent Events.

## Local Model

By default, `make serve` looks for the model in:

```text
./lfm2-1.2b-tool-q4_k_m.gguf
./models/lfm2-1.2b-tool-q4_k_m.gguf
../lfm2-1.2b-tool-q4_k_m.gguf
```

If no local file is found, `llama-server` tries to download:

```text
LiquidAI/LFM2-1.2B-Tool-GGUF:Q4_K_M
```

You can also set a custom path:

```bash
cp .env.example .env
# edit LFM25_GGUF_PATH=/path/to/model.gguf
make serve
```

The `llama-server` is started with the following defaults (override in `.env`):

| Variable | Default | Notes |
|----------|---------|-------|
| `LLAMA_PORT` | `8080` | Port for the OpenAI-compatible API |
| `LLAMA_CTX` | `8192` | Context size; 8K balances speed and capacity for the 1.2B model |
| `LLAMA_SERVER_URL` | `http://127.0.0.1:8080` | URL Streamlit uses for the liveness check |

## Demo Flow

1. Open the Employee Portal page.
2. Select an application and error scenario.
3. Click sign in to generate a simulated ERP error.
4. Ask Agent P to inspect the current error or paste an error message into chat.
5. Ask Agent P to contact IT and create a ticket.
6. Open IT Operations to see the ticket handoff.

Useful prompts:

```text
今出ているエラーを確認して
社内規程も検索して
まだ解決しないのでITに連絡してチケットを作成してください
```

Pasted error example:

```text
Sign-in failed
Additional authentication required
Error Code: AADSTS50076
Trace ID: trc-aadsts50076-demo
Correlation ID: corr-demo
```

## Smoke Test

The smoke test uses a mocked Pi runtime, so it does not need a running model:

```bash
make test
```

## Project Layout

```text
demo1-final/
├── app.py
├── runtime/                  Pi Agent P wrapper and ERP tool extension
├── .pi/skills/erp-support/   Pi skill instructions
├── .pi-agent/                local Pi provider settings
├── erp_state/                simulated ERP page state
├── knowledge/                local enterprise policy knowledge base
├── scripts/                  model server startup helper
├── tests/                    mocked smoke test
├── requirements.txt
├── package.json
└── Makefile
```

## Architecture

```text
Streamlit (app.py, port 8501)
    │
    │ subprocess + JSON protocol
    ▼
Pi CLI (node_modules/.bin/pi)
    │
    │ reads .pi-agent/models.json (local-lfm provider)
    ▼
llama-server (llama.cpp, port 8080)
    │
    ▼
LFM2-1.2B-Tool Q4_K_M GGUF
```

The Streamlit UI talks to the **Pi CLI** (a Node.js process), not directly to
llama-server. Pi then forwards chat completion requests to the local llama-server
using the OpenAI-compatible `/v1/chat/completions` endpoint. The `app.py`
liveness check (`/health`) also goes directly to llama-server on port 8080.

## Notes

- The demo runs locally. The LFM model endpoint is expected at `127.0.0.1:8080`.
- All ERP tools are **simulated**. High-risk actions such as MFA disablement,
  permission grants, and Conditional Access changes are intentionally blocked
  in `runtime/pi_erp_extension.ts`.
- The full audit trail of every Pi session is written to
  `.pi-agent/sessions/<project>/<timestamp>.jsonl`.

## License

MIT. See `LICENSE`.
