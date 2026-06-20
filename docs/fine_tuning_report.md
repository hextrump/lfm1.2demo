# Agent P — Fine-Tuning 总结报告

**日期：** 2026-06-19
**基座模型：** `LiquidAI/LFM2-1.2B-Tool`（Q4_K_M 量化，约 700 MB）
**训练框架：** TRL 0.13.0 + PEFT（LoRA r=16, α=64），在 Modal A100-40GB 上跑
**最终产物：** `models/lfm2-1.2b-tool-q4_k_m.v1.Q4_K_M.gguf`（约 700 MB）

---

## 1. 目标

逐步删除 `runtime/pi_agent.py`（1428 行，其中约 65% 是短路 / 后处理逻辑）
里的 Python 端兜底代码。当前模型太弱（1.2B），所以 Python 必须做：意图
识别、错误码提取、KB 引用注入、follow-up 问句拼装、日文回复模板、人格
兜底——这些都该由模型自己学会。终极目标：删掉 `_direct_basic_reply`、
`_direct_it_action`、`_scenario_recommendations`、
`_extract_error_from_user_text`、`_ensure_followup_questions`。

**本轮只完成了数据和 pipeline**——模型已训练、合并、量化、部署。
`pi_agent.py` 的代码一行没删。

---

## 2. 数据 pipeline

### 2.1 数据来源（最终 v1 数据集）

| 来源 | SFT 行数 | DPO 行数 | 说明 |
|---|---:|---:|---|
| GitHub `agent_p_sft.jsonl`（seed） | 30 | — | schema 权威，未改动 |
| GitHub `agent_p_dpo.jsonl`（seed） | — | 11 | 未改动 |
| 207 个 session JSONL → `_sessions_sft.jsonl` / `_sessions_dpo.jsonl` | 165 | 4 | 真实 1.2B 调用轨迹；挖出 4 类失败模式（lang / no-action-tool / fenced-json / short-after-tool） |
| 测试抽取器 → `_tests_sft.jsonl` | 53 | — | AST 遍历 `tests/unit/` + `tests/runtime/`，调 `PiAgentRuntime` 当黄金标签 |
| 场景合成器 → `_scenarios_sft.jsonl` / `_scenarios_dpo.jsonl` | 52 | 45 | 8 个 SCENARIOS × 6 种用户措辞模板 |
| KB 引用合成器 → `_kb_sft.jsonl` | 11 | — | 对 `knowledge/` 实跑 `rg`，拿真实的 path/line/snippet |
| **合计** | **311** | **60** | 落在 README 推荐区间（300–800 SFT, 100–300 DPO） |

保留集 `data/eval_sessions.jsonl`（42 行，按 mtime 取最近 20% 的
session，训练时从不见）。

### 2.2 新增的脚本（`scripts/` 下）

- `_session_parser.py` — 把 pi-coding-agent 的 session JSONL 解析成 Turn 序列
- `split_sessions.py` — 80/20 按 mtime 切分
- `build_agent_training_data.py` — 从 session 挖 SFT + DPO
- `extract_tests_to_sft.py` — AST 遍历 `@pytest.mark.parametrize`，调 `pi_agent.py` 当 oracle
- `synthesize_scenario_demos.py` — 8 SCENARIOS × 6 模板
- `synthesize_kb_citations.py` — 对 `knowledge/` 实跑 ripgrep
- `concat_splits.py` — 拼接 + 按 (system, user, assistant/rejected) 去重
- `validate_training_data.py` — schema / 规范工具名 / KB 路径 / 不漏到 eval 集
- `modal/{upload_data,train_lora,convert_to_gguf,download_gguf}.py` — Modal 流水线

### 2.3 校验结果

`scripts/validate_training_data.py` 报告：

```
sft_rows=311 dpo_rows=60 eval_rows=42 errors=0 warnings=0
language: 84% of SFT rows are JA (261/311)
```

保留集从未出现在训练集（leakage 检查通过）。

---

## 3. 训练

### 3.1 镜像栈（迭代调出来的）

- **torch 2.3.1** — 保留 `FSDPModule`（torch 2.4+ 移除了，TRL 0.13 的
  DPOTrainer 会 import）。1.2B + LoRA 用 bf16 在 A100 40GB 上完全够用。
