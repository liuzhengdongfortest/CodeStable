---
name: cs-code-review
description: "Code review gate。实现完成后做首次独立审查；review-fix 后按变化风险选择 focused closure 或完整独立复审。这是只读横切 gate，不实现代码、不替代 cs-audit。"
argument-hint: "[--range <git-range>] [scope]"
contracts:
  - grep: "{slug}-review.md"
  - grep: "reviewer"
  - grep: "只读"
  - grep: "blocking"
  - grep: "references/independent-review/protocol.md"
  - grep: "focused closure"
  - grep: "progressive reference loading"
  - not-grep: "git push"
  - not-grep: "read all references"
---

# cs-code-review

## 启动必读

动作前先跑 CodeStable preflight：读 `.codestable/attention.md`（缺失先 `cs-onboard`）；不要用 `AGENTS.md`/`CLAUDE.md` 等外部入口代替它；细则见 `.codestable/reference/execution-conventions.md`。

本技能是**横切代码审查 gate**：任何流程实现完成后、commit / QA / 验收前做首次独立只读 review；已有 review 的修复 diff 先分类，再做 focused closure 或完整独立复审。它只读代码和产物，只写 `{slug}-review.md`，不直接修代码、不更新 checklist、不改 spec。

审查目标不是追求完美代码，而是确认本次改动没有降低系统代码健康，并且确实朝对应 spec（design / fix-note / refactor-design / 用户确认范围）的目标前进。能自动格式化或 lint 的问题不要手工阻塞；会影响正确性、维护性、安全、性能、可测试性、需求满足或后续验收可信度的问题必须指出。

> 共享路径与命名约定看 `.codestable/reference/shared-conventions.md` 第 0 节。
> 报告语言：code review 报告正文默认用**中文**（见 `.codestable/attention.md` 报告语言节）；frontmatter / yaml 字段不翻译。

`cs-code-review` 是只读横切审查 gate（单一职责，不是 stage 编排型 workflow）：一次调用只审当前变更范围、产出一份 `{slug}-review.md`，不路由子阶段。下方 `## Spec` 是前门契约，正文「进入来源」「启动检查」「审查流程」「严重度」「退出条件」是方法论主体。

## Spec

