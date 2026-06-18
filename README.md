# ERP / CRM / SSO Agent P Demo

> **社内サポート AI デモ** — ローカル LLM のみで動く、ERP / CRM / SSO 問い合わせ対応エージェント。
> データは一切社外に出ません。

LFM2 1.2B Tool(ローカル) + Pi agent runtime + 模擬 ERP ツール + ripgrep ナレッジ検索 + Streamlit UI で、ERP ログイン、権限、ライセンス、Power BI などの社内サポートを**完全オフライン**で実行するデモです。

---

## 📖 目次

1. [設計思想](#設計思想)
2. [アーキテクチャ](#アーキテクチャ)
3. [データフロー](#データフロー)
4. [ユースケース](#ユースケース)
5. [コンポーネント](#コンポーネント)
6. [セットアップ](#セットアップ)
7. [使い方](#使い方)
8. [テスト](#テスト)
9. [制限事項](#制限事項)
10. [ライセンス](#ライセンス)

---

## 🎯 設計思想

| 原則 | 実装 |
|------|------|
| **完全ローカル** | すべての推論・データ・KB を社内で完結。外部 API なし |
| **小型モデルで実用** | 1.2B パラメータでもツール呼び出しが安定する設計 |
| **可視化** | Live Tail Console で「何が起きているか」をリアルタイム表示 |
| **誤動作への防御** | 1.2B は弱いので、ハルシネーション防止層を Python 側で実装 |
| **運用ログ** | 全アクション・全会話を `.pi-agent/sessions/` に記録(監査対応) |
| **テスト可能** | 95 件の pytest(unit / runtime / UI) |

---

## 🏗️ アーキテクチャ

### 全体構成

```
┌────────────────────────────────────────────────────────────────────────────────────┐
│                              👤  End User (Browser)                                  │
│                                                                                    │
│   ┌──────────────────────────┐  ┌──────────────────────────┐  ┌────────────────┐  │
│   │  Employee Portal (Streamlit) │  IT Operations Console        │  │  Audit Log │  │
│   │  ────────────────────    │  ─────────────────────        │  │ ─────────── │  │
│   │  • Sign in (8 シナリオ)    │  • Ticket 一覧                │  │  • 全操作履歴 │  │
│   │  • Agent P チャット        │  • チケット詳細                │  │  • 引き継ぎ   │  │
│   │  • ナレッジ KB 検索       │  • IT Agent P チャット          │  │  • 状態遷移   │  │
│   │  • チケット作成         │  • 6 種のアクション実行      │  │               │  │
│   └────────────┬─────────────┘  └────────────┬─────────────┘  └────────────────┘  │
│                │                          ▲                                    │
│   ┌────────────┴──────────────────────────┴────────────────────────────┐       │
│   │            🪟  Live Tail Console (SSE :8765)                          │       │
│   │  ────────────────────────────────────────────────────────────────    │       │
│   │  agent activity + llama-server events をリアルタイム表示               │       │
│   │  「今モデルが何を考えてるか」を可視化                                    │       │
│   └──────────────────────────────────────────────────────────────────┘       │
└────────────────────────────────────┬───────────────────────────────────────────┘
                                     │ HTTPS / SSE
                                     ▼
┌────────────────────────────────────────────────────────────────────────────────────┐
│                    🐍  Python Application Layer  (app.py)                       │
│   ┌─────────────────────────────────────────────────────────────────────┐      │
│   │                    Streamlit Web Server (:8501)                       │      │
│   └─────────────────┬─────────────────────────────────┬─────────────────┘      │
│                     │                                 │                      │
│   ┌─────────────────▼──────────────┐   ┌─────────────▼─────────────────┐      │
│   │  Agent P  (Employee side)        │   │  IT Operations Agent P        │      │
│   │  runtime/pi_agent.py            │   │  runtime/pi_agent.py          │      │
│   │  ──────────────────────────    │   │  chat_it()                    │      │
│   │  •  identity guard (no model)  │   │  •  erp_it_list / get         │      │
│   │  •  code-level followup        │   │  •  erp_it_resolve / close    │      │
│   │  •  code-level ticket create   │   │  •  erp_it_reassign / comment │      │
│   │  •  code-level recommendations │   │  •  status transitions        │      │
│   └──────┬───────────────┬─────────┘   └─────────────┬─────────────────┘      │
│          │ subprocess    │ JSON                    │ subprocess                 │
│          │ OpenAI API    ▼                          ▼ OpenAI API                 │
└──────────┼──────────────────────────────────────────────────────────────────────┘
           │
           ▼
┌────────────────────────────────────────────────────────────────────────────────────┐
│                    🟢  Pi CLI  (Node.js, offline mode)                            │
│   ┌──────────────────────────────────────────────────────────────────────┐       │
│   │   .pi/skills/erp-support/SKILL.md   ←─── Agent behavior rules          │       │
│   │   .pi/skills/it-support/SKILL.md    ←─── IT Agent behavior rules      │       │
│   │   --append-system-prompt (per persona)                                  │       │
│   │   --tools (filtered list per profile)                                   │       │
│   └──────────────────┬───────────────────────────────────────────────────┘       │
│                      │ OpenAI-compatible HTTP                                    │
└──────────────────────┼─────────────────────────────────────────────────────────┘
                       ▼
┌────────────────────────────────────────────────────────────────────────────────────┐
│                       🤖  LLM Layer  (model serving)                              │
│   ┌──────────────────────────────────────────────────────────────────────┐       │
│   │                llama-server  (llama.cpp)                              │       │
│   │                127.0.0.1:8080   OpenAI-compatible API                  │       │
│   │                                                                       │       │
│   │   📦  LFM2-1.2B-Tool  Q4_K_M  GGUF  (~728 MB, 1.17B params)         │       │
│   │       context: 8192 tokens   /   CPU inference:  AMD Ryzen 7 (8c/16t)  │       │
│   └──────────────────────────────────────────────────────────────────────┘       │
└────────────────────────────────────────────────────────────────────────────────────┘
                       │
                       ▼
┌────────────────────────────────────────────────────────────────────────────────────┐
│                          💾  Data Layer                                          │
│   ┌──────────────────────────┐  ┌──────────────────────────┐  ┌───────────────┐     │
│   │  erp_state/                │  │  knowledge/                 │  │  .pi-agent/  │     │
│   │  ┌──────────────────────┐ │  │  ┌──────────────────────┐│  │  ┌────────┐ │     │
│   │  │current_error.json   │ │  │  │entra-id-            ││  │  │models  │ │     │
│   │  │(active error)       │ │  │  │ login-errors.md    ││  │  │.json   │ │     │
│   │  └──────────────────────┘ │  │  ├──────────────────────┤│  │  ├────────┤ │     │
│   │  ┌──────────────────────┐ │  │  │dynamics-            ││  │  │settings│ │     │
│   │  │tickets.json          │ │  │  │salesforce-         ││  │  │.json   │ │     │
│   │  │(IT チケット store)  │ │  │  │permissions.md      ││  │  └────────┘ │     │
│   │  └──────────────────────┘ │  │  ├──────────────────────┤│  │               │     │
│   │                            │  │  │mfa-exception-     ││  │  sessions/   │     │
│   │  /tmp/demo1_live_tail.log  │  │  │vendor-policy.md   ││  │  *.jsonl     │     │
│   │  (Live Tail event ストリーム)│  │  ├──────────────────────┤│  │  (監査ログ)  │     │
│   │                            │  │  │powerbi-...         ││  │               │     │
│   │                            │  │  │ticket-routing-... ││  │               │     │
│   │                            │  │  └──────────────────────┘│  │               │     │
│   └──────────────────────────┘  └──────────────────────────┘  └───────────────┘     │
└────────────────────────────────────────────────────────────────────────────────────┘
```

### レイヤー責務

| レイヤー | 責務 | ポート / 場所 |
|---------|------|---------------|
| **UI 層** | ユーザー操作・結果表示・リアルタイム可視化 | Streamlit :8501, SSE :8765 |
| **Agent 層** | 自然言語理解・ツール選択・ペルソナ切替 | Python `runtime/pi_agent.py` |
| **Pi CLI 層** | モデル実行・JSON イベントストリーム | Node.js subprocess |
| **LLM 層** | 推論・テキスト生成 | llama-server :8080 |
| **Data 層** | 状態・ナレッジ・監査ログ | `erp_state/`, `knowledge/`, `.pi-agent/` |

---

## 🌊 データフロー

### ユースケース 1: 従業員が Agent P にエラー診断をもとめる

```
👤 User: 「今出ているエラーを確認して」
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│ Streamlit  (app.py:1599)                                    │
│  chat_input 受信 → run_employee_chat_live()                 │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│ Agent P  (runtime/pi_agent.py:108)                          │
│                                                              │
│  1. identity guard  → スキップ (ERP 質問)                    │
│  2. chat() 呼び出し                                          │
│     ├─ _tool_profile() = "erp_current_error"                  │
│     ├─ _run_pi() subprocess → `pi` CLI                      │
│     │     args: --skill erp-support, --tools erp_*           │
│     │           --append-system-prompt "<AGENT_P_RULES>"     │
│     │           -p "今出ているエラーを確認して"              │
│     │                                                        │
│     │  [Pi CLI] llama-server に POST /v1/chat/completions │
│     │            ← 1.2B Tool が erp_get_current_error を呼ぶ │
│     │            ← JSON event stream で tool 結果を返す     │
│     │                                                        │
│     ├─ 結果解析:                                              │
│     │   events: [erp_get_current_error/start, /ok]          │
│     │   reply:   "<モデルの日本語要約>"                      │
│     │                                                        │
│     └─ _ensure_followup_questions()  ◀── Python 層ガード │
│           ├─ _is_mostly_english(reply)?                     │
│           │   YES → 1 回だけ re-prompt                      │
│           ├─ 構造チェック: 質問 + 推奨 ある?                  │
│           │   YES → スキップ                                 │
│           └─ NO  → 構造化ブロックを append                  │
│                「追加でお聞きしたいこと」+「推奨される次のステップ」│
│                                                              │
│  3.  result.reply を return                                │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│ Streamlit                                                    │
│  render_chat_container(chat_placeholder, ...)               │
│  → chat bubble に reply 全文を一発で表示                    │
│  → Live Tail に emit_event_to_live_tail(reply.events)       │
│     → append_live_event() → /tmp/demo1_live_tail.log 追記 │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼ (SSE push, ~100ms 遅延)
┌─────────────────────────────────────────────────────────────┐
│ Live Tail SSE Server  (scripts/live_tail_server.py:8765)    │
│  tail -F /tmp/demo1_live_tail.log                           │
│  → data: [timestamp] [kind] text\n\n  を subscriber に送信   │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│ Browser: <iframe src="about:srcdoc">                        │
│   const es = new EventSource("http://127.0.0.1:8765/sse?…")│
│   es.onmessage = (e) => appendLine(e.data)                  │
│   → 11 行のタイムラインがリアルタイム表示                    │
└─────────────────────────────────────────────────────────────┘
```

### ユースケース 2: 従業員が「チケットで依頼して」と言う

```
👤 User: 「チケットで依頼して」
         │
         ▼
[Streamlit] run_employee_chat_live()
         │
         ▼
[Agent P] chat()  ───┐
                    │  モデルが erp_create_ticket_from_current_error を
                    │  呼んだかどうかチェック
                    ▼
        result.ticket is None ???
            │                  │
           YES                NO (モデルが呼んだ)
            │                  │
            ▼                  └→ 結果をそのまま return
[Code-level guard]
_create_ticket_directly(user_text)
  ├─ read erp_state/current_error.json
  ├─ lookup SCENARIOS[key] for risk/priority/route
  ├─ ripgrep KB → top 5 evidence
  ├─ generate ticket_id: KW-#### (TS hash algo と同じ)
  └─ return PiAgentResult(ticket=..., reply="**IT チケットを...")
            │
            ▼
[Streamlit] persist_agent_result()
  ├─ st.session_state.tickets.append(ticket)
  └─ persist_tickets_to_disk() → erp_state/tickets.json
```

### ユースケース 3: IT オペレーターが IT Agent でチケットを解決

```
👷 IT Op: 「KW-1234 を MFA 再設定で対応したので解決マークして」
         │
         ▼
[Streamlit] IT Operations ページ → IT Agent チャット
         │
         ▼
[IT Operations Agent P] chat_it()
  system prompt: 「ACT, don't punt. 必ず erp_it_* tool を呼べ」
  skill: .pi/skills/it-support/SKILL.md
  tools: erp_it_list / get / triage / resolve / close / reassign / add_comment
         │
         ▼
[Pi CLI] モデルが erp_it_get_ticket を呼び、現在状態を確認
         │
         ▼
[Pi CLI] モデルが erp_it_resolve_ticket を呼ぶ
         args: { ticket_id: "KW-1234", resolution_note: "MFA 再設定で対応" }
         │
         ▼
[TS Tool] updateTicketInStore() → tickets.json 書き換え
  ticket.status = "Resolved"
  ticket.resolution_note = "MFA 再設定で対応"
  ticket.history.push({ at, action: "resolved", note })
         │
         ▼
[Streamlit] persist_tickets_to_disk()
  st.rerun() → IT Operations ページで status 表示が "Resolved" に
```

---

## 💼 ユースケース

| シナリオ | ユーザー入力例 | Agent 動作 |
|---------|-------------|-----------|
| **A: ログイン失敗** | `今出ているエラーを確認して` | erp_get_current_error → MFA 通知承認を推奨 |
| **B: アプリ割り当て** | `AADSTS50105 で入れない` | erp_get_current_error → アクセス申請フォーム案内 |
| **C: ライセンス不足** | `Dynamics 365 が使えない` | ライセンス申請・上長承認のフロー案内 |
| **D: Conditional Access ブロック** | `自宅 PC から繋げない` | VPN 接続・会社支給端末利用を案内 |
| **E: CRM メニュー非表示** | `Sales Hub が見えない` | role / Business Unit 確認、CRM Owner 連絡を推奨 |
| **F: Power BI アクセス拒否** | `レポートが見えない` | workspace 権限確認、BI 管理者を案内 |
| **G: 障害(複数ユーザー)** | `チーム全員使えない` | P2 エスカレーション、IT Ops 連絡 |
| **H: ベンダー MFA 例外** | `外部委託先が MFA 失敗` | Security Team レビュー依頼 |

---

## 🧩 コンポーネント

| ファイル | 役割 |
|--------|------|
| `app.py` (1702 lines) | Streamlit UI、チャット、Live Tail 描画、ページ遷移 |
| `runtime/pi_agent.py` | Pi subprocess ラッパ、ペルソナ切替、コード層ガード |
| `runtime/pi_erp_extension.ts` | 13 個のツール(従業員 6 + IT 7) |
| `scripts/live_tail_server.py` | SSE サーバ(stdlib only,~190 行) |
| `scripts/start_lfm25_server.sh` | llama.cpp 起動スクリプト |
| `.pi/skills/erp-support/SKILL.md` | 従業員ペルソナの行動ルール |
| `.pi/skills/it-support/SKILL.md` | IT ペルソナの行動ルール |
| `.pi-agent/models.json` | OpenAI-compatible provider 設定 |
| `tests/` (95 tests) | unit / runtime / UI の 3 層 pytest |

### コード層ガード(1.2B モデルが弱いため)

| 機能 | 場所 | 役割 |
|------|------|------|
| **identity guard** | `_direct_basic_reply()` | モデル呼出し前に identity/capability/date/greeting を返す |
| **structured followup** | `_ensure_followup_questions()` | 必ず「追加でお聞きしたいこと」+「推奨される次のステップ」ブロックを append |
| **language re-prompt** | `chat()` 内 | モデル返答が英語ばかりなら 1 回だけ日本語強制再生成 |
| **no hallucination ticket** | `_create_ticket_directly()` | モデルが ticket を捏造した場合、Python 側で current_error.json + KB から真の KW-#### を生成 |
| **server log coalesce** | `drain_server_log_to_timeline()` | n_decoded の連続イベントを 1 行に集約 |
| **reset on new turn** | `chat()` 先頭 | `server_log_pos` をファイル末尾にリセット、過去のログが混ざらないように |

---

## 🛠️ セットアップ

### 前提条件

- Python 3.10+(3.12 推奨)
- Node.js 20+, npm
- `ripgrep`(`apt install ripgrep` / `brew install ripgrep`)
- `llama-server`(このフォルダに同梱)
- 空き容量 約 2 GB(GGUF モデル用)

### インストール

```bash
cd demo1-final
make install         # Python + Node 依存
make serve          # llama-server 起動
make live-tail      # SSE サーバ(:8765)
make run            # Streamlit(:8501)→  http://127.0.0.1:8501
```

### モデル

[LFM2-1.2B-Tool](https://huggingface.co/LiquidAI/LFM2-1.2B-Tool-GGUF)(Q4_K_M, ~728 MB)を使用。Tool バリアントは**関数呼び出し専用**に fine-tune されており、Agent P の `erp_*` ツール呼び出しに必須です。Instruct バリアントではツール呼び出しが安定しません。

---

## 🚀 使い方

### 1. シナリオ選択 → Sign in

Employee Portal ページで:
- 「Inquiry scenario」ドロップダウンから 8 種類のエラー(SSO / Power BI / ライセンス…)を選択
- `Sign in` ボタンで模擬 ERP エラーを生成
- `current_error.json` に書き込まれる

### 2. Agent P に質問

チャット欄(右側)に入力:
```
今出ているエラーを確認して
社内規程も検索して
まだ解決しないのでITに連絡してチケットを作成してください
```

### 3. IT 部門が対応

左メニューから **IT Operations** に切替:
- チケット一覧
- IT Agent チャット:`KW-1234 を解決`、`Closed にアーカイブ`、`CRM チームに再分派` など
- 全アクションは即時 `erp_state/tickets.json` に永続化

---

## 🧪 テスト

```bash
make test-unit    # 56 tests, < 1s,  サービス不要
make test-runtime # 33 tests, ~8min, llama-server 必要
make test-ui      #  6 tests, ~2min, Streamlit + llama 必要
make test-all     # 95 tests, ~9min, HTML レポート生成
```

`tests/reports/report.html` に HTML レポートが出力されます。

---

## ⚠️ 制限事項

- **1.2B モデル**のため、出力は時々不正確。**コード層ガード**で補完しています
- 高リスク操作(MFA 無効化、ライセンス付与、Conditional Access 変更)は**意図的にブロック**(`pi_erp_extension.ts`)
- すべて**シミュレーション** — 実 ERP には接続しません
- 監査ログは `.pi-agent/sessions/<project>/<timestamp>.jsonl` に JSON Lines 形式で記録

---

## 📄 ライセンス

MIT。`LICENSE` を参照。
