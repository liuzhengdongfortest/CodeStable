---
doc_type: feature-design-review
feature: 2026-07-17-lean-workflow-artifacts
status: passed
review_state: passed
review_reason: ""
reviewer_id: ""
reviewed: 2026-07-17
round: 4
---

# lean-workflow-artifacts feature design 审查报告

## 1. Scope And Inputs

- Design: `.codestable/features/2026-07-17-lean-workflow-artifacts/lean-workflow-artifacts-design.md`
- Checklist: `.codestable/features/2026-07-17-lean-workflow-artifacts/lean-workflow-artifacts-checklist.yaml`
- Intent / brainstorm: none
- Roadmap: none
- Related docs: `.codestable/requirements/demand-driven-skill-runtime.md`
- Reviewed SHA-256: design `08763d1e0e4380b4043c503e559aaf4c6ac5d2dd461a72a8021e4cfdf41cfae8`; checklist `ee8efe38dd7780b9e41e6a33c9377a936f0b38249253df50ef1aa6de0db5773f`
- Focused-closure SHA-256: design `9b5dd46c02ebe01ec482f134c3451785a20289b78b69ebd2a0b624b8454fa314`; checklist `6f621219f2b537f08e68682271ef318672eef2c57759bbe466328622725d0a0c`
- Code facts checked: `cs-code-review` report/independent-review contracts、`cs-feat` QA/acceptance/implementation/Goal protocols、`build-review-packet.py`、`codestable-workflow-next.py`、`codestable_common.py`、Goal consistency gate 与相关 tests

### Independent Review

- Status: completed
- Detection: independent-agent
- Provider / agent: `claude/claude-opus-4-8`, `95042d32-c775-460d-96b9-10d4633aecdc`
- Raw output: round 4 无 blocking、无 important；3 条 nit 与 1 条 suggestion 已经 focused closure 吸收
- Merge policy: reviewer 结论已按仓库事实逐条本地核验；只合并可证实 findings
- Gate effect: none

Review history：round 1/2 先收口 freshness、packet 挂载点和 compact template；round 3 发现 typed QA block 会引入新的 Standard/Goal/acceptance 恢复状态机，因此从 v0.1 删除该 slice；round 4 对收窄后的完整设计独立复审通过。首个 round 3 agent `2132d2e4-5429-4505-8c11-180e3e6ff479` 因 provider turn 卡死未产出 verdict，已按 reviewer failed 归档；替补 `efda113b-51de-4092-a2af-f649f85f0375` 的 blocking 已被 round 4 输入消化。

## 2. Design Summary

- Goal: 减少不必要的中间产物、packet 内联和跨阶段全文重读，同时把 QA 固定为行为测试职责。
- Key contracts: human document / workflow receipt / ephemeral transport 三分；按 consumer projection 加载；review/Goal QA passed 紧凑、异常状态详细；workspace locator 与 scoped portable 分离。
- Steps: 5；风险热点是 legacy packet 逐字节兼容、compact template 下游投影、QA/acceptance 职责边界。
- Checks: 18；覆盖 artifact admission、transport、review/QA projection、resolver compatibility、skill boundary 和 evidence dedup。
- Baseline / validation: 当前 portable packet 实测约 712KB 且带入 41 个无关 untracked 文件；实现后以 golden、内容缺席、artifact/read-set/packet bytes 和 dogfood trace 证明收益。

## 3. Findings

### blocking

none

### important

none

### nit

- [x] FDR-401 compact QA 省略 Command Results / Scenario Results / Cleanliness 时，acceptance 的硬枚举需改成 projection/如有。
- [x] FDR-402 QA 移除 Cleanliness 后，明确由 code review、DoD cleanliness 与 final audit 继续承担。
- [x] FDR-403 共享 artifact reference 同时点名 `cs-onboard/references/` 模板源与 `.codestable/reference/` runtime 副本。

### suggestion

- [x] FDR-404 `tests/test_review_packets.py` 明确断言 workspace transport 不含正文或 fenced code body。

### learning

- QA 角色收紧与 QA recovery FSM 是两个独立问题；为前者引入 typed block 会产生 receipt consumption 和 Goal handoff 恢复成本，应单独设计。
- compact artifact 的兼容锚点是 canonical 路径和 frontmatter，而不是固定正文篇幅。

### praise

- 持久化与加载深度拆开决策，直接对应“少落盘”和“少重复加载”两个不同成本。
- 诚实限定 packet 收益只发生在 file-handoff/remote，不把现有 locator reviewer 虚报为新增优化。
- QA 明确覆盖 functional/integration/E2E/browser/API/CLI/manual 场景，不再承担代码质量复审。

## 4. User Review Focus

- 用户需要重点拍板：v0.1 不新增 artifact store、digest wire、QA block state 或 resolver 分支；保留 human-facing design/decision/acceptance，压缩或不持久化可重建过程材料。
- implement 需要重点遵守：legacy packet 无新 flag 时逐字节兼容；workspace/scoped transport 必须 allowlist；compact review/QA 保留所有 gate/runner/lane 恢复字段；failed/blocked 保持 detailed。
- code review / QA / acceptance 需要重点复核：QA 必须实际运行行为场景；acceptance 只消费 projection/如有章节；token 收益必须有 bytes/read-set/dogfood 数据。

## 5. Evidence Confidence Ledger

| Check | Verdict | Evidence Class | Basis | Follow-up |
|---|---|---|---|---|
| Acceptance Coverage Matrix | pass | E | S1-S9 均映射 step 与 evidence，core 标记完整 | implementation 逐项留证据 |
| DoD Contract | pass | E | DoD gate passed；CMD-001..005 均有 core/failure handling | 实现后执行全部命令 |
| Steps and checks traceability | pass | E | 5 steps 与 18 checks 覆盖挂载点和反向边界 | checklist 即时更新 |
| Roadmap contract compliance | n/a | C | direct Standard feature，无 roadmap owner | none |
| Module interface design | pass | C | packet flags 是现有 builder 的 additive transport seam；无新依赖 | golden 锁 legacy bytes |
| Validation and artifacts | pass | C | runtime 仅读 compact artifact frontmatter；packet baseline 已实测 | 实现后比较 before/after |

Summary: E=3, C=3, H=0, H-only core checks=none。

## 6. Residual Risk

- QA 的“不默认读源码/diff”是协议与 dogfood 纪律，不是 runtime sandbox；由 scenario fixtures 与 read trace 抽查。
- legacy portable 逐字节兼容尚待实现期 golden 锁定；默认 flag 分支不得触碰旧 serializer 行为。
- compact 带来的 token 收益尚待实际度量；不能用文档行数代替 packet/artifact/read-set bytes。
- 既有 QA failed/blocked 恢复语义保持原样，其状态机债务不在本 feature 修复。

## 7. Verdict

- Status: passed
- Next: 交给用户整体 review，停在 owner `ConfirmDesign`；未经明确批准不得进入 implementation。

## 8. Focused Closure

- Closed findings: FDR-401, FDR-402, FDR-403, FDR-404
- Attributed delta: design decision 4、挂载点 1、packet step 2；checklist packet/acceptance/Cleanliness checks
- Verification: YAML validation passed；DoD contract gate passed；`git diff --check` passed；focused-closure SHA 已记录
- Classification: 只把 round 4 已在范围内的责任归属、模板路径与测试断言写显式；未改变行为、公开契约、架构边界、验收语义或 feature 范围，因此不增加 round、不启动新 reviewer。