```haskell
csCodeReview :: ReviewRequest -> ReviewOutcome
data ReviewRequest = ReviewRequest
  { entrySource : Maybe Source        -- feat | feat-ff | issue | refactor | refactor-ff | ad-hoc
  , gitRange    : Maybe Text          -- --range；缺则审工作区 unstaged/staged diff
  , resumeInput : Maybe ReviewResume  -- pending lane result 或 self-review downgrade
  , repoFacts   : RepoFacts           -- attention + spec 产物 + git diff，优先于聊天历史
  }
data Source = Feat | FeatFf | Issue | Refactor | RefactorFf | AdHoc
data ReviewState = ReviewState        -- 从来源 spec、review report lane 字段和 git diff 恢复
  { source        : Maybe Source
  , specFinalized : Bool              -- 来源 spec 产物存在且已定稿（feature: checklist 全 done）
  , diffAttributed : Bool            -- 当前 diff / staged / range 里有本轮可归因改动
  , laneA         : LaneStatus        -- 环节 A 独立 Task agent review（gate 必需）
  , laneB         : LaneStatus        -- 环节 B OCR 行级扫描（装了就跑）
  , priorReview   : Maybe Verdict     -- 已有 {slug}-review.md 的 status
  , priorIndependentReview : Bool     -- 旧报告已有可复用 reviewer gate 锚点
  , changeClass   : ChangeClass
  }
data LaneName = LaneA | LaneB
data ExternalRunRef = TaskRunRef AgentRef | OcrRunRef Text
data LaneStatus = ReadyToLaunch | Pending ExternalRunRef | Completed | Failed Reason | Skipped | Unavailable Reason
data LaneResult = LaneCompleted Findings | LaneFailed Reason
data ReviewResume = ResumeLane LaneName ExternalRunRef LaneResult | ResumeSelfReviewDowngrade ApprovalRef
data ChangeClass = Initial | ClosureOnly | Material | Unknown
data Verdict = Passed | ChangesRequested | Blocked
data ReviewOutcome
  = ReviewWritten Verdict             -- {slug}-review.md 落盘，reviewer 字段按已完成环节写
  | FocusedClosure Verdict            -- 复用已完成的首次 reviewer，追加可归因 closure evidence
  | Launching LaneName                -- 按 independent-review protocol 启动一次并先持久化 run ref
  | Awaiting ReviewWait               -- 已启动的 reviewer 尚未返回；等待或恢复，不请求 owner 批准
  | HumanCheckpoint CheckpointReason  -- 停下等用户确认，不越过继续
  | NeedsHuman ReviewBlocker          -- 缺输入或来源事实，无法开审
data ReviewWait = LaneStillPending LaneName ExternalRunRef
data CheckpointReason = SelfReviewDowngrade
data ReviewBlocker
  = AttentionMissing
  | SpecNotFinalized      -- 来源 spec 产物缺失 / 未定稿 → 退回来源实现技能
  | DiffNotAttributable   -- 无可归因 diff / 定稿 spec / git range → 退回来源或请补范围
  | InvalidReviewResume   -- lane/ref 不匹配，拒绝从聊天记忆猜测结果归属
restoreReviewState :: RepoFacts -> Either ReviewBlocker ReviewState
restoreReviewState facts
  | invalidPersistedLaneState facts = Left InvalidReviewResume
  | fullRereviewRequired facts = Right (resetLanesForNewRound facts)
  | otherwise = Right (normalizeCurrentRound facts)
applyReviewResume :: Maybe ReviewResume -> ReviewState -> Either ReviewBlocker ReviewState
applyReviewResume Nothing s = Right s
applyReviewResume (Just (ResumeLane lane ref result)) s
  | pendingLaneRef lane s == Just ref = Right (persistLaneResult lane ref result s)
  | otherwise                         = Left InvalidReviewResume
applyReviewResume (Just (ResumeSelfReviewDowngrade ref)) s
  | pendingSelfReviewDowngrade s && approvalArtifactApproved s ref "code-review-local-only" = Right (persistReviewDowngrade ref s)
  | otherwise = Left InvalidReviewResume
csCodeReview req = either NeedsHuman selectReviewOutcome
  (restoreReviewState req.repoFacts >>= applyReviewResume req.resumeInput)
```

`selectReviewOutcome` 从仓库事实选结论（决策细则见「启动检查」「独立 reviewer 编排」「结论」「review-fix 衔接」；此处只固定分支形态）：

```haskell
selectReviewOutcome :: ReviewState -> ReviewOutcome
selectReviewOutcome s
  | attentionMissing s                                 -> NeedsHuman AttentionMissing
  | not s.specFinalized                                -> NeedsHuman SpecNotFinalized
  | not s.diffAttributed                               -> NeedsHuman DiffNotAttributable
  | anyLaneFailed s                                    -> ReviewWritten Blocked
  | Just lane <- firstLaunchableLane s                 -> Launching lane
  | Just wait <- firstPendingLane s                    -> Awaiting wait
  | focusedClosureEligible s && hasBlocking s          -> FocusedClosure ChangesRequested
  | focusedClosureEligible s                           -> FocusedClosure Passed
  | laneAMissing s && not (userAcceptedDowngrade s)    -> HumanCheckpoint SelfReviewDowngrade
  | hasBlocking s                                      -> ReviewWritten ChangesRequested
  | otherwise                                          -> ReviewWritten Passed
focusedClosureEligible :: ReviewState -> Bool
focusedClosureEligible s = s.priorIndependentReview
                        && s.priorReview `elem` [Just Passed, Just ChangesRequested]
                        && s.changeClass == ClosureOnly
laneFailed :: LaneStatus -> Bool
laneFailed (Failed _) = True
laneFailed _          = False
anyLaneFailed :: ReviewState -> Bool
anyLaneFailed s = laneFailed s.laneA || laneFailed s.laneB
```

