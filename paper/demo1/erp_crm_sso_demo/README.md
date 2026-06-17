# ERP / CRM / SSO Agent P Demo

社内 IT 一次切り分け AI Agent P。ローカル LFM 2.5 1.2B Instruct + Pi agent runtime
+ 模拟 ERP 工具链 + ripgrep 企业知识库检索 + ticket 创建/移交。

Designed to demonstrate that a 1.2B local model can act as a general enterprise
agent: read user intent, pick the right ERP tool, search local policy, create
tickets, and refuse high-risk admin actions — all without leaving the host.

## Quickstart (Windows / WSL / Linux / macOS)

```bash
# 1. clone and enter
git clone https://github.com/hextrump/lfm1.2demo.git
cd lfm1.2demo
git checkout demo1-clean
cd paper/demo1/erp_crm_sso_demo

# 2. install Python + Node deps (uses uv if installed, else venv + pip)
make install

# 3. start the local LFM2.5 server (port 8080)
#    If lfm2.5-1.2b-instruct-q4_k_m.gguf is not in the repo root,
#    llama-server will download it from Hugging Face.
make serve &

# 4. in a second terminal, run the demo
make run
# -> http://localhost:8501
```

If you only want to validate the install without a real LFM server, run:

```bash
make test        # mocked Pi runtime, 14/14 expected pass
make smoke       # alias for `make test`
```

## Pages

- **Employee Portal** — Simulated Dynamics 365 / Salesforce / Power BI login
  screen. Pick a scenario (AADSTS50076, AADSTS50105, license missing, MFA
  exception, …) and ask Agent P through the chat box.
- **IT Operations** — Tickets that Agent P created and handed off.
- **Knowledge Search** — `ripgrep` over the local `knowledge/` directory.
- **Audit Log** — Every chat, tool call, and ticket handoff.

## Architecture

```text
Streamlit (app.py)
  - simulates ERP web UI
  - writes erp_state/current_error.json
  - sends user chat to Pi Agent P via JSON mode
        |
        v
Pi Agent P (runtime/pi_agent.py)
  - local-lfm provider (llama.cpp)
  - LFM2.5-1.2B-Instruct
  - skill: .pi/skills/erp-support/SKILL.md
  - extension: runtime/pi_erp_extension.ts
        |
        v
ERP / MCP-like tools (TypeScript)
  - erp_get_current_error            read active ERP error
  - erp_inspect_current_error_with_kb read + KB lookup
  - erp_analyze_pasted_error_with_kb  classify pasted error
  - erp_query_state                  structured business state
  - kb_rg_search / kb_read_knowledge local policy search
  - erp_draft_ticket                 build a ticket draft
  - erp_create_ticket                commit a ticket
  - erp_create_ticket_from_current_error end-to-end ticket
  - erp_handoff_to_it_agent          send to IT-side agent
  - erp_execute_admin_action         low-risk actions only
```

The Python agent layer enforces a **tool profile** per prompt:

- Greeting / date — `--no-tools`, direct reply.
- Pasted ERP/SSO/CRM error — only `erp_analyze_pasted_error_with_kb`.
- Current page error — `erp_get_current_error` + KB tools.
- Explicit IT / ticket request — `erp_create_ticket_from_current_error`.
- File / code / shell — built-in Pi tools enabled.

This is a runtime-level permission guard, not a Python-side classifier. The
local model still decides whether to call the tool.

## Demo flow

1. Open the Employee Portal.
2. Pick `Dynamics 365` and scenario `AADSTS50076` (SSO / MFA login failure).
3. Click `Sign in` to push the error into the simulated ERP page.
4. Type into the chat box:
   - `今出ているエラーを確認して` — Agent P reads the current error.
   - `社内規程も検索して` — Agent P searches the local KB.
   - `まだ解決しないのでITに連絡してチケットを作成してください` — Agent P
     creates a ticket and hands it off to IT Operations.
5. Switch to **IT Operations** to see the new ticket.
6. Switch to **Audit Log** to see the full decision trace.

