# DeepSeek Thinking Provider: Interface Contracts

> [返回设计决策](deepseek-thinking-provider-design.md) · [继续阅读实现与测试](deepseek-thinking-provider-implementation.md)

## 2. 接口契约

### 2.1 RequestMessage：轮内 assistant reasoning 回传

```rust
let message = RequestMessage::assistant_tool_calls_with_text_and_reasoning(
    Some(MessageContent::from_text("I will inspect the file.")),
    Some("I need to read the target file before editing.".to_string()),
    vec![tool_call],
);
```

序列化为 OpenAI ChatCompletions：

```json
{
  "role": "assistant",
  "content": "I will inspect the file.",
  "reasoning_content": "I need to read the target file before editing.",
  "tool_calls": [
    {
      "id": "call_1",
      "type": "function",
      "function": {
        "name": "read_file",
        "arguments": "{\"path\":\"src/lib.rs\"}"
      }
    }
  ]
}
```

```rust
// 来源：crates/march-core/src/provider/messages.rs RequestMessage
// 来源：crates/march-core/src/provider/wire/shared.rs serialize_openai_message
// 来源：crates/march-core/src/agent/prompting.rs append_assistant_tool_call_message
```

错误路径示例：来自 `recent_chat` 的 assistant final text 不应带 `reasoning_content`：

```json
{
  "role": "assistant",
  "content": "Done."
}
```

```rust
// 来源：crates/march-core/src/provider/messages.rs build_messages
```

### 2.2 DeepSeek request policy

DeepSeek V4 thinking 请求：

```json
{
  "model": "deepseek-v4-pro",
  "messages": [
    { "role": "user", "content": "Use a tool if needed." }
  ],
  "stream": true,
  "thinking": { "type": "enabled" },
  "reasoning_effort": "high",
  "max_tokens": 384000
}
```

约束：

- Thinking Mode 下不发送 `temperature`、`top_p`、`presence_penalty`、`frequency_penalty`。
- `max_tokens` 仍可发送。
- 非 DeepSeek provider 不受此 policy 影响。

```rust
// 来源：crates/march-core/src/provider/wire.rs OpenAiWire::build_request
// 来源：crates/march-core/src/provider/messages.rs RequestOptions
```

禁用 thinking 的未来兼容形态：

```json
{
  "thinking": { "type": "disabled" }
}
```

本 feature 不要求 UI 暴露禁用入口，但 request builder 的 helper 应能表达该状态，避免后续再改 wire contract。

### 2.3 Stream parse：reasoning 与正文分流

输入 SSE data：

```json
{
  "choices": [
    {
      "delta": {
        "reasoning_content": "I should inspect the config first."
      }
    }
  ]
}
```

输出：

```rust
vec![WireStreamDelta::ReasoningDelta(
    "I should inspect the config first.".to_string()
)]
```

UI event：

```json
{
  "kind": "assistant_stream_delta",
  "field": "reasoning",
  "delta": "I should inspect the config first."
}
```

输入正文 SSE data：

```json
{
  "choices": [
    {
      "delta": {
        "content": "I'll read the config now."
      }
    }
  ]
}
```

输出 `WireStreamDelta::ContentDelta(...)`，UI event 的 `field` 为 `"content"`。

```rust
// 来源：crates/march-core/src/provider/wire.rs OpenAiWire::parse_stream_event
// 来源：crates/march-core/src/provider/delivery.rs StreamCollector::ingest_delta
// 来源：crates/march-core/src/ui/backend/messaging.rs send_agent_progress_event
```

### 2.4 Non-stream parse：response 保留 reasoning

输入：

```json
{
  "choices": [
    {
      "message": {
        "role": "assistant",
        "reasoning_content": "Need current date first.",
        "content": "Let me check.",
        "tool_calls": [
          {
            "id": "call_date",
            "type": "function",
            "function": { "name": "get_date", "arguments": "{}" }
          }
        ]
      }
    }
  ]
}
```

输出：

```rust
WireResponse {
    reasoning_content: Some("Need current date first.".to_string()),
    content: Some("Let me check.".to_string()),
    tool_calls: vec![WireToolCall { id: "call_date", name: "get_date", arguments_json: "{}" }],
}
```

```rust
// 来源：crates/march-core/src/provider/wire.rs OpenAiWire::parse_response
// 来源：crates/march-core/src/provider/delivery.rs build_provider_response_from_wire_response
```

主要错误路径：

```json
{
  "choices": [
    {
      "message": {
        "role": "assistant",
        "reasoning_content": "I know the answer.",
        "content": "",
        "tool_calls": null
      }
    }
  ]
}
```

结果：`ProviderResponse.content == None` 且 `tool_calls` 为空，agent runner 报错，不把 reasoning 当 final text。

### 2.5 Persisted/UI timeline：reasoning 只进消息展示，不进 recent_chat

Agent event：

```rust
AgentProgressEvent::AssistantReasoningPreview {
    message_id: "assistant-message-1".to_string(),
    delta: "Need current date first.".to_string(),
}
```

Persisted timeline 更新：

```rust
message.reasoning.push_str(delta);
```

UI event：

```json
{
  "kind": "assistant_stream_delta",
  "message_id": "assistant-message-1",
  "field": "reasoning",
  "delta": "Need current date first."
}
```

```rust
// 来源：crates/march-core/src/ui/backend/messaging.rs apply_agent_progress_to_persisted_timeline
// 来源：crates/march-core/src/ui/types/events.rs UiAssistantStreamField
```

前端已有契约：

```ts
if (event.field === 'reasoning') {
  message.reasoning += event.delta
}
```

```ts
// 来源：src/composables/chatRuntime/chatEventReducer.ts applyAgentEventToTimeline
```

### 2.6 DeepSeek preset 与模型能力

DeepSeek preset：

```rust
VendorPreset {
    id: "deepseek",
    display_name: "DeepSeek",
    protocol: Protocol::OpenAi,
    default_base_url: "https://api.deepseek.com",
    suggested_models: &[
        "deepseek-v4-flash",
        "deepseek-v4-pro",
        "deepseek-chat",
        "deepseek-reasoner",
    ],
    probe_model: "deepseek-v4-flash",
    // ...
}
```

模型能力：

```json
{
  "deepseek-v4-flash": {
    "context_window": 1000000,
    "max_output_tokens": 384000
  },
  "deepseek-v4-pro": {
    "context_window": 1000000,
    "max_output_tokens": 384000
  }
}
```

能力限制：

- `supports_tool_use = true` 应由 settings model 能力默认值或用户选择体现；当前 `model_capabilities.json` 只包含 token 能力，本 feature 不扩展该 JSON schema。
- `reasoning` capability 若代码尚未实现 schema，design 不要求把 `ReasoningCapability` 写入 JSON；DeepSeek thinking policy 先基于 `vendor_preset_id` + model id 识别。

```rust
// 来源：crates/march-core/src/settings/vendor_preset.rs VENDOR_PRESETS
// 来源：crates/march-core/src/model_capabilities.json
// 来源：src/lib/providerBaseUrl.ts providerBaseUrlDefaults
```