`anyLaneFailed` 包含环节 A 的 `Blocked` / failed 和已启动环节 B 的 `OcrFailed`；失败优先于等待，
必须先写 `status: blocked`，不能被 `hasBlocking` 或默认 passed 分支吞掉。`Material` / `Unknown`
永远不满足 `focusedClosureEligible`，必须重新走完整独立复审。

`restoreReviewState` 校验报告当前 `round`：旧 `status: blocked` 缺 lane/ref 或非法 enum 直接 `Left InvalidReviewResume`；`ClosureOnly` 保留同 round 的 `Completed`，`Initial` / `Material` / `Unknown` 完整复审必须增加 round，并按当前能力把两 lane 重置为 `ReadyToLaunch` / `Unavailable`，不得复用旧 completed reviewer。`Launching` 成功后先持久化 `Pending ref` 再返回 `Awaiting`。self-review 降级先按 approval conventions 写 pending `code-review-local-only` 命名决策，只消费可机械核验的 `ApprovalRef`。

## 进入来源（横切）

| 来源 | 进入点 | spec 产物 | 通过后去向 |
|---|---|---|---|
| `cs-feat` Standard lane | impl 完成、accept-inline 前 | design + checklist | `cs-feat` acceptance（Inline Verification Matrix） |
| `cs-feat` Goal lane | impl 完成、QA 前 | design + checklist + goal evidence | `cs-feat` QA 阶段 |
| `cs-feat` fastforward mode | ff-note 落盘、commit 前 | ff-note + 用户原始需求 | 收尾提交 |
| `cs-issue` fix 阶段 | fix-note 落盘、commit 前 | report + analysis + fix-note | 收尾提交 |
| `cs-refactor` standard mode | apply-notes 完成、commit 前 | scan + refactor-design + checklist | 收尾提交 |
| `cs-refactor` fastforward mode | 自证通过、commit 前 | 用户确认的重构范围 + 验证命令 | 收尾提交 |
| ad-hoc / pre-merge | 用户要求 | 用户指定范围 / git range | 给结论 |

**不是 `cs-audit`**：audit 主动扫一片代码找潜在问题；code review 只审当前变更范围。

本次调用参数：$ARGUMENTS。非空且不是字面 `$ARGUMENTS` 时，按 ad-hoc 来源处理；`--range <git-range>` 指定提交范围，其余文本作为范围说明或文件 scope。仍需按「启动检查」核对范围内确有可归因改动。

无参数默认行为：参数为空或仍是字面 `$ARGUMENTS` 时，按「进入来源」表从当前流程产物和 git diff 推断来源；没有可归因 diff、定稿 spec 或 git range 时，不做空 review，退回来源实现技能或请用户补范围。

ad-hoc 参数如果含 `--range`，审查范围来自 `git diff {range}`，不要求工作区有未提交 diff。历史裸 git range（如 `main..HEAD`、`origin/main...HEAD` 或一个 commit/ref）可兼容识别；新文档和新调用一律用 `--range`。参数如果是文件路径、自然语言范围或 pre-merge 说明，则先解析为明确文件 / diff 来源；解析不清时先问清楚。

## 输入

进入 review 前必须读取：

- `.codestable/attention.md`
- 来源的 spec 产物（feature 看 `{slug}-design.md` + `{slug}-checklist.yaml`；issue 看 report+analysis+fix-note；refactor 看 scan+refactor-design+checklist；ff / ad-hoc 看用户确认范围）
- 实现完成汇报 / 最近实现记录（如果在对话里，按对话事实引用；如果已落文件，读文件）
- `git status --short`
- `git diff`（有 staged diff 时也读 `git diff --cached`；ad-hoc git range 读 `git diff {range}`）
- diff 涉及的人写代码文件和相邻关键调用点
- spec 指向的 architecture / requirement / roadmap 相关文档（只读，判断改动是否会影响归并；feature 即 design 第 4 节）
- goal / gate 模式下的 evidence pack、gate results、DoD results；缺失时回 implementation gate 补证据，不现场猜测
- 独立 Task agent reviewer 输出（如果本轮已启动）