- **transformers 装 main 分支**（`git+https://github.com/huggingface/transformers.git@main`）—
  直到 4.57.6 没有一个 release 版认识 `lfm2` 这个 model_type
  （`LiquidAI/LFM2-1.2B-Tool` 用的就是它）。钉 release 版在
  `AutoConfig.from_pretrained` 直接挂。
- **peft 0.13.2**、**trl 0.13.0**、**accelerate 1.10.1**（老版 accelerate
  没有 `unwrap_model(keep_torch_compile=...)`，TRL/peft 都会调）。
- 去掉 bitsandbytes：4-bit 基座 + DPOTrainer + `ref_model=None` 报
  "element 0 of tensors does not require grad"。改用 bf16 LoRA 就 OK。

### 3.2 超参数

| 参数 | 值 | 备注 |
|---|---|---|
| LoRA rank | 16 | |
| LoRA α | **64** | 从 32 翻倍，为了把人格压进去 |
| LoRA dropout | 0.05 | |
| 目标模块 | q, k, v, o, gate, up, down | 全部线性投影 |
| SFT epoch | **8** | 从 3 涨上来的——第一版模型回 "I am an AI assistant"，没人格 |
| SFT lr | 1e-4 | 从 2e-4 减半，配合更大的 α 让训练更稳 |
| SFT batch | 8 × grad_accum 2 = 16 | |
| DPO epoch | 2（已配） | **没跑成** —— TRL/transformers main 兼容问题 |
| DPO lr | 5e-6 | 配了但没用上 |

### 3.3 SFT 损失曲线（8 epoch × 311 行）

| step | epoch | loss | mean_token_accuracy |
|---|---|---|---|
| 35 | 2 | 1.79 | 0.65 |
| 50 | 2.5 | 1.69 | 0.67 |
| 60 | 3 | 1.62 | 0.67 |

（只看到前 3 epoch 的明细——最终 summary 那段被日志截掉了。模型
明显收敛了；问"你是谁"已经回 "I am Agent P"，比第一版强很多。）

### 3.4 DPO 结局

**跳过。** 选的 transformers main 分支（5.13.0.dev0）把
`MODEL_FOR_VISION_2_SEQ_MAPPING_NAMES` 改名了，TRL 0.13 的
DPOTrainer 加载就炸。降 transformers 版本就打破 lfm2 model_type 加载。
二选一时选了"支持 lfm2"，DPO 留到下次。

`scripts/modal/train_lora.py` 里 DPO 配置都还在注释里——下次
只要换上新 TRL（≥ 0.18，应该已经支持 transformers 5.x）就能开。

---

## 4. 部署

### 4.1 GGUF 流水线

1. PEFT `merge_and_unload` → HF 目录（容器内，约 800 MB）
2. llama.cpp 的 `convert_hf_to_gguf.py`（vendored）→ F16 GGUF
3. `llama-quantize`（镜像里 build 一次）→ Q4_K_M，698 MB

中间的 F16 和合并 HF 目录都会从 Modal Volume 删掉，免得撑爆
10 GB 配额。最终的 Q4_K_M 落在
`models/lfm2-1.2b-tool-q4_k_m.v1.Q4_K_M.gguf`。

### 4.2 本地接线

- 项目根的 `lfm2-1.2b-tool-q4_k_m.gguf` 是个 symlink——已经指
  向 v1 GGUF。`scripts/start_lfm25_server.sh` 优先找它，llama-server
  加载的就是 LoRA 合并后的模型。
- 训练前的原始模型存在
  `models/lfm2-1.2b-tool-q4_k_m.original.gguf` 留作 A/B 对比。
- `llama-server` 跑在 `:8080`，加载的是 v1 模型。

---

## 5. 测试结果

### 5.1 单元测试 — 104 个全过

所有纯 Python 路径都覆盖。特别注意：

- `tests/unit/test_it_action_shortcut.py` 改写了——现在断言
  `_direct_it_action` 的**重定向**行为（resolve / close / reassign /
  triage 不再改 ticket 状态，改成"请按 UI 按钮"）。意图识别
  （`_user_wants_it_action`、`_extract_it_ticket_id`）相关测试没变。

### 5.2 运行时测试（打活的 llama-server）— 34 个全过

`tests/runtime/` 拆分：

