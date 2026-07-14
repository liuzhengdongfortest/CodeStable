# Feature Acceptance Reference

## Global Route Governance

`cs-feat` acceptance 阶段默认是 L3：它可能写长期 architecture / requirement / roadmap 状态，并决定 feature 是否可进入 finish / merge。必须遵守全局 route governance：

- requirement 不允许在 accept 阶段自由重写；
- capability-boundary 变化必须先有 owner-approved requirement delta；
- 没有 delta 但需要改 requirement 时，停止并写对应 unit 的 `approval-report.md`（格式见 `.codestable/reference/approval-conventions.md`）；
- code / design / requirement / architecture / decision 冲突时，先运行只读 analyze pass，记录 finding，再等 owner 判断；
- 小范围、无 requirement 影响的 feature 可以记录 skip，不生成 delta；
- roadmap `status` 只做机械完成状态回写，不替 owner 改 scope。

## requirement delta / clarification 回写：7 分支判据

对照方案 frontmatter 的 `requirement`、第 1 节需求摘要、feature 目录下已有 `*-req-delta.md` 和 clarifications，逐条判定（这是受 delta 约束的实际写文件动作，不是自由重写 requirement 的机会）：

```haskell
data RequirementRef = NoRequirement | DraftRequirement | CurrentRequirement
data CapabilityImpact = NoCapabilityChange | NewCapability | BoundaryChanged | NoUserVisibleChange
data DeltaState = ApprovedDelta | NoApprovedDelta
data ReqWriteback
  = SkipRequirement | NeedBackfillApproval | ApplyDeltaAndMarkCurrent
  | ApplyDeltaAndLog | NeedDeltaApproval | RequirementUnchanged
  | InvalidRequirementState

writeback :: RequirementRef -> CapabilityImpact -> DeltaState -> ReqWriteback
writeback NoRequirement NoCapabilityChange _       = SkipRequirement
writeback NoRequirement NewCapability _            = NeedBackfillApproval
writeback DraftRequirement _ ApprovedDelta         = ApplyDeltaAndMarkCurrent
writeback DraftRequirement _ NoApprovedDelta       = NeedDeltaApproval
writeback CurrentRequirement BoundaryChanged ApprovedDelta = ApplyDeltaAndLog
writeback CurrentRequirement BoundaryChanged NoApprovedDelta = NeedDeltaApproval
writeback CurrentRequirement NoUserVisibleChange _ = RequirementUnchanged
writeback _ _ _ = InvalidRequirementState
```

`NoCapabilityChange` 只和 `NoRequirement` 配对；已有 current requirement 且没有用户可见变化时用
`NoUserVisibleChange`。`CurrentRequirement + NewCapability` 表示 impact 分类错误或 requirement 已过期，
保留为 `InvalidRequirementState` 并停下复核，不静默当作 unchanged。

`NeedBackfillApproval` / `NeedDeltaApproval` 都先写 `approval-report.md`，不在 acceptance 内直接落 current。

## 最终审计（final audit）完整步骤

9 节报告填完、checks 全部 `passed` 之后，**还不能直接宣布完成**。再跑一轮 final audit，用最终工作区反查原始设计：

1. **重读原始契约**：重新打开 `{slug}-design.md` 第 1 / 2 / 3 / 4 节和 `{slug}-checklist.yaml`，不要只看实现汇报或验收报告草稿。
2. **聚合命令复验**：重跑本 feature 相关的 build / typecheck / lint / test；功能性前端改动重跑浏览器验证；非功能性前端改动复核替代证据；把命令、退出码、关键输出写入报告末尾"最终审计"。
3. **场景抽样复核**：对第 3 节所有可自动验证的场景尽量重跑；对截图 / 手工类标 `trust-prior-verify` 时写清依赖的证据来源。功能性核心路径不能仅靠 `trust-prior-verify` 或 residual-risk 通过；无法在当前环境验证时写 `blocked`，除非 design 预先定义为条件性非阻塞并已验证替代路径。非功能性 feature 可以用静态 / 一致性 / 目标测试证据完成复核。
4. **交付物复核**：对照 design 的交付物清单和 implement 的实际交付物索引，逐项检查代码入口、配置 key、schema、路由、文档归并、roadmap 状态是否真实存在于最终工作区 / diff 中；不要只在报告里写"已建议"。
5. **完整工作区复核**：看 `git status` + `git diff`，确认未跟踪文件、暂存文件、未暂存文件都被纳入判断。验收不能只看最近 commit；本地未提交文件也可能是交付物或污染源。
6. **diff 清洁度复核**：检查本次新增 debug 输出、临时 TODO/FIXME、注释掉代码、无用 import、方案外文件；发现就修或记录为用户确认的遗留。
7. **知识沉淀复核**：第 8 节候选是否已经分流到 attention / learning / decide / guide / libdoc 的退出提示；不要让可复用经验只留在验收报告里。
8. **覆盖率诚实标记**：在报告末尾写 `re-verified` 和 `trust-prior-verify` 数量。trust-prior 比例高于 30% 时，明确提醒用户哪些 UI / 手工项需要终审肉眼确认。