## Eval and fine-tuning

The full eval suite runs 14 representative cases against the local model:

```bash
make eval
# 2026-06-17 baseline
#   PASS smalltalk_date_no_tools
#   PASS smalltalk_greeting_no_tools
#   PASS pasted_sso_error_analyze_only
#   PASS pasted_sso_error_japanese_analyze_only
#   PASS pasted_salesforce_error_analyze_only
#   PASS current_error_fetch
#   PASS current_error_with_policy_lookup
#   PASS ticket_request_create_ticket
#   PASS ticket_request_english
#   PASS ticket_request_escalation
#   PASS vendor_mfa_no_disable
#   PASS multi_user_outage_collect
#   PASS powerbi_denial_analyze
#   PASS crm_menu_missing_analyze
```

The mocked unit tests use `tests/mock_pi.py` and a stub `subprocess.run` so
they run in seconds without an LFM server:

```bash
make test
# 14/14 pass on ok mode
# 14/14 pass on silent mode (fallback rescue)
# 2/14 pass on wrong mode (model hallucination; needs DPO)
```

To fine-tune the LFM2.5 base on collected session logs:

```bash
make install-train     # peft, trl, bitsandbytes
make build-data        # writes training_data/{sft,dpo}.jsonl
make train             # SFT then DPO, LoRA + 4-bit quant
# adapter saved to training_data/lora_agent_p/{sft,dpo}/
```

## Project layout

```text
erp_crm_sso_demo/
├── Makefile
├── README.md
├── LICENSE
├── .env.example
├── .gitignore
├── requirements.txt
├── requirements-train.txt
├── package.json
├── app.py                              Streamlit UI
├── runtime/
│   ├── __init__.py
│   └── pi_agent.py                     Pi-first runtime
├── .pi/
│   └── skills/erp-support/SKILL.md     Pi skill description
├── .pi-agent/
│   ├── models.json                     local-lfm provider config
│   └── settings.json                   Pi default model + provider
├── erp_state/
│   └── current_error.json              simulated ERP page state
├── knowledge/
│   ├── sso/entra-id-login-errors.md
│   ├── erp_crm/dynamics-salesforce-permissions.md
│   ├── powerbi/workspace-report-permissions.md
│   ├── security/mfa-exception-vendor-policy.md
│   └── helpdesk/ticket-routing-priority-matrix.md
├── scripts/
│   ├── start_lfm25_server.sh
│   ├── build_agent_training_data.py
│   ├── train_lora.py
│   └── eval_agent_p.py
├── tests/
│   ├── mock_pi.py
│   └── test_eval_with_mock.py
├── training_data/
│   ├── README.md
│   ├── agent_p_sft.jsonl               (small seed, see README)
│   └── agent_p_dpo.jsonl               (small seed, see README)
└── runtime/pi_erp_extension.ts         ERP / MCP-like tools
```

## Prerequisites

- Python 3.10+ (3.12 recommended; `uv` is optional but speeds up install).
- Node 20+ and npm.
- `ripgrep` (`rg`) on `$PATH` for the local KB search.
- ~2 GB free disk for `lfm2.5-1.2b-instruct-q4_k_m.gguf`.
- For fine-tuning: CUDA-capable GPU with 8 GB+ VRAM (QLoRA on 4-bit
  fits on a single RTX 3060/4060).

## Known setup notes

- On a Windows host, the `pi` binary lives in `node_modules/.bin/pi`. If you
  see `Input/output error` on that path, delete `node_modules` and re-run
  `npm install`. The symlinks can be corrupted by tools that walk the
  filesystem across the WSL boundary.
- The first `make serve` invocation may take a few minutes while
  `llama-server` downloads the GGUF model from
  `LiquidAI/LFM2.5-1.2B-Instruct-GGUF:Q4_K_M` if no local copy is present.
- The `pi` runtime expects `PI_CODING_AGENT_DIR` to point at
  `.pi-agent/`. The Python wrapper sets this automatically.

## License

MIT. See `LICENSE`.
