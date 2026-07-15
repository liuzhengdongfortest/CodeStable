# Refactor Fastforward Protocol

用户说"优化一下这个函数"而改动明显很小（单函数变长、组件里抽个 composable、一段重复代码合并）时走完整三阶段太重。fastforward 让 AI 像平时一样直接改但守住底线——行为等价、引用经典方法、跑测试自证。

很轻：没有 scan、design 或 checklist；只保留一个机器可读 state，改完一句话汇报。

## Spec

```haskell
data FastForwardStage = Apply | Verify | CodeReview | ResolvePartial | WriteNote
data ApprovalState = ApprovalMissing | ApprovalPending | ApprovalApproved | ApprovalRejected
data PartialDisposition
  = NoPartialChanges | DispositionMissing | DispositionPending
  | KeepForStandard | DiscardApproved
data FastForwardOutcome
  = Run FastForwardStage | PersistCheckpoint CheckpointReason
  | Checkpoint CheckpointReason | RouteStandard | Complete

eligible :: FastForwardState -> Bool
eligible s = and
  [ behaviorPreserving s, changedFiles s <= 1, changedLines s <= 100
  , changePoints s <= 3, hasBehaviorSafetyNet s
  , not (requiresVisualValidation s), not (changesPublicApi s)
  , not (crossesModuleBoundary s)
  ]

advance :: FastForwardState -> FastForwardOutcome
advance s
  | (not (eligible s) || complexityExpanded s)
  , partialDisposition s == DispositionMissing
                                      = PersistCheckpoint PartialChangeDisposition
  | (not (eligible s) || complexityExpanded s)
  , partialDisposition s == DispositionPending
                                      = Checkpoint PartialChangeDisposition
  | (not (eligible s) || complexityExpanded s)
  , partialDisposition s == DiscardApproved
                                      = Run ResolvePartial
  | not (eligible s) || complexityExpanded s = RouteStandard
  | alignmentApproval s == ApprovalMissing
                                      = PersistCheckpoint ConfirmMethodAndScope
  | alignmentApproval s == ApprovalPending
                                      = Checkpoint ConfirmMethodAndScope
  | alignmentApproval s == ApprovalRejected = RouteStandard
  | not (changesApplied s)                   = Run Apply
  | not (verificationPassed s)               = Run Verify
  | not (codeReviewPassed s)                 = Run CodeReview
  | effectApproval s == ApprovalMissing      = PersistCheckpoint ConfirmEffect
  | effectApproval s == ApprovalPending      = Checkpoint ConfirmEffect
  | effectApproval s == ApprovalRejected     = RouteStandard
  | noteRequested s && not (noteExists s)    = Run WriteNote
  | otherwise                                = Complete
```

每个 `Run` 前后都更新 `{slug}-ff-state.yaml`；进入 `CodeReview` 前写 `status: review-pending`，
review 返回后从该文件恢复。`PersistCheckpoint` 先写 state + pending `approval-report.md`，再停等
显式 owner 输入。`Complete` 同时把 state 写成 `status: complete`，不能只靠聊天里的完成汇报。
owner 输入只来自主入口已与当前 pending reason 精确匹配的 `ResumeRefactorCheckpoint`。
`PartialChangeDisposition` 只接受 `KeepPartialChanges` / `DiscardPartialChanges`，分别持久化为 `KeepForStandard` / `DiscardApproved`；其他通用 approve/reject/revise 输入一律 fail-closed，不存在未建模的 stash 选项。

## 执行前检查与完成 gate

CodeStable 不决定分支或检出策略；按当前宿主 / owner 已选择的检出环境推进。改动前先确认当前 dirty scope，只把和本次小重构相关的改动纳入结果。

自证通过、提交前进入 `cs-code-review` 做独立 diff 评审；blocking 未清零、important 未处理或未被 owner 明确接受时不算完成。需要 commit 时按仓库既有提交规范或 owner 指示执行。

---

## 入场 3 条硬检查（不过就退完整流程）

先做 `shared-conventions.md` 第 7 节的**第一性原则 pre-pass**：外部行为必须不变，不可破约束是公开接口和现有测试，最小充分改动必须能对应到经典重构方法；无法从这些推出的"顺手优化"都不做。若重写涉及实现手段选择（正则替代结构化处理等），做 `.codestable/reference/solution-depth-conventions.md` 的方案深度 pre-pass，按场景论证不图省事。

任一 `eligible` 条件不满足就退到 standard：行为必须不变；范围最多 1 文件、100 行、3 个动点；
必须有能观察行为的 safety net，且不涉及目视验证、公开接口或跨模块边界。没测试时可先补
characterization test，再重新判定。

完整 scan 阶段是 7 条入场检查，这里压成最关键 3 条——剩下 4 条（跨模块 / 全口味 / 生成代码 / 扫不完）在"范围真的小吗"里已被隐含排除。

