# ERP / CRM Agent P Demo 设计

目标：用假的 ERP / CRM / SSO 系统作为测试场，验证本地 LFM 2.5 1.2B Instruct 在 Pi agent runtime 中是否能作为通用企业内部 Agent P，自己判断用户意图、按需调用工具、处理 ERP / IT 支持问题。

## 1. 核心定位

这个 demo 的重点不是 UI，也不是写一套 Python 规则模拟 agent。

真正要测试的是：

```text
Pi Agent Runtime + Local LFM 2.5 1.2B Instruct + ERP Skill + ERP Tools + ERP Simulator
```

Streamlit 只负责两件事：

- 模拟人类员工通过网页/键鼠操作 ERP。
- 把用户聊天输入发给 Pi Agent P，并渲染 Pi 返回的消息和 tool trace。

Agent P 是常驻通用 agent。它平时可以正常聊天；当用户问 ERP、SSO、CRM、权限、工单、IT 问题时，由 LFM 2.5 1.2B 自己判断是否需要工具，再调用 Pi tools。

当前模型迁移：

- 旧模型：`lfm2-1.2b-tool-q4_k_m.gguf`
- 新模型：`lfm2.5-1.2b-instruct-q4_k_m.gguf`
- 启动脚本：`scripts/start_lfm25_server.sh`
- Pi 默认模型：`.pi-agent/settings.json` 已切到 LFM2.5
- Pi runtime 默认模型：`agent_q/pi_agent.py` 已切到 LFM2.5

失败日志数据化：

- 采集脚本：`scripts/build_agent_training_data.py`
- SFT 输出：`training_data/agent_p_sft.jsonl`
- DPO 输出：`training_data/agent_p_dpo.jsonl`
- 当前用途：把误调用 `read`、误建单、未调用 ERP 分析工具、口头说“已建 ticket”但没有调用 ticket tool 等失败样本转成 LoRA / QLoRA 的训练草稿。
- 评估脚本：`scripts/eval_agent_p.py`

当前实现的约束：

- `app.py` 不再用 `AgentQRuntime` 做分类、检索、建单。
- `handle_employee_chat()` 对所有用户输入都直接调用 `PiAgentRuntime.chat()`。
- Python 只保存模拟 ERP 页面状态、启动 Pi、解析 Pi JSON 事件、渲染结果。
- Knowledge Search 页面保留手动 `rg` 检索，用作对照观察，不参与 Agent P 的聊天路径。

## 2. 正确架构

```text
Employee Web ERP UI
  - 登录页面、错误页面、用户上下文
  - 写入 erp_state/current_error.json 作为模拟网页状态
        |
        v
Pi Agent P Runtime
  - Pi session / JSON or RPC event stream
  - Local LFM 1.2B as agent brain
  - Skill discovery and prompt guidance
  - Tool loop and tool trace
        |
        +--> ERP Support Skill
        |     .pi/skills/erp-support/SKILL.md
        |     - 何时查当前错误
        |     - 何时搜索知识库
        |     - 何时建单 / handoff
        |
        +--> ERP Tools Extension
              agent_q/pi_erp_extension.ts
              - erp_get_current_error
              - erp_inspect_current_error_with_kb
              - erp_query_state
              - kb_rg_search
              - kb_read_knowledge
              - erp_draft_ticket
              - erp_create_ticket
              - erp_create_ticket_from_current_error
              - erp_handoff_to_it_agent
              - erp_execute_admin_action
```

关键点：

```text
用户通过 Web UI 操作 ERP。
Agent P 通过 tool/API 操作同一个模拟 ERP。
```

两者面对同一个系统状态，只是入口不同。

## 3. 不应该做的事

以下逻辑会让测试失真，主路径必须禁止：

- Python 先分类。
- Python 先 `rg_search`。
- Python 决定是否建 ticket。
- Python 把 Pi 当成补充说明生成器。
- Python fallback 到 llama.cpp 直连。
- UI 根据固定 scenario 自动给出诊断。
- 用户普通聊天被 Python 拦截成固定回答。

旧的 `agent_q/runtime.py`、`agent_q/tools.py`、`agent_q/pi_client.py` 只作为历史 POC 兼容文件保留，不能从 Streamlit 主 demo 调用。

这些都会绕过 LFM 1.2B 的 agent 判断能力。

## 4. Pi 的职责

Pi Agent P 应该自己处理：

- 普通聊天
- 判断是否是 ERP / IT 支持问题
- 判断是否需要读取当前 ERP 页面错误
- 判断是否需要搜索知识库
- 判断是否需要创建工单
- 判断是否需要 handoff 给 IT Agent
- 记录 tool trace

用户只看到普通聊天框。

示例：

```text
用户：こんにちは
Agent P：こんにちは。

用户：今出ているエラーを確認して
Agent P：调用 erp_get_current_error -> kb_rg_search -> 回答

用户：今出ているエラーを確認して、社内規程も検索して
Agent P：调用 erp_inspect_current_error_with_kb -> 回答

用户：AADSTS50076 と表示されます
Agent P：从文本提取错误码 -> 按需调用 erp_query_state / kb_rg_search

用户：まだ解決しないのでITに連絡してください
Agent P：优先调用 erp_create_ticket_from_current_error，或 erp_draft_ticket -> erp_create_ticket -> erp_handoff_to_it_agent
```

## 5. Skill 设计

位置：

```text
.pi/skills/erp-support/SKILL.md
```

作用：

- 给 Pi/LFM 提供 ERP 支持流程知识。
- 告诉模型什么时候用什么工具。
- 不直接执行逻辑，不替代模型判断。

Skill 内容应覆盖：

- 当前页面错误检查流程
- 粘贴错误文本处理流程
- 本地知识库检索流程
- 工单创建流程
- IT handoff 流程
- 高风险动作边界

## 6. Extension / Tool 设计

位置：

```text
agent_q/pi_erp_extension.ts
```

工具：

### erp_get_current_error

读取当前模拟 ERP 页面错误：

```text
erp_state/current_error.json
```

用于“帮我看当前错误”“今出ているエラーを確認して”等场景。

### erp_inspect_current_error_with_kb

读取当前 ERP 错误，并用错误码或系统名检索本地知识库。

这是给小模型准备的业务复合工具。它不是 Python 代替模型判断，而是把真实 ERP/MCP 里常见的“读取当前页面状态 + 查企业规则”封装成一个业务 API，减少 1.2B 在多步 tool planning 时漏调工具。

### erp_query_state

根据用户文本或错误信息返回结构化业务状态：

- system
- error_code
- category
- risk
- route
- impact
- blocked_actions

### kb_rg_search

用 `rg` 搜索本地知识库。

### kb_read_knowledge

读取知识库文件片段。

### erp_draft_ticket

生成模拟工单草稿。

### erp_create_ticket

创建模拟 ticket，返回 ticket id。

### erp_create_ticket_from_current_error

从当前 ERP 错误日志创建 ticket，并附带 KB evidence 和 IT handoff package。

这是第二个业务复合工具，用来测试本地小模型能否选择正确业务能力。它替代的是人工员工在 ERP 里打开错误、复制 trace、查规程、填 ticket 的一连串操作。

### erp_handoff_to_it_agent

把 ticket 和证据交给 IT-side Agent P。

### erp_execute_admin_action

执行模拟低风险动作。高风险动作必须拒绝或转审批。

## 7. 当前评估模式

当前阶段测试模型能力上限，但不能把所有工具无条件暴露给 1.2B。实测发现：

- 普通日期问题可能误调用内置 `read` 去找不存在的日期文件。
- 粘贴 SSO 错误可能误调用 `erp_create_ticket`，把“报错文本”当成“建单请求”。

因此当前 demo 使用 runtime tool profile：

- 普通聊天 / 日期问题：`--no-tools`，直接回答。
- 粘贴 ERP/SSO/CRM 错误：只开放 `erp_analyze_pasted_error_with_kb`。
- 当前页面错误检查：只开放 `erp_get_current_error` / `erp_inspect_current_error_with_kb` / KB 工具。
- 明确 IT 連絡 / チケット作成：开放 ticket / handoff 工具。
- 明确文件、代码、shell 操作：才开放 Pi built-in tools。

这不是 Python 代替模型做 ERP 判断，而是 agent runtime 的工具权限路由：让小模型在正确的工具集合里做判断，避免无关工具干扰业务能力测试。

原始 maximum capability mode 可作为压力测试：

- 不加 `--no-tools`
- 不加 `--no-builtin-tools`
- Pi 内置工具可用
- ERP extension tools 可用
- ERP skill 可用

这可以观察 LFM 1.2B 在工具很多的情况下是否会选择正确工具，但不作为主 demo 交互模式。

后续生产化可以切换到 safety profile：

- 禁用内置开发工具
- 只开放 ERP/MCP tools
- 高风险动作审批化

## 8. LFM2.5 + LoRA / QLoRA 微调计划

当前实测结论：

- LFM2.5-1.2B-Instruct 比旧 LFM2 tool GGUF 稳定：普通问候 / 日期问题不再频繁误调用 `read`。
- 粘贴 SSO 错误时，模型能在受控工具 profile 下调用 `erp_analyze_pasted_error_with_kb`，且不会直接建单。
- 当前页面错误检查能调用 `erp_get_current_error`。
- 仍然失败的关键点：用户明确说“ITに連絡 / チケットを作成”时，模型有时只输出“我会创建 ticket”，没有真正调用 `erp_create_ticket_from_current_error`。这类“承诺执行但未调用工具”的失败必须作为 DPO 负样本。

2026-06-17 当前 eval 基线：

```text
PASS smalltalk_date_no_tools
PASS pasted_sso_error_analyze_only
PASS current_error_fetch
FAIL ticket_request_create_ticket
```

失败原因不是 ERP tool 不可用，而是模型没有发出 tool call。即使 tool profile 只暴露 `erp_create_ticket_from_current_error`，模型仍可能口头承诺“チケットを作成します”。因此下一步重点是行为微调，而不是继续堆 prompt。

训练数据来源：

```text
.pi-agent/sessions/.../*.jsonl
        |
        v
scripts/build_agent_training_data.py
        |
        +--> training_data/agent_p_sft.jsonl
        +--> training_data/agent_p_dpo.jsonl
```

SFT 目标：

- 普通聊天：不调用工具。
- 日期 / 问候：直接回答，不读文件。
- 粘贴错误：调用 `erp_analyze_pasted_error_with_kb`。
- 当前页面错误：调用 `erp_get_current_error` 或复合检查工具。
- 明确建单 / IT 連絡：调用 `erp_create_ticket_from_current_error`。

DPO 目标：

- chosen：正确 tool call 或正确直接回答。
- rejected：历史失败输出，例如：
  - `read("こんにちは今日は何の日")`
  - 对粘贴错误直接 `erp_create_ticket`
  - 对 ticket 请求只说“チケットを作成します”但没有 tool call
  - 当前错误请求没有读取 ERP 状态

微调顺序：

1. 先用 `training_data/agent_p_sft.jsonl` 做小规模 SFT LoRA，让模型学会 Pi tool-call 格式和 ERP intent 边界。
2. 再用 `training_data/agent_p_dpo.jsonl` 做 DPO / preference tuning，重点压制“乱用 read”和“口头执行不调用工具”。
3. 重新跑 `scripts/eval_agent_p.py`，比较四个基本场景：
   - smalltalk/date no tools
   - pasted SSO error analyze only
   - current ERP error fetch
   - explicit ticket creation
4. 如果工具行为稳定但业务回答质量差，再补 ERP 知识数据；如果工具行为仍不稳定，继续扩大行为数据，不急着加知识。

当前数据规模：

```text
python3 scripts/build_agent_training_data.py
# SFT examples: 24
# DPO examples: 25
```

这个规模只够验证训练链路。真正微调前应扩到：

- SFT：300-800 条，多语言、多系统、多错误码、多工具调用。
- DPO：100-300 对，重点覆盖已观察到的失败。
- Eval：至少 30 个固定 case，覆盖普通聊天、粘贴错误、当前页面、ticket、handoff、权限边界。

参考 Liquid AI 文档方向：

- `https://docs.liquid.ai/lfm/fine-tuning/datasets`
- `https://docs.liquid.ai/lfm/fine-tuning/trl`

Liquid 文档的核心启发是：SFT 和 DPO 需要拆成不同格式的数据集。我们的 `agent_p_sft.jsonl` 用 chat messages 格式训练“应该怎么做”；`agent_p_dpo.jsonl` 用 prompt / chosen / rejected 格式训练“正确工具行为优于错误工具行为”。

## 9. POC 成功标准

- UI 聊天输入直接进入 Pi Agent P，而不是 Python 规则。
- LFM 1.2B 可以正常处理普通聊天。
- 当用户要求查看当前错误时，Pi 调用 `erp_get_current_error`。
- 当需要依据时，Pi 调用 `kb_rg_search`。
- 当用户要求 IT 支持时，Pi 创建 ticket 并 handoff。
- 页面能显示 Pi tool trace。
- Pi session / JSONL 可用于复盘。

## 9. 实施路线

### Phase 1：Pi-first 单轮 JSON agent

先用 `pi --mode json -p` 每次处理一轮，快速验证 tool loop。

```text
Streamlit chat -> Pi JSON -> LFM -> tools -> response/tool trace
```

这是当前可运行版本。它不是最终常驻 agent，但已经满足关键验证：每个用户输入都由 Pi/LFM 决定是否调用工具。

### Phase 2：Pi RPC 常驻会话

改成 `pi --mode rpc` sidecar，让 Agent P 真正常驻：

```text
Streamlit starts Pi RPC sidecar
chat_input -> RPC prompt
Pi streams events
UI renders assistant messages and tool trace
```

Phase 2 的目标是保持长会话上下文、减少每轮启动开销，并让员工侧 Agent P 与 IT 侧 Agent P 都作为独立 Pi session 接入同一个 ERP/MCP 工具层。

### Phase 3：IT-side Agent P

IT Operations 页面也接 Pi session，用同一套或另一套 IT skill/tools 处理 ticket。

## 10. 产品叙事

Internal ERP Portal 是模拟企业系统。

真正测试对象是本地 LFM 1.2B 在 Pi runtime 中能否作为通用 Agent P：

- 看懂用户请求
- 决定是否需要工具
- 操作 ERP tools
- 检索企业知识库
- 创建和移交工单
- 减少人工 IT / ERP 支持成本