如果工作区有本轮范围外的既有 dirty 文件，先记录为 baseline/无关变更；审查结论只针对本轮可归因的改动。无法区分归因时写成 `residual-risk`，不要把不确定当通过。

## 启动检查

先按「进入来源」表确认本轮来源，再做对应前置校验：

1. 来源的 spec 产物存在且已定稿——feature 看 `{slug}-design.md`（`doc_type=feature-design`、`status=approved`、`feature` 与目录一致）+ `{slug}-checklist.yaml`（`steps` 全 `done`）；issue 看 report+analysis+fix-note；refactor 看 scan+refactor-design+checklist；ff 看用户确认范围；ad-hoc 看用户指定范围 / git range。缺定稿 spec 时退回对应实现技能，不硬审。
2. goal / gate 模式下，先读取 `{slug}-evidence-pack.md`、`{slug}-gate-results.json` 和 `{slug}-dod-results.json`；缺失或 gate blocking 未解释时退回 implementation.before_review。
3. 流程来源必须在当前 unstaged / staged diff 或本轮提交范围里看到实现改动；ad-hoc git range 必须 `git diff {range}` 非空。ad-hoc range 审查允许工作区干净；非 range 且完全没有可归因改动时退回来源实现技能或请用户补范围。
4. 如果已有 `{slug}-review.md`：
   - `status: passed` 且 diff 未变化：提示按表进入「通过后去向」。
   - `status: changes-requested` / `blocked`：读取旧 findings，确认是否处于 review-fix 后的复审。
   - `status: blocked` 且 lane 字段不完整、pending 缺 ref 或 ref 与恢复输入不匹配：fail-closed 为 `InvalidReviewResume`，不得猜测 reviewer 归属或重复启动。
   - diff 已变化：先分类。仅 `test/docs/type/metadata/nit-only`，且不改变行为、公开契约、安全、数据、并发或架构的可归因修正，走 focused closure；其余属于实质变化并增加完整独立复审轮次。
   - 无法确定变化类别、跨会话无法还原 review 后增量，或 closure diff 混入生产行为修改：fail-closed 做完整独立复审。

## 独立 reviewer 编排

首次审查和实质变化后的完整复审必须按 `references/independent-review/protocol.md` 执行双环节 review：环节 A 是独立 Task agent review，环节 B 是 OCR 行级扫描（装了就跑）。focused closure 不重启双环节，但必须满足启动检查里的窄条件并保留首次 reviewer 锚点。

进入审查流程第 2 步前先读取该 reference；没有读取它就不能启动 reviewer，也不能写 `reviewer` 字段。

## 审查流程

### 1. 上下文与范围

- 用 design 第 1/2/3 节确认目标、明确不做、关键决策、验收场景。
- 用 checklist steps 确认实现声称已经完成的范围。
- 用 `git status` / `git diff` 列出真实改动文件，标出新增、修改、删除、未跟踪、staged。
- 判断 diff 大小和风险：跨模块、跨边界、数据迁移、权限/安全、并发/异步、用户可见 UI、公共 API、测试缺口。

### 2. 独立审查合并

- 按 `references/independent-review/protocol.md` 自检工具并启动环节 A / 环节 B；启动条件、OCR scope 规则、严重度映射和降级处理都以该 protocol 为准。
- 本地可以先做整体审查草稿，但最终 verdict 必须等所有已启动 reviewer 返回、逐条本地事实核验合并后才能定稿。
- 报告里保留来源：标注每条 finding 来自哪个 reviewer（`heterogeneous-agent` / `independent-agent` / `ocr` / `local`）。

### 3. 整体审查

先看整体，再看行级细节：

