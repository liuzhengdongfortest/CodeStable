# Artifact 持久化与读取约定

本文件由 `cs-onboard` 同步到项目 `.codestable/reference/artifact-conventions.md`。仅在决定是否写 artifact、或决定某个消费者需要读到什么深度时按需加载；不要在每个 skill 启动时读取。

持久化与读取深度是两个独立判断：文件值得保留，不代表每个下游都要读全文；当前 agent 需要一段信息，也不代表必须为它新建文件。

## 持久化判断

按顺序判断：

1. 内容是否承载 owner 意图、设计理由、长期知识或最终交付结论？是则写完整 **human document**。
2. 是否有 gate、断点恢复或下一阶段必须消费的状态、开放项、残余风险？是则写最小 **workflow receipt**。
3. 是否只服务当前 run 或 agent 传输，且**可从仓库事实重建**？是则作为 **ephemeral transport**，默认不进入 workflow unit。
4. 临时材料里出现影响设计、公开契约或后续恢复的结论时，把结论晋升到对应 human document 或 workflow receipt；不要为了保留结论而保存整份原始材料。

| 类型 | 默认持久化 | 典型内容 |
|---|---|---|
| human document | 完整落盘 | requirement、design、ADR、owner decision、最终 acceptance |
| workflow receipt | 最小投影 | review/QA verdict、runner/lane 恢复字段、开放 finding、QA focus、residual risk |
| ephemeral transport | 不进入 unit | packet、raw reviewer 输出、完整成功日志、diff 副本、可重建的中间摘要 |

已有 canonical 路径、`doc_type` 和 `status` 保持兼容。不要为上述分类给每个 artifact 新增分类字段，也不要引入通用 artifact store、receipt service 或 runtime journal。

## 读取深度判断

消费者先读完成职责所需的 **consumer projection**，只有命中 drill-down 条件才读 canonical 全文或原始证据。

| 消费者 | 默认 projection | drill-down 后 |
|---|---|---|
| implementation | approved design、checklist 当前 step、当前 fix item | design gap 或范围冲突时回完整设计与 owner |
| code review | canonical spec locator、live code/diff、验证引用 | finding 需要时读取相关完整证据 |
| QA / accept-inline | design 行为场景、运行入口、review 的 QA focus / residual risk | 测试失败或 blocked 时读取相关日志、fixture、配置或代码 |
| acceptance | design 与 owner 事实、review/QA verdict 和开放风险投影 | 状态冲突、缺字段或验收证据不足时回源 |
| Goal evidence consumer | evidence pack 状态与引用投影 | failed、warning 或摘要不一致时读取 raw DoD/gate JSON |

drill-down 条件包括：

- verdict 不是 passed，或存在开放 finding / residual risk；
- freshness、scope、identity 或恢复字段无法确认；
- evidence 出现 failed、warning、缺字段或摘要不一致；
- projection 无法支持当前职责的明确判断；
- owner 明确要求查看完整材料。

不得把“按需读取”实现为盲信摘要。命中条件时必须回源；未命中时不要同时全文加载 receipt、原始日志和可从其重建的重复证据。

## 写入与消费约束

- passed receipt 只保留完整 frontmatter、下游 projection 和恢复锚点；failed / blocked / changes-requested 使用 detailed variant。
- raw agent 输出被 owner 合并核验后丢弃；material finding 写入 canonical review/design/issue artifact。
- packet 优先使用当前 workspace locator；只有 file-handoff / remote 场景才生成 scoped portable 内容包。
- Standard accept-inline 的行为验证直接进入 acceptance，不额外制造 QA 文件；Goal 仍保留 canonical QA receipt。
- 完整成功输出只保留命令、状态、摘要与 locator；失败输出保留足够诊断和复测的信息。
