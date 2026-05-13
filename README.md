# ローカルAI申請受付支援 Demo

Local AI Application Reception Assistant — LFM2-1.2B-Tool による申請内容解析・台帳データ管理

## 概要

日本の社内申請業務（申請受付・台帳登録）を、ローカルAIモデルで支援するDemoシステム。

**課題**: 30人の審査員が手動で申請を確認、不備チェック、台帳記載を行っている。
**目標**: ローカルAI + 2人の監督者で同じ業務を処理し、工数を大幅削減。

**重要**: 申請内容に個人情報・機密情報が含まれるため、外部API（OpenAI等）は使用不可。全処理をローカルで完結。

## アーキテクチャ

```
┌─────────────┐     ┌──────────────────┐     ┌────────────┐
│  React +     │────▶│  FastAPI Agent    │────▶│ llama.cpp  │
│  Vite UI     │◀────│  (Extract only)  │◀────│  server    │
│  :5174       │     │  (Score = Code)  │     │  :8080     │
└─────────────┘     └──────────────────┘     └────────────┘
```

- **llama.cpp server**: LFM2-1.2B-Tool Q4_K_M (731MB) を CPU で推論。フィールド抽出のみに使用
- **FastAPI Agent**: フィールド抽出はモデル、不備チェック・リスク評価・判定・台帳生成は全てプログラム（確定的スコアリング）
- **React UI**: 申請入力 → 結果表示 → 审核員確認 → 台帳データベース（CRUD）

## パイプライン設計

```
申請内容入力
    ↓
① フィールド抽出 (LLM tool calling + 正則フォールバック)
    ↓
② 不備チェック (プログラム: キーワード検出 + フィールド完全性スコア)
    ↓
③ リスク評価 (プログラム: 費用/不備/種別/明確度 4次元スコアリング)
    ↓
④ 受付判定 (プログラム: リスク + 不備 → 差戻/要確認/受付)
    ↓
⑤ 台帳データ生成 (プログラム: 全データ集約 + 信頼度スコア)
    ↓
审核員確認 → 台帳登録完了
```

**設計方針**: モデル（1.2B）は事実抽出にのみ使用。判断・評価は全て確定的プログラムで処理し、小モデルの不安定さに影響されない。

### スコアリング基準

**リスクスコア (0-9)**:
| 次元 | 0点 | 1-2点 | 3点 |
|------|-----|-------|-----|
| 費用 | <100万円 | 100-1000万円 | ≥1000万円 |
| 不備 | なし | 項目数に応じ | - |
| 種別 | 契約更新 | 設備変更/人事異動 | 予算申請 |
| 明確度 | 十分 | 簡略 | 不明確 |

合計 → 低(0-2) / 中(3-5) / 高(6+)

**判定ルール**:
- 高リスク → 差戻
- 不備あり → 要確認
- 中リスク・不備なし → 受付（審査員確認後）
- 低リスク・不備なし → 受付

## 使用モデル