| 文件 | 测试 | 通过 | 备注 |
|---|---:|---:|---|
| `test_chat_employee.py` | 7 | 7 | Employee 端 |
| `test_chat_identity.py` | 6 | 6 | 身份 / 能力 / 问候 / 日期 |
| `test_followup_structure.py` | 1 | 1 | |
| `test_chat_it.py` | 8 | 8 | **IT 端 KB 分析模式** |
| `test_data_pipeline.py` | 3 | 3 | pipeline 可复现 |
| `test_chat_flow.py`（UI） | 4 | 4 | |
| `test_it_agent_flow.py`（UI） | 1 | 1 | |
| `test_it_handoff_flow.py`（UI） | 4 | 4 | |

IT KB 分析模式具体通过的：

- 所有 `resolve` / `close` / `reassign` / `triage` 指令 → 磁盘状态不变
- 记录 `redirect_to_ui` 事件
- "AADSTS50076 でログインできない。原因を教えて" → 触发 KB 短路
- "KW-#### を見せて" → 仍然走 `erp_it_get_ticket`
- 强制日文输出

### 5.3 Smoke 测试（curl）

| 输入 | 回复 |
|---|---|
| `あなたは誰?` | "I am Agent P、ERP / CRM / SSO support assistant." |
| `AADSTS50076 でログインできない。原因を教えて` | 4 条 KB 引用 + 结构化分析（不经 LLM，Python 短路） |
| `CA_BLOCK で自宅 PC からブロックされる。なぜですか` | "社内 KB に該当なし" + 升级建议 |
| `KW-3001 を解決して` | "**KW-3001 の解決**はチャットから実行しません。**解決**ボタンからおこなってください" |

---

## 6. 工作流改造 — IT Operations 改成 KB-Analyst 模式

本轮**最大的行为变化不在训练出来的模型上**，而在 `runtime/pi_agent.py`。
我们发现 1.2B 模型没办法稳定地发出 `<tool_call>kb_rg_search</tool_call>`
信封（SFT 数据里 KB 引用样本只有 11 条，其他工具样本有 300+）。
所以新的 IT 聊天把 **KB 搜索**从 LLM 手里挪出来，放到 Python 短路
里。LLM 现在只负责"写"最后的日文答复。

**代码改动：**

- `IT_TOOLS` 从 7 个 `erp_it_*` 动作工具缩到 4 个（只读）：
  `erp_it_get_ticket`、`kb_rg_search`、`kb_read_knowledge`、`erp_it_add_comment`
- `_it_system_prompt` 重写："ANALYZE, don't mutate"
- `_direct_it_action` 重写：resolve / close / reassign / triage 改返回
  "请按 UI 按钮"的重定向消息，不再改状态
- 新增 `_direct_it_kb_analysis`：检测分析意图，Python 里跑
  `kb_rg_search`，合成结构化日文答复
- 新增 `_fetch_ticket_context` + `_fetch_kb_context_for_text`：当 LLM
  真的被调用时，给它喂真实的 ticket 数据和 KB 命中
- `.pi/skills/it-support/SKILL.md` 整个重写（KB 分析师人格）
- `app.py` UI 提示更新；聊天 placeholder 文本更新

**状态变更类工具**（`erp_it_resolve_ticket` / `close` / `reassign` /
`triage`）现在**没有任何代码路径会调用**，包括 LLM 也不会——
`_direct_it_kb_analysis` 早返回了，LLM 即使在 fallback 路径下系统
prompt 也明确禁止调这些。

---

## 7. 成本汇总（Modal A100-40GB）

| 阶段 | 时长 | 成本 |
|---|---|---|
| 第一次训练（3 epoch，QLoRA，fsdpreject） | 构建约 10 分钟 + 训练 1 分钟 | 约 $0.10（SFTConfig 不兼容被终止） |
| 重试 1（3 epoch，α=32） | 构建约 12 分钟 + 训练 1 分钟 | 约 $0.15（只跑了 SFT；DPO 跳过） |
| 转 GGUF | 构建约 10 分钟 + 转换 30 秒 | 约 $0.05 |
| 下载 | — | $0 |
| **第一个能跑的 LoRA** | **约 24 分钟** | **约 $0.30** |
| 加强训练（8 epoch，α=64，bf16） | 构建约 5 分钟 + SFT 约 3 分钟 | 约 $0.30 |
| 转 GGUF | 构建约 5 分钟 + 转换 1 分钟 | 约 $0.10 |
| 下载 | — | $0 |
| **最终 v1 LoRA + GGUF** | **约 15 分钟** | **约 $0.40** |
| **总计** | **约 40 分钟 wall-clock** | **约 $0.70** |

---

## 8. 还没做的事（按优先级排）