- design fit：实现是否满足 design，又没有偷偷扩范围。
- 架构 fit：新代码是否放在正确层次，是否绕过既有抽象、引入反向依赖或过度耦合。
- 复杂度：是否为当前问题引入过度泛化、补丁分支、参数膨胀、大函数/大类继续膨胀。
- 测试策略：现有测试和新增测试是否能证明关键场景；测试是否会在代码坏掉时真实失败。
- 风险面：错误处理、数据校验、安全边界、权限、并发、幂等、性能、可观测性、回滚/卸载。
- 对抗式审查：假设 diff 必有一个生产 bug，列出最可能失败的 3-5 条反例；能被事实支撑的进入 findings，不能完全确认的进 residual-risk / QA focus。
- 文档/归并影响：是否出现 acceptance 必须回写的 architecture / requirement / roadmap 变更。

### 4. 行级审查

对人写代码逐文件审查，至少覆盖：

- 逻辑正确性：边界值、空值、异常路径、状态转换、时序问题、off-by-one。
- 错误处理：错误语义是否明确，是否吞错，是否把恢复逻辑和业务逻辑搅在一起。
- 数据与安全：输入验证、注入风险、敏感信息、权限检查、跨租户/跨用户隔离。
- 性能与资源：重复 IO、N+1、无界循环/缓存、内存泄漏、未释放资源。
- 并发/异步：竞态、死锁、取消、重入、重复提交、幂等。
- 可维护性：命名是否沿用 design 术语，是否复用已有 helper，是否新增重复逻辑。
- 清洁度：调试输出、临时 TODO/FIXME、注释掉代码、未使用 import、方案外文件。

生成代码、锁文件、大数据文件可以抽样，但报告里要说明抽样范围。人写业务代码不能跳过不看。

### 5. 结论

把发现按严重度归类，并给出明确 verdict：

- `passed`：没有 blocking；important 已修复、无重要项、或用户明确接受延后。
- `changes-requested`：有 blocking，或 important 多到会影响验收可信度。
- `blocked`：缺少关键输入、diff 归因无法判断、设计/实现状态不满足 review 前置条件，或本轮已启动独立 Task agent reviewer 但结果仍 pending / failed / blocked 且用户尚未确认降级。

**`reviewer` 字段（gate 锚点）**：`{slug}-review.md` 的 frontmatter `reviewer` 决定下游质量 gate 是否放行，按 `references/independent-review/protocol.md` 的实际完成情况写 `subagent+ocr` / `subagent` / `ocr` / `self`。任一已启动环节仍 pending / failed / blocked 时不定稿 `passed`，也不写 `subagent`。

## 严重度

- `blocking`：必须先修。会导致功能不满足 design、数据/安全/权限风险、明显 bug、验收无法可信执行、严重架构倒退、测试完全覆盖不到关键风险。
- `important`：应该修；若用户决定延后，必须在 review 报告和 acceptance residual risk 中明确记录。
- `nit`：小的清晰度或一致性建议，不阻塞。
- `suggestion`：替代实现思路，不要求本次采用。
- `learning`：知识性说明，不要求动作。
- `praise`：记录值得保留的好做法；少量即可。
- `residual-risk`：review 无法完全消除的不确定性，需要 QA / acceptance 重点复核。

不要把个人偏好升级成 blocking。blocking 必须能用仓库事实、design 契约、可靠工程原则或可复现实例支撑。

## 报告模板

报告落在来源流程的 spec 目录，文件名 `{slug}-review.md`；feature 来源即 `.codestable/features/{feature}/{slug}-review.md`，issue/refactor 等放各自流程目录。

完整 frontmatter 与各章节模板见同包 `references/report-template.md`（按已加载 `SKILL.md` 所在目录解析，不要按业务仓库根目录猜路径）。没有某类 finding 时写 `none`，不要删除章节；下一轮复审要能对比。

## review-fix 衔接

下一步去向按「进入来源」表确定（feature 来源即 review-fix→`cs-feat` implementation 阶段、通过→`cs-feat` QA 阶段；issue/refactor/ff 各回对应主入口阶段或提交收尾）。