final audit 发现任何缺口：

- 先把对应 checklist check 改回 `failed`；
- 定位属于代码、方案、架构、req、roadmap 哪一类；
- 写一段"缺口修复说明"：只针对失败项，禁止顺手扩范围；修复后重新跑对应验收节和 final audit；
- 同一缺口连续三轮仍失败，停止并向用户交还：列缺口、三次尝试、建议下一步；不要写"通过"。

验收报告在第 9 节后追加：

```markdown
## 10. 最终审计

- 验证证据来源：`{slug}-qa.md` / accept-inline verification
- Evidence sources：`{slug}-evidence-pack.md` / `{slug}-dod-results.json` / `{slug}-gate-results.json`
- Inline Verification Matrix（无 QA 报告时必填）：{ID / 来源 / 核心性 / 命令或动作 / 结果}
- 聚合命令：{命令 + 退出码 + 摘要}
- 场景复核：re-verified {N} / trust-prior-verify {M}
- 交付物复核：代码 / 配置 / schema / 路由 / 文档 / architecture / requirement / roadmap {通过 / 缺口}
- 完整工作区复核：git status / tracked diff / untracked files {通过 / 缺口}
- diff 清洁度：{通过 / 修复项 / 用户确认遗留}
- 知识沉淀出口：attention / learning / decide / guide / libdoc 候选 {已分流 / 无候选}
- 结论：通过 / 有缺口（含处理记录）
```

## 容易踩的坑

- "测试都过了" → 测试通过 ≠ 验收场景满足，要逐条核对第 3 节
- "没跑过 `cs-feat` QA 阶段所以不能 accept" → 不对。standalone accept 可以现场补同等验证证据；goal 模式才强制独立 QA 报告
- "QA passed" → QA frontmatter 通过 ≠ 可直接验收；还要确认功能性核心路径没有被塞进 residual-risk，非功能性 feature 的替代证据足够
- "我肉眼看了一下" → 按清单走，逐项勾选
- 接口偏差在报告里写"已知偏差"而不修代码 / 回填方案
- 挂载点反向核对只看清单不 grep——漏记的挂载点溜进项目，后面拔不干净
- 第 3 节功能性前端改动只 typecheck 没浏览器跑过
- 第 5 节归并写"整体不影响架构"一句话带过，没逐条核查
- 架构 doc 需要更新而只写"建议以后更新"——归并是当下动作不是建议
- 第 7 节只改 items.yaml 没同步主文档，两份不一致
- frontmatter 有 `roadmap` 却在第 7 节写"跳过"——有值就必须回写
- 相信实现汇报而不重读 design / checklist 做最终审计——后续改动可能已经破坏前面 step
- 只看 commit 不看完整工作区——未跟踪文件可能漏验，未暂存临时代码可能混进交付
- 交付物只听实现汇报不查文件 / 配置 / 文档 / roadmap 状态——"说完成"不等于真的落盘
- final audit 发现缺口但为了流程闭环写成"遗留"——真正的验收缺口要先修再通过
- 报告写完没让用户终审就宣告完成
- 用户没明确同意就 `git commit`
- **accept 阶段自由重写长期 requirement**——必须走 owner-approved delta，缺 delta 就停下写 `approval-report.md`