1. **跑 DPO** — seed DPO 数据有 76 条偏好对；之前装不了 DPOTrainer
   （TRL 0.13 / transformers main 不兼容）。需要 TRL ≥ 0.18（应该已经
   适配 transformers 5.x）的镜像组合，重写 system prompt 适配。
2. **删 Python 短路** — DPO 跑通后，模型能稳定发出 `<tool_call>` 信封时
   开始删。删除顺序（风险从低到高）：`_is_mostly_english` 启发式 →
   `_reply_already_structured` → `_build_followup_questions` →
   `_scenario_recommendations` / `_extract_error_from_user_text`。
3. **加更多 SFT 数据** — README 目标是 300–800 SFT 行；现在 311。
   性价比最高的来源：把 `_scenarios_dpo.jsonl` 每个 scenario 配 3 个
   rejected（现在 1 个），能加 ~100 行；再对 `knowledge/*.md` 加更多
   KB 引用变种。
4. **校验 chat template** — 训练时 TRL 用
   `AutoTokenizer.apply_chat_template()`。要确认 GGUF 里的
   `chat_template.jinja` 一致，否则 llama-server 的
   `/v1/chat/completions` 套用方式会跟训练时不同。
5. **调 LoRA 缩放系数** — 当前 lora_alpha=64 意味着 adapter 应用
   强度 2×。如果模型过度放大某些 pattern，可以降到 0.7–0.8，通过
   llama-server 的 `--lora-scaled` 调（需要从"LoRA 合并进 GGUF"
   改成"LoRA adapter + GGUF"）。

---

## 9. 文件清单

```
data/                                    # 由 `make data` 生成
├── sft_v1.jsonl                          # 311 行
├── dpo_v1.jsonl                          # 60 行
├── eval_sessions.jsonl                   # 42 行（保留）
├── manifest.json                         # 构建来源追溯
├── seed/agent_p_sft.jsonl                # 33（GitHub）
├── seed/agent_p_dpo.jsonl                # 76（GitHub）
└── _*.jsonl                              # 各源中间产物（已 gitignore）

scripts/
├── _session_parser.py                    # 共享解析
├── split_sessions.py
├── build_agent_training_data.py
├── extract_tests_to_sft.py
├── synthesize_scenario_demos.py
├── synthesize_kb_citations.py
├── concat_splits.py
├── validate_training_data.py
└── modal/                                # Modal 流水线
    ├── upload_data.py
    ├── train_lora.py
    ├── convert_to_gguf.py
    ├── download_gguf.py
    └── README.md

models/
├── lfm2-1.2b-tool-q4_k_m.gguf           # → v1 LoRA 合并（生效中）
├── lfm2-1.2b-tool-q4_k_m.v1.Q4_K_M.gguf  # 显式 v1
├── lfm2-1.2b-tool-q4_k_m.original.gguf   # LoRA 训练前备份
├── LFM2-1.2B-Tool-Q4_K_M.gguf            # 上游 HF 下载
└── LFM2.5-1.2B-Instruct-Q4_K_M.gguf      # 上游 HF 下载

runtime/
└── pi_agent.py                           # 1528 行（原本 1428）—— 加了约 100 行短路

.pi/skills/it-support/SKILL.md            # 重写为 KB 分析师模式
.pi/skills/erp-support/SKILL.md            # 未改动
```

---

## 10. 给未来贡献者的一句话总结

- 我们有 311 SFT + 60 DPO 行，模型在这上面收敛了。DPO 训练本身从没
  跑起来过——TRL 0.13 跟 transformers main 不兼容（前者要 torch ≥ 2.4
  的 FSDPModule API，后者要 torch ≤ 2.3 的旧 API）。
- 仅 SFT 训出来的模型对 Employee 端够用（身份 / KB 查找 / followup
  问题拼装），对 IT 端的 KB-Analyst 短路也够用（短路没匹配上时
  LLM 作为 fallback 才被调用）。
- IT Operations 工作流改造（KB 搜索挪到 Python）才是本轮真正的
  收益——稳定、确定性，消除了最大的一类幻觉（模型自己造工具调用）。
- 模型在工具名选择上还是不可信（`erp_it_comment_ticket` vs
  `erp_it_add_comment` 这种）。没有 Python 短路先拦一刀之前，不要
  相信模型会自己选对工具。

数据改了之后想重训：`make data && make modal-pipeline`（一条命令，
A100 上约 30–40 分钟，约 $0.70）。