---

## 用经典方法不发挥

fastforward 不读完整方法库，但要守住"**每一处改动都能对应到一个经典重构方法**"。AI 心里想不出"我这步是 Extract Function / Memoization / Guard Clauses / ..." 里的哪一个 → 这次不是简单重构退完整流程查方法库。

常用方法（覆盖 fastforward 80% 场景）：

- **Extract Function**：> 5 行、内聚、能命名的片段 → 抽出独立函数
- **Extract Variable**：复杂表达式 → 命名变量或 query
- **Guard Clauses**：开头多层嵌套 if 检查 → 提前 return 拉平
- **Decompose Conditional**：复杂 if 条件 → 命名为布尔函数
- **Extract Composable / hook**：组件里封闭的状态 + 副作用 → 独立 composable / hook
- **Memoization**：重复计算 → computed / useMemo
- **Cancellation**：副作用缺 cleanup → 加 onUnmounted / useEffect return

想做的动作不在这几种里、不是开箱即用的经典方法（涉及 Parallel Change / Strangler Fig / 分层纠偏）→ 退完整流程。

---

## 流程

### 1. 一次对齐

一句话回用户：**"我打算做 {方法名}，动 {具体文件/函数}，改动点 {N} 处，预计影响 {范围}。确认就开干。"**

确认就下一步。用户说"还有个 X 要改"——评估 X 是否破坏入场 3 条，破坏了就退完整流程。

### 2. 改

按经典方法步骤改。不产出 design doc / checklist，代码直接落盘。

### 3. 自证

- 跑测试（单元 / 集成 / 类型检查 / lint）
- grep 检查旧引用是否清理干净（做了 Extract / Inline 这类）
- 改了前端状态逻辑跑类型检查 + 已有测试；**不做 UI 目视验证**——要 UI 目视就不该走 fastforward
- 自证通过后进入 `cs-code-review`；blocking 未清零、important 未处理或未被明确接受时不进 commit

### 4. 一句话汇报

```
✓ 已完成。方法：{方法名}。改动：{文件路径:行号范围}。验证：{跑了什么测试 / 通过情况}。
```

有偏离 / apply 过程中发现想再改点别的 → **停下问用户不发挥**。

---

## 文件产出

始终建 `.codestable/refactors/{YYYY-MM-DD}-{slug}/{slug}-ff-state.yaml`，只保存恢复所需的最小状态：

```yaml
mode: fastforward
status: aligning # aligning | applying | verifying | review-pending | effect-pending | complete | switch-required
method: ExtractFunction
scope: [src/example.ts]
alignment_approval: pending # missing | pending | approved | rejected
partial_disposition: no-partial-changes
verification: pending
review_status: missing
effect_approval: missing
```

用户明确“留记录”时再加 `{slug}-refactor-note.md`；仍不写 design / checklist。

---

## 什么时候跳出 fastforward

改到一半出现以下任一，**停下告诉用户"比预期复杂，建议切回完整流程"**：

- 改动点从 3 个涨到 5+
- 发现要动的文件不止 1 个
- 冒出一个不在常用方法清单里的动作
- 发现没有测试能覆盖
- 用户追加"顺便改一下 X"带入行为改动
- 改完 AI 自证失败且不是简单修正能搞定

切回前先把 `status: switch-required` 和本轮可归因路径写入 state。默认保留改动进入 standard
scan；若 owner 要丢弃，先写 pending `PartialChangeDisposition` approval。只有 owner 明确选择丢弃后，
才在 `ResolvePartial` 对本轮精确路径执行恢复；禁止裸 `git restore`、禁止触碰 baseline dirty 文件。

---

## 不做什么

- **不写 scan / design / checklist** —— 写了就违背 fastforward 存在的理由
- **不跨多文件改** —— 跨文件就不是"小重构"
- **不做需要 HUMAN 目视的改动** —— 前端渲染 / 交互 / 性能感知要人看的走完整流程
- **不碰公开接口** —— 改公开接口要走 Parallel Change，不是 fastforward 能做的

---

## 容易踩的坑

- **把"小"判断得太宽**：用户说"小重构"但实际动 3 个文件——AI 要老实说"这不算小"
- **跳过入场 3 条检查就开干**：这个技能的意义就在这 3 条
- **自证偷懒**：只跑类型检查不跑单元测试，或完全不 grep 旧引用
- **改中发挥**：看到邻居代码也"顺手改改"——fastforward 范围在确认那一刻就锁死
- **行为改动伪装成重构**：加新参数、改返回值格式——这是行为改动伪装不了

---

## 相关

- `cs-refactor` 主入口 — refactor 流程骨架
- `references/library/methods.md` — 完整方法库
- `.codestable/reference/system-overview.md` — CodeStable 体系总览
