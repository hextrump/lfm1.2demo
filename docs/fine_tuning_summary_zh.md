# Agent P Fine-Tuning — 一页总结

**基座：** LiquidAI/LFM2-1.2B-Tool（Q4_K_M） · **训练：** A100-40GB · **耗时 + 成本：** 40 分钟 / $0.70

## 目标

`runtime/pi_agent.py` 1428 行里有 65% 是 1.2B 模型太弱逼出来的 Python 短路
（`_direct_basic_reply`、`_direct_it_action`、`_scenario_recommendations` 等）。
最终要把这些删掉，让模型自己干。本轮只完成"数据和 pipeline 跑通"，代码
一行没删。

## 做了什么

**数据（311 SFT + 60 DPO + 42 eval）**
- GitHub seed：30 SFT + 11 DPO
- 207 个真实 session JSONL 挖出 165 SFT + 4 DPO
- 测试 + 场景 + KB 引用合成器：再补 116 SFT + 45 DPO
- README 推荐 300–800 SFT / 100–300 DPO，**SFT 达标，DPO 偏低**

**训练（v1 LoRA）**
- 配置：LoRA r=16 / α=64 / target=[q,k,v,o,gate,up,down] / 8 epoch / bf16
- loss：2.0 → 1.62，mean_token_accuracy 0.67
- 产物：PEFT merge → HF → GGUF F16 → Q4_K_M（698 MB），落到
  `models/lfm2-1.2b-tool-q4_k_m.v1.Q4_K_M.gguf`

**本轮最大的工作流变化：IT Operations 改成 KB-Analyst 模式**
- 旧：聊天里调 `erp_it_resolve_ticket` / close / reassign / triage
- 新：聊天只做 KB 搜索 + 分析，状态变更全走 UI 按钮
- 实现：把 KB 搜索挪到 Python 短路（`_direct_it_kb_analysis`），
  LLM 只负责"写"日文答复——1.2B 不可靠地发 `<tool_call>` 信封

## 测试结果

| 套件 | 通过 |
|---|---:|
| 单元测试 | 104/104 |
| 运行时测试（打活 llama-server） | 34/34 |
| 身份 prompt | "I am Agent P、ERP / CRM / SSO support assistant." ✓ |

## 遗憾

- **DPO 没跑** — TRL 0.13 要 torch ≤ 2.3 的 `FSDPModule` API，
  transformers main 又要 torch ≥ 2.4，两边打架。选了"支持 lfm2 加载"，
  牺牲了 DPO。
- **1428 行 Python 短路一个没删** — LoRA 还不够强，模型仍然会
  幻觉（"I am an AI assistant"、拼错工具名 `erp_it_comment_ticket`）。
- **KB 引用样本太少** — 311 SFT 里只有 11 条 `kb_rg_search`
 <tool_call>样本（KB 引用合成器最多产这么多）。

## 下一步

1. 升 TRL ≥ 0.18 跑 DPO（已配好参数）
2. 扩 SFT 到 600+ 行：每 scenario 配 3 个 rejected（+100）+ KB 引用变种（+30）
3. DPO 跑通后开始删 Python 短路（先删 `_is_mostly_english`，最后
   删 `_scenario_recommendations`）
4. 改完数据重训一条命令：`make data && make modal-pipeline`

详细版见 `docs/fine_tuning_report.md`（10 节，~370 行）。
