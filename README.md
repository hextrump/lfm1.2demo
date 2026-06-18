# ERP / CRM / SSO Agent P Demo

> 社内サポート AI デモ。LFM2-1.2B Tool をローカルで動かし、ERP / CRM / SSO
> 問い合わせ対応 + IT チケット運用を**完全オフライン**で実行。

---

## アーキテクチャ

```
  ┌────────────────────────────────────────┐
  │  👤  Browser (Employee + IT + Audit)  │  ← UI Layer
  │  + 🪟   Live Tail Console (SSE :8765)  │
  └────────────────┬───────────────────────┘
                   ▼
  ┌────────────────────────────────────────┐
  │  🐍  Streamlit :8501                   │  ← App Layer
  │  ├─ Agent P (Employee side)            │
  │  └─ IT Operations Agent P              │
  └────────────────┬───────────────────────┘
                   ▼
  ┌────────────────────────────────────────┐
  │  🟢  Pi CLI  (Node.js, subprocess)     │  ← Agent Runtime
  │  skill: erp-support / it-support       │
  └────────────────┬───────────────────────┘
                   ▼ HTTP (OpenAI-compat)
  ┌────────────────────────────────────────┐
  │  🤖  llama-server :8080                │  ← LLM Layer
  │  LFM2-1.2B-Tool Q4_K_M  (1.17B params) │
  └────────────────┬───────────────────────┘
                   ▼
  ┌────────────────────────────────────────┐
  │  💾  Data Layer                         │
  │  erp_state/  knowledge/  .pi-agent/    │
  └────────────────────────────────────────┘
```

5 レイヤー:UI → App → Agent Runtime → LLM → Data。すべて社内で完結。

---

## クイックスタート

```bash
make install         # Python + Node 依存
make serve          # llama-server 起動(:8080)
make live-tail      # Live Tail SSE サーバ(:8765)
make run            # Streamlit(:8501) →  http://127.0.0.1:8501
```

## 使い方

1. **Employee Portal** でシナリオ選択 → Sign in
2. チャットで `今出ているエラーを確認して`
3. **IT Operations** で IT Agent が対応(`KW-#### を解決`)

## ファイル構成

```
app.py                          Streamlit UI
runtime/pi_agent.py             Pi ラッパ + コード層ガード
runtime/pi_erp_extension.ts     13 ツール(従業員 6 + IT 7)
scripts/live_tail_server.py     SSE サーバ
.pi/skills/{erp,it}-support/    Agent 行動ルール
erp_state/                      状態ファイル(current_error + tickets)
knowledge/                      社内規程 KB(5 docs)
tests/                          95 pytest(unit / runtime / UI)
```

## テスト

```bash
make test-unit    # 56 tests, < 1s
make test-runtime # 33 tests, ~8min  (要 llama-server)
make test-ui      #  6 tests, ~2min  (要 Streamlit)
make test-all     # 95 tests + HTML レポート
```

## 制限

- 1.2B モデルは時々不正確 → コード層ガード(followup / re-prompt / 真 ticket 生成)で補完
- 高リスク操作(MFA 無効化、ライセンス付与、Conditional Access 変更)は**意図的にブロック**
- すべてシミュレーション — 実 ERP には接続しない

## ライセンス

MIT