| | |
|---|---|
| **モデル名** | LFM2-1.2B-Tool |
| **パラメータ数** | 1.17B |
| **量子化** | Q4_K_M (GGUF, 731MB) |
| **特徴** | Tool calling専用、非思考型、低遅延 |
| **用途** | フィールド抽出のみ（判定はプログラム） |
| **Context** | 32,768 tokens |
| **推奨推論** | greedy decoding (temperature=0) |
| **ダウンロード** | [HuggingFace](https://huggingface.co/LiquidAI/LFM2-1.2B-Tool-GGUF) |

## ディレクトリ構造

```
LFM1.2b/
├── app/
│   ├── server.py            # FastAPI — API endpoints, CORS, 台帳CRUD
│   ├── agent.py             # パイプライン: LLM抽出 + プログラム判定
│   ├── tools.py             # Tool Schema定義 + パーサー
│   ├── models.py            # llama-server管理 (起動/停止/健康確認)
│   └── frontend/            # React + Vite UI
│       ├── src/
│       │   ├── App.tsx      # メインUI (入力/結果/台帳テーブル/CRUD)
│       │   ├── api.ts       # FastAPI通信
│       │   ├── types.ts     # TypeScript型定義
│       │   └── index.css    # スタイリング
│       ├── vite.config.ts   # ポート5174 + APIプロキシ設定
│       └── package.json
├── data/
│   ├── sample_applications.jsonl   # 5シナリオの日本語サンプル申請
│   └── ledger_template.json        # 台帳フィールドテンプレート
├── pyproject.toml            # Python依存関係
├── Makefile                  # make install / server / frontend / dev
├── .env.example              # 環境変数テンプレート
└── .gitignore
```

**注意**: GGUFモデルファイル（731MB）とllama.cppバイナリはGitリポジトリに含まれません。下記の手順で別途ダウンロードしてください。

## セットアップ

### 前提条件

- Python 3.11+
- Node.js 18+
- llama.cppサーバー（CPU用）

### 1. リポジトリのクローン

```bash
git clone https://github.com/YOUR_USERNAME/LFM1.2b.git
cd LFM1.2b
```

### 2. モデルとllama.cppのダウンロード

```bash
# llama.cppのビルド（またはリリースからダウンロード）
# https://github.com/ggergan/llama.cpp/releases

# GGUFモデルのダウンロード
# https://huggingface.co/LiquidAI/LFM2-1.2B-Tool-GGUF から
# LFM2-1.2B-Tool-Q4_K_M.gguf をダウンロードしてプロジェクトルートに配置
```

### 3. Python依存関係のインストール

```bash
pip install -e .
```

### 4. Reactフロントエンドのインストール

```bash
cd app/frontend
npm install
```

### 5. llama-server の起動

```bash
cd /path/to/LFM1.2b
./llama-server -m lfm2-1.2b-tool-q4_k_m.gguf --host 0.0.0.0 --port 8080 -c 8192
```

起動確認:
```bash
curl http://localhost:8080/health
# → {"status":"ok"}
```

### 6. FastAPIサーバーの起動

```bash
cd /path/to/LFM1.2b
uvicorn app.server:app --port 5173 --reload
```

### 7. Reactフロントエンドの起動

```bash
cd app/frontend
npm run dev
```

ブラウザでアクセス: `http://localhost:5174`

## 使い方

1. ブラウザで `http://localhost:5174` を開く
2. **サンプル選択**ボタンで5つの日本語申請シナリオをロード、または手動でテキスト入力
3. **処理開始**ボタンをクリック
4. パイプラインが実行される（抽出→不備→リスク→判定→台帳）
5. **审核員確認**ボタンで台帳登録確定
6. 台帳データベーステーブルでCRUD操作（新規追加/編集/削除/検索）

## サンプル申請シナリオ

| # | シナリオ | 特徴 | 期待結果 |
|---|---|---|---|
| 1 | 設備変更申請（田中太郎） | 書類完備、350万円 | 受付（中リスク） |
| 2 | 人事異動申請（佐藤花子） | 引き継ぎ計画未提出 | 要確認（不備あり） |
| 3 | 予算申請（本田健一） | 1,500万円、契約書未確定 | 差戻（高リスク） |
| 4 | 不明確な申請 | 内容不足、種別不明 | 要確認（内容不明確） |
| 5 | 契約更新申請（中村幸子） | 同一条件更新、書類あり | 受付（低リスク） |

## API Endpoints

| Method | Path | 説明 |
|---|---|---|
| `POST` | `/api/process` | 申請テキストを送信、パイプライン実行 |
| `POST` | `/api/confirm` | 审核員確認、台帳ステータスを受付済に更新 |
| `GET` | `/api/export/{id}?format=json\|csv` | 台帳データエクスポート |
| `GET` | `/api/sample` | サンプル申請データ5シナリオ |
| `GET` | `/api/status` | llama-server状態確認 |
| `GET` | `/api/ledger` | 台帳エントリ一覧 |
| `POST` | `/api/ledger` | 台帳エントリ手動追加 |
| `PUT` | `/api/ledger/{id}` | 台帳エントリ更新 |
| `DELETE` | `/api/ledger/{id}` | 台帳エントリ削除 |

## 小モデル対策 (1.2Bの制限への対応)

| 制限 | 対策 |
|---|---|
| 日本語生成が不安定 | Tool callingで強制構造化出力。模型不調時は正規表現フォールバック |
| 判断が不正確 | **判断は全てプログラムで処理**。リスク評価・受付判定は確定的スコアリング |
| ハルシネーション | 不備キーワード検出 + 確率的判断の排除 |
| 不明入力への対応 | 入力テキストの意味キーワード検出 + フィールド完全性チェック |

## 技術スタック

| 層 | 技術 |
|---|---|
| 推論エンジン | llama.cpp (CPU, OpenAI-compatible API) |
| AIモデル | LFM2-1.2B-Tool Q4_K_M (Liquid AI, 731MB GGUF) |
| バックエンド | Python 3.11+ + FastAPI + httpx |
| フロントエンド | React + Vite + TypeScript |
| データ形式 | JSON / CSV (台帳エクスポート) |

## 参考

- [LFM2-1.2B-Tool Model Card](https://huggingface.co/LiquidAI/LFM2-1.2B-Tool)
- [LFM2-1.2B-Tool-GGUF](https://huggingface.co/LiquidAI/LFM2-1.2B-Tool-GGUF)
- [Liquid4All/cookbook](https://github.com/Liquid4All/cookbook)
- [LFM2 Technical Report](https://arxiv.org/abs/2511.23404)

## License

This project is provided as a demo. The LFM2 model is subject to its own license terms.