# DeepSeek Thinking Provider: Implementation And Tests

> [返回设计决策](deepseek-thinking-provider-design.md) · [接口契约](deepseek-thinking-provider-contracts.md)

## 3. 实现提示

### 目标文件状况评估

目标文件总体能接住 feature，但应做最小必要拆分：

- `provider/delivery.rs` 约 551 行，同时负责 HTTP、SSE、stream collector、debug response、stream capability cache。新增 reasoning 后，collector 逻辑应保持小而集中，不再把 content/reasoning/tool_calls 全散在 match 分支里。
- `provider/messages.rs` 约 490 行，承担上下文消息构造和 tool/server tool 辅助函数。新增 `reasoning_content` 时只改 RequestMessage 构造与 serialization 所需字段，不在这里塞 DeepSeek policy。
- `agent/runner.rs` 约 399 行，已有 tool loop 编排。新增 reasoning preview 和 tool-call transient 回传时，优先加小 helper（如 flush reasoning delta / build assistant tool transient），避免 loop 主干继续膨胀。

### 改动计划

1. **新建/调整 provider reasoning 数据结构**
   - 在 `ProviderResponse` / `WireResponse` 增加 `reasoning_content: Option<String>`。
   - 在 `WireStreamDelta` 增加 `ReasoningDelta(String)`。
   - 在 `ProviderProgressEvent` 增加 `ReasoningDelta(String)`。
   - 在 `DebugStructuredProviderResponse` 增加可选 `reasoning_content`。

2. **扩展 RequestMessage 轮内 reasoning 回传**
   - 给 `RequestMessage` 增加 `reasoning_content: Option<String>`。
   - 所有构造函数默认 `None`。
   - 新增 assistant tool-call 构造 helper，允许传 `content + reasoning_content + tool_calls`。
   - `serialize_openai_message` 对 assistant message 序列化 `reasoning_content`。

3. **实现 DeepSeek OpenAI ChatCompletions request policy**
   - 增加 helper：`is_deepseek_vendor(config)`、`is_deepseek_v4_model(options.model)`、`deepseek_thinking_policy(...)`。
   - DeepSeek V4 默认发送 `thinking.enabled` + `reasoning_effort = "high"`。
   - DeepSeek Thinking Mode 下跳过 temperature/top_p/penalty 字段；非 DeepSeek 保持现状。
   - 更新 preset default base URL / suggested models / probe model；同步前端 default URL。

4. **实现 OpenAI-compatible reasoning parse**
   - `parse_response` 从 `message.reasoning_content` 填 `WireResponse.reasoning_content`，正文只读 `content`。
   - `parse_stream_event` 解析 `delta.reasoning_content` 为 `WireStreamDelta::ReasoningDelta`。
   - 删除 `openai_message_text` 的 reasoning fallback，或拆成 `openai_message_content` + `openai_message_reasoning_content`。

5. **打通 Provider → Agent → UI 的 reasoning delta**
   - `StreamCollector` 分别累积 `reasoning_content` 与 `content`。
   - stream 时发送 `ProviderProgressEvent::ReasoningDelta`。
   - agent runner 转成 `AssistantReasoningPreview`。
   - messaging 层转成 `UiAssistantStreamField::Reasoning`，并更新 persisted timeline 的 `message.reasoning`。
   - 非流式 fallback 后补发缺失 reasoning delta。

6. **修正 tool-call 后的 transient message**
   - agent runner 调用 `append_assistant_tool_call_message` 时传入 `response.reasoning_content`。
   - 下一轮 provider request 中 assistant tool-call message 包含 `reasoning_content`。
   - 确保 final message 写入 `recent_chat` 仍只用 `content`。

7. **更新架构文档与测试**
   - 更新 `reasoning.md`、`provider.md`、`DESIGN.md` 中 DeepSeek 表述。
   - 增加单元测试：request body、stream reasoning parse、non-stream parse、tool-call transient serialization、DeepSeek preset 默认值。
   - 跑 `cargo test -p march-core provider`；若测试分组不存在，跑相关 crate 定向测试或 `cargo test -p march-core`。

### 实现风险与约束

- 不得把 `reasoning_content` 当正文 fallback；这是本 feature 最大 correctness 风险。
- DeepSeek tool-call assistant message 即使 `content` 为空，也要能和 `reasoning_content + tool_calls` 一起序列化。
- 非 DeepSeek OpenAI-compatible provider 若偶然返回 `reasoning_content`，可以展示 reasoning，但不能自动发送 DeepSeek `thinking` request 参数。
- `request_json` debug 必须反映真实发送 body，方便检查 thinking 字段和是否跳过采样参数。
- 旧 `deepseek-chat` / `deepseek-reasoner` 不移除，避免用户已有模型配置突然不可选；但 suggested models 排序把 V4 放前面。
- 官方文档显示 `deepseek-chat` / `deepseek-reasoner` 将于 2026-07-24 停用；测试不要把这两个 alias 当唯一 DeepSeek 模型。

### 推进顺序

1. **数据结构铺底**：为 `RequestMessage`、`WireResponse`、`ProviderResponse`、`WireStreamDelta`、`ProviderProgressEvent` 增加 reasoning 字段/变体。
   退出信号：`cargo check -p march-core` 至少推进到所有新增字段编译错误清完，非 DeepSeek provider 构造函数默认 `None`。

