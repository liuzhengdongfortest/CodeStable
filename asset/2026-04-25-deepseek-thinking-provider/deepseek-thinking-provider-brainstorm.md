---
doc_type: feature-brainstorm
feature: 2026-04-25-deepseek-thinking-provider
status: confirmed
summary: 将 DeepSeek 官方 OpenAI-compatible API 正式接入 March，覆盖普通对话、Thinking Mode 与工具调用中的 reasoning_content 轮内回传
tags: [provider, deepseek, reasoning, tool-calls]
---

# DeepSeek Thinking Provider Brainstorm

> Stage 0 | 2026-04-25 | 下一步：design

## 想做什么、为什么

用户想把 DeepSeek 接成 March 的正式 provider，不只是填一个 base URL 能发普通聊天，而是要覆盖 DeepSeek 官方 API 的 Thinking Mode 和 tool calls。

这次讨论前先扫了项目架构和现有代码：March 已经有 Provider 的 `Protocol × VendorPreset` 结构，DeepSeek preset 已存在；架构层也已经把 reasoning 作为跨 provider 的统一能力写进 `codestable/architecture/reasoning.md`。真正缺口不在"有没有 DeepSeek 入口"，而在 DeepSeek 官方 Thinking Mode 的协议细节和 March 当前 wire 层之间还没对齐：

- DeepSeek 官方 OpenAI-compatible Thinking Mode 使用 `thinking: { "type": "enabled" | "disabled" }` 控制开关，使用 `reasoning_effort: "high" | "max"` 控制强度。
- Thinking Mode 下返回的思考内容在 `reasoning_content` 字段里，和 `content` 同级。
- 若某轮 assistant 进行了工具调用，后续请求必须完整回传该轮 `reasoning_content`，否则 DeepSeek API 会返回 400。
- Thinking Mode 下 `temperature`、`top_p`、`presence_penalty`、`frequency_penalty` 不生效，不能把这些参数当作有效运行控制展示给用户。
- DeepSeek 当前官方模型入口已更新为 `deepseek-v4-flash` / `deepseek-v4-pro`；旧 `deepseek-chat` / `deepseek-reasoner` 已标注未来废弃。

因此，本 feature 的真问题是：**让 March 能以 DeepSeek 官方 OpenAI-compatible API 运行普通对话、thinking 模式和工具调用，并把 DeepSeek 的 `reasoning_content` 纳入 March 现有 reasoning 分层，而不是把它混进正文或 recent_chat。**

## 考虑过的方向

### 方向 A：最小接入

- 更新 DeepSeek preset 的 base URL / suggested models / 默认能力，让用户填 key 后能跑普通聊天。
- 价值：最快能用，改动小。
- 代价：Thinking Mode 和工具调用中的 `reasoning_content` 仍然没有被正式建模；一旦 DeepSeek 在工具调用后要求回传 reasoning，March 可能在 agent loop 中收到 400。
- 结论：否决。用户要的是正式可用，包含 thinking + tool calls，不是普通 chat 的浅接入。

### 方向 B：DeepSeek Thinking 正式接入

- 更新 DeepSeek preset 和内置模型能力，包含 `deepseek-v4-flash` / `deepseek-v4-pro`。
- 在 OpenAI ChatCompletions wire 层支持 DeepSeek Thinking Mode 的请求参数：`thinking` 与 `reasoning_effort`。
- 流式和非流式都把 `reasoning_content` 解析成 March 内部 reasoning 流，正文继续走 `content`。
- Agent loop 中若 DeepSeek assistant 消息带 tool calls，必须在轮内历史里保留并回传对应 `reasoning_content`。
- Thinking Mode 下抑制或忽略不生效的采样参数，避免 debug request 和 UI 语义误导。
- 价值：完整覆盖用户真正需要的 DeepSeek provider 能力，且贴合 March 既有 reasoning 架构。
- 代价：需要触碰 provider wire format、stream collector、RequestMessage 轮内结构、模型能力和少量 UI 参数显隐逻辑。
- 结论：选定。

### 方向 C：统一 Reasoning 参数系统

- 顺手补齐 Anthropic / OpenAI / Gemini / DeepSeek 的 reasoning 控件、TaskRunParams、能力 schema 和所有 UI 细节。
- 价值：reasoning 体系一次性更完整。
- 代价：范围明显扩大，已经接近一组 feature；容易把 DeepSeek 接入和全局 reasoning 体系重做混在一起。
- 结论：否决。本次只做 DeepSeek 正式接入所需的最小 reasoning 扩展；若发现通用参数结构缺口，design 阶段只补必要接口，不做全局 UI 重做。