如果有 `blocking`：

1. 报告 `status: changes-requested`。
2. 告诉用户下一步触发来源实现技能的 review-fix 模式。
3. review-fix 只修 blocking findings；important 是否修由用户或实现者判断，但不能顺手扩大范围。
4. review-fix 完成后必须回到本审查；由本技能判断 focused closure 或完整独立复审，不能直接进入下游。

focused closure 只在首次独立审查已完成、当前主 agent 能精确归因 review 后增量，并且增量仅为 test/docs/type/metadata/nit-only 时成立。主 agent 必须逐条核对原 finding、检查增量 diff、运行目标验证，并在同一报告追加 `Focused Closure`（关闭的 REV、文件/行、命令与结果、为何未改变行为/契约）；保留原 `reviewer` 和 `round`。任一条件不满足或无法确定，就完整独立复审。

如果只有 `important`：

- 默认建议先修；如果用户明确接受延后，报告里把它移入 residual risk，并允许进入通过后去向。

如果没有 blocking，且 important 已处理或被明确接受：

- 报告 `status: passed`。
- 告诉用户下一步是「进入来源」表的通过后去向（Standard feature→accept-inline；Goal feature→QA）。

## Progressive Reference Loading

进入具体环节才加载对应 reference，不在启动时读全部（progressive reference loading）：

- 启动独立 reviewer（进入「审查流程」第 2 步）前 → `references/independent-review/protocol.md`；没读它不能启动 reviewer，也不能写 `reviewer` 字段。
- 落盘报告前 → `references/report-template.md`（按已加载 `SKILL.md` 所在目录解析）取完整 frontmatter 与章节模板。

禁止：启动即读全部 references；跳过 `references/independent-review/protocol.md` 直接写 `reviewer`；任一已启动环节未返回就定稿 `passed`。

## Failure Behavior

`cs-code-review` 的五种运行结果：

- `NeedsHuman`：无法开审。`.codestable/attention.md` 缺失（→ `cs-onboard`）；来源 spec 未定稿或 diff 无法归因时不做空 review，退回来源实现技能或请用户补范围。
- `Launching`：按 protocol 启动指定 lane 一次；拿到 run id 后先写入报告，再进入 `Awaiting`，不得把启动命令当成 pending 状态重复执行。
- `Awaiting`：独立 reviewer 已启动但尚未返回。保留 lane 与 `ExternalRunRef`，只接受匹配的 `ResumeLane`；报告 `status: blocked`，不定稿 `passed`，也不把等待伪装成 owner approval。
- `HumanCheckpoint`：只有缺独立 Task agent 能力、需要 owner 明确接受 self/ocr 降级时返回 `SelfReviewDowngrade`。
- `ReviewWritten Blocked`：任一 reviewer 已失败或明确 blocked。记录失败事实和重试 / 改配置 / 明确降级选项，不写虚假的 completed reviewer。

五种情况都要报告：来源与 `{slug}-review.md` 路径、当前 verdict / status、阻塞或 checkpoint 原因、需要的用户决策或下一步动作（退回哪个来源实现技能 / 补什么范围 / 等哪个 reviewer）、已启动环节的状态，以及是否可安全重跑本审查。不要在环节未返回或有 blocking 时假装通过。

## 退出条件

- [ ] 已读取 attention、定稿的来源 spec、实现证据、git status/diff 和相关代码；未定稿则退回来源技能。
- [ ] 主 agent 已自检 Task agent 能力和 `ocr` CLI，记录可用情况。
- [ ] 首次/完整复审的 A/B 环节均已返回并经本地核验；focused closure 已证明旧 reviewer、增量归因和类别。
- [ ] 已完成整体与逐文件行级审查，并按全部严重度分类。
- [ ] `{slug}-review.md` 已落来源目录；`passed` 的 reviewer 值与实际完成环节一致。
- [ ] blocking 指向 review-fix；通过则明确 lane-aware 下游去向。