2. **OpenAI message serialization / parsing**：实现 assistant `reasoning_content` 序列化、stream parse、non-stream parse，并删除正文 fallback。
   退出信号：新增单元测试证明 `reasoning_content` 不会出现在 `content`，但会出现在 response reasoning 字段。

3. **DeepSeek request policy 与 preset 更新**：更新 DeepSeek base URL / suggested models / model capabilities / 前端 URL 默认值，插入 thinking request 字段并跳过采样参数。
   退出信号：单元测试构造 DeepSeek V4 request body，断言含 `thinking.enabled`、`reasoning_effort=high`，且不含 `temperature` / `top_p` / penalties。

4. **Provider delivery reasoning collector**：stream collector 分别累积 reasoning 和正文，并向上发 `ProviderProgressEvent::ReasoningDelta`。
   退出信号：stream parse + delivery 层测试证明 reasoning delta 被累计到 `ProviderResponse.reasoning_content`，content 仍独立。

5. **Agent/UI 事件链路**：新增 `AssistantReasoningPreview`，打通 messaging 层和 persisted timeline。
   退出信号：后端事件单测或 reducer 测试证明 reasoning delta 写入 `PersistedAssistantMessage.reasoning`，UI event field 为 `reasoning`。

6. **Tool-call 轮内回传**：agent runner 在追加 assistant tool-call transient message 时带 `response.reasoning_content`。
   退出信号：构造一轮 provider response `{ reasoning_content, tool_calls }` 后，下一次 serialized messages 中的 assistant tool-call message 包含相同 reasoning。

7. **文档和回归验证**：更新架构文档并跑测试。
   退出信号：`cargo test -p march-core` 或定向测试通过；design 中列出的官方约束在 `reasoning.md` / `provider.md` 中有对应长期说明。

### 测试设计

| 功能点 | 验证方式 | 关键用例 |
|---|---|---|
| DeepSeek preset | 单元测试 | `lookup_preset("deepseek")` 默认 URL 为 `https://api.deepseek.com`，probe model 为 `deepseek-v4-flash`，suggested models 含 V4 两个模型。 |
| DeepSeek request body | 单元测试 | DeepSeek V4 + stream=true → body 含 `thinking.enabled` / `reasoning_effort=high` / `max_tokens`，不含采样参数。 |
| OpenAI stream reasoning parse | 单元测试 | `delta.reasoning_content` → `WireStreamDelta::ReasoningDelta`；`delta.content` → `ContentDelta`；同 chunk 两者都在时都不丢。 |
| Non-stream reasoning parse | 单元测试 | `message.reasoning_content + content + tool_calls` → `WireResponse` 三类字段都保留。 |
| 正文隔离 | 单元测试 | `content=""` 且 `reasoning_content` 非空时，`ProviderResponse.content == None`，agent 不把它当 final text。 |
| Tool-call 回传 | 单元/集成测试 | 第一轮 response 带 `reasoning_content + tool_calls`，执行工具后第二轮 request messages 里 assistant message 原样带回 reasoning。 |
| UI/persist reasoning | 单元测试 | `AssistantReasoningPreview` 同时更新 persisted `message.reasoning` 和 UI `assistant_stream_delta { field=reasoning }`。 |
| 非 DeepSeek兼容 | 单元测试 | OpenAI / custom OpenAI-compat request 不插入 `thinking` 字段，采样参数行为保持原样。 |

## 4. 与项目级架构文档的关系

### 名词

- `reasoning_content` 从 DeepSeek 特有字段升级为 OpenAI-compatible visible reasoning 的系统级名词，应写回 `codestable/architecture/reasoning.md`。
- DeepSeek V4 Thinking Mode 替换旧的 “DeepSeek-R1 / InlineTag” 主表述，应同步 `DESIGN.md` 的总入口摘要。

### 动词骨架

- “provider stream reasoning delta → AgentProgressEvent → UiAssistantStreamField::Reasoning → AssistantMessage.reasoning” 是跨 provider 可见的事件链路，应写回 `reasoning.md` 和 `ui-events.md` 已有 reasoning 描述处。
- “tool-call 后轮内回传 reasoning_content，但 Turn 结束后丢弃”是上下文管理约束，应写回 `reasoning.md` 的 Thinking Block 不进入 recent_chat 章节。

### 跨层纪律

- Provider wire 层不得把 reasoning fallback 成正文。
- Vendor-specific request policy 归 `OpenAiWire` 内部，不上浮到 AgentContext。
- Thinking Mode 下不生效的采样参数由 wire 层按 provider policy 抑制发送，UI 后续可再做提示，但 request body 先保证正确。

### 关联架构文档

以下均为上游 March 项目内路径，不是本仓库内链接：

- `codestable/architecture/DESIGN.md`
- `codestable/architecture/provider.md`
- `codestable/architecture/reasoning.md`
- `codestable/architecture/ui-events.md`

架构总入口需要更新一句 DeepSeek reasoning 表述；不是新增设计入口，只是把旧“DeepSeek-R1 inline tag”刷新为当前官方 Thinking Mode。

### 官方资料

- DeepSeek Thinking Mode: https://api-docs.deepseek.com/zh-cn/guides/thinking_mode
- DeepSeek Models & Pricing: https://api-docs.deepseek.com/quick_start/pricing
- DeepSeek Change Log 2026-04-24: https://api-docs.deepseek.com/updates
