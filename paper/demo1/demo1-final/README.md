# ERP / CRM / SSO Agent P Demo

Local enterprise support agent demo using:

- LFM2.5 1.2B Instruct running locally through llama.cpp
- Pi agent runtime
- Simulated ERP / CRM / SSO tools
- Local enterprise knowledge search with ripgrep
- Streamlit web UI

The demo shows how a small local model can help users troubleshoot ERP login,
permission, license, Power BI, and support ticket workflows without sending
business data to an external API.

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

In a second terminal, start the web demo:

```bash
make run
```

Open:

```text
http://127.0.0.1:8501
```

## Local Model

By default, `make serve` looks for the model in:

```text
./lfm2.5-1.2b-instruct-q4_k_m.gguf
./models/lfm2.5-1.2b-instruct-q4_k_m.gguf
../lfm2.5-1.2b-instruct-q4_k_m.gguf
```

If no local file is found, `llama-server` tries to download:

```text
LiquidAI/LFM2.5-1.2B-Instruct-GGUF:Q4_K_M
```

You can also set a custom path:

```bash
cp .env.example .env
# edit LFM25_GGUF_PATH=/path/to/model.gguf
make serve
```

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

## Notes

- The demo runs locally. The LFM model endpoint is expected at `127.0.0.1:8080`.
- Pi connects to the local model through `127.0.0.1:7878`; the Python wrapper
  sets the Pi runtime directory automatically.
- The ERP tools are simulated. High-risk actions such as MFA disablement,
  permission grants, and Conditional Access changes are intentionally blocked.

## License

MIT. See `LICENSE`.