## 已敲定的设计点

- 已确认：本 feature 走"方向 B：DeepSeek Thinking 正式接入"，范围包含普通对话、Thinking Mode、tool calls。
- 已确认：DeepSeek 仍走现有 `Protocol::OpenAi` / Chat Completions wire adapter，不新增 `Protocol` 变体；厂牌身份继续由 `vendor_preset_id = "deepseek"` 承载。
- 已确认：DeepSeek 的 `reasoning_content` 是轮内 provider 协议事实，不能进入 `recent_chat`；这符合 March "Thinking block 不进入 recent_chat" 的架构原则。
- 已确认：有 tool calls 的 DeepSeek assistant 消息必须在本 Turn 的后续 provider 请求里带回 `reasoning_content`，这是官方 API 约束，不是 UI 展示需求。
- 倾向：把 DeepSeek Thinking Mode 建模为现有 `ReasoningStyle::InlineTag` 的扩展或重命名后的 OpenAI-compatible visible reasoning style，而不是引入全新上层概念。
- 倾向：DeepSeek 官方 base URL 更新为 `https://api.deepseek.com`；保留 `/v1` 兼容只作为用户 override 能力，不继续作为 preset 默认值。
- 待验证：DeepSeek `thinking` 字段在 Rust 自建 wire 层应直接作为 Chat Completions body 字段发送，还是需要特殊放入与 OpenAI SDK `extra_body` 等价的位置。由于 March 不经 SDK，design 阶段应以实际 HTTP body 为准。

## 选定方向与遗留问题

选定方向是：**DeepSeek Thinking 正式接入**。这次 feature 应从 provider wire 层把 DeepSeek 官方 Thinking Mode 作为一等兼容场景处理：请求时可控制 thinking 开关和强度，响应时把 `reasoning_content` 和 `content` 分流，工具调用后按官方要求在轮内历史中回传 reasoning，最终仍只把正文写入持久化 recent_chat。

明显不做：

- 不做全局 reasoning 控件 UI 大改；只做 DeepSeek 正式可用所必需的参数入口和能力识别。
- 不新增 DeepSeek 独立协议 adapter；DeepSeek 官方 OpenAI-compatible API 仍归入 OpenAI Chat Completions 分支。
- 不接 DeepSeek Anthropic API 格式；本 feature 聚焦用户给出的 OpenAI-format Thinking Mode 文档。
- 不把 reasoning 内容持久化进 recent_chat 或 Notes。

遗留给 design 的问题：

1. `RequestMessage` 是否需要新增 `reasoning_content: Option<String>` 字段，或引入更通用的 `ReasoningBlock` 轮内结构，以支持 tool-call 子轮回传。
2. `ProviderProgressEvent` 是否要新增 `ReasoningDelta`，让 DeepSeek 流式 `reasoning_content` 进入 UI 的 `assistant_stream_delta { field: "reasoning" }` 链路，而不是复用 `ContentDelta`。
3. 非流式响应中 `reasoning_content` 该如何进入 debug trace 和 UI：是否只在最终 `ProviderResponse` 增加 reasoning 字段，还是统一走一套"响应解析后补发 reasoning event"机制。
4. DeepSeek Thinking Mode 的运行参数如何挂到现有 `RequestOptions`：是先加 DeepSeek-specific 字段，还是先落通用 `reasoning_enabled` / `reasoning_effort` 的最小版本。
5. Thinking Mode 下不生效的采样参数如何处理：请求层直接不发送，还是保留发送但在 debug / UI 中提示不生效。
6. 模型能力表应如何更新：`deepseek-v4-flash` / `deepseek-v4-pro` 的 context / max output / tool calls / reasoning 能力以官方模型页为准，旧 `deepseek-chat` / `deepseek-reasoner` 是否保留为兼容 suggested models。
7. 现有 `codestable/architecture/reasoning.md` 里 DeepSeek 描述偏旧，design 阶段需要同步更新架构文档，使其反映官方 Thinking Mode、`thinking` 开关、`reasoning_effort`、tool-call 回传约束。

官方文档来源：

- DeepSeek Thinking Mode: https://api-docs.deepseek.com/zh-cn/guides/thinking_mode
- DeepSeek 首次调用 API / base URL / 模型说明: https://api-docs.deepseek.com/zh-cn/
