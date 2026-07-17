# Feature QA Protocol

本阶段是 review 通过后、acceptance 前的行为 QA gate。它以测试人员视角运行功能、集成、E2E、browser、API、CLI 或 manual 场景，并写 `{slug}-qa.md`。默认不改代码、不改 checklist、不改 design；发现失败后回到 `cs-feat` implementation 阶段的 qa-fix。

本阶段默认只用于 Goal lane，或用户在 Standard lane 明确要求独立 QA 报告的情况。Standard 默认把同等强度验证合并进 accept-inline；Quick 不生成独立 QA 报告。

QA 的目标不是再做一遍 code review，也不是最终归档验收报告。它回答一个问题：候选版本通过用户或调用方入口运行时，design 承诺的行为是否真的成立。执行算法统一见同 skill 的 `references/qa/behavioral-verification.md`；独立 QA 和 Standard accept-inline 必须使用同一契约。

## Spec

```haskell
data FeatureKind = Functional | NonFunctional | Mixed
data QAInput = StartQA | ResumeQARunner OwnerApproval
data QAStatus = QAPassed | QAFailed | QABlocked
data QANext = RouteAcceptance | RouteQAFixThenReview | ResolveEnvironmentOrInputs
data QAPreflight = ContinueQA | ReturnToCodeReview
data WaitReason = QARunner AgentRef
data QARunnerOutcome
  = RunQALocally | LaunchQARunner AgentCapability AgentConfig | MergeRunnerEvidence Findings
  | Awaiting WaitReason | HumanCheckpoint Reason | Blocked Reason

selectQARunner :: QAInput -> QARequest -> AgentEnv -> AgentRun -> QARunnerOutcome
selectQARunner input q env run = qaRunnerGate (highRisk q) (selectTaskAgent QA env) run (case input of ResumeQARunner approval -> Just approval; _ -> Nothing)

qaRunnerGate :: Bool -> AgentSelection -> AgentRun -> Maybe OwnerApproval -> QARunnerOutcome
qaRunnerGate _ _ (Finished findings) _ = MergeRunnerEvidence findings
qaRunnerGate _ _ (Active ref) _ = Awaiting (QARunner ref)
qaRunnerGate _ _ (Failed reason) _ = Blocked reason
qaRunnerGate False _ NotStarted _ = RunQALocally
qaRunnerGate True (SelectionBlocked reason) NotStarted _ = Blocked reason
qaRunnerGate True (SelectionNeedsOwnerApproval _) NotStarted (Just ApproveLocalOnly) = RunQALocally
qaRunnerGate True (SelectionNeedsOwnerApproval reason) NotStarted _ = HumanCheckpoint reason
qaRunnerGate True (Start agent config) NotStarted _ = LaunchQARunner agent config
qaRunnerGate _ _ _ _ = Blocked InvalidQARunnerTransition

qaPreflight :: QAState -> QAPreflight
qaPreflight q
  | reviewRoundAndScopeCurrent q = ContinueQA
  | otherwise                    = ReturnToCodeReview

qaVerdict :: QAState -> QAStatus
qaVerdict q
  | inputsMissing q || candidateAttributionUnknown q              = QABlocked
  | implementationFailure q                                   = QAFailed
  | functionalCoreMissing q && causedByEnvironment q           = QABlocked
  | functionalCoreMissing q                                    = QAFailed
  | kind q == NonFunctional && not (alternativeEvidenceEnough q) = QAFailed
  | blockingItemsPassed q && behavioralEvidencePassed q         = QAPassed
  | otherwise                                                   = QAFailed

nextQA :: QAStatus -> QANext
nextQA QAPassed  = RouteAcceptance
nextQA QAFailed  = RouteQAFixThenReview
nextQA QABlocked = ResolveEnvironmentOrInputs

persistedQAStatus :: QAStatus -> Text
persistedQAStatus QAPassed = "passed"
persistedQAStatus QAFailed = "failed"
persistedQAStatus QABlocked = "blocked"
```

`qaPreflight` 发生在 `qaVerdict` 和任何 terminal QA receipt 之前。无法用现有 review round/scope 契约证明 review 覆盖当前候选时，直接 `ReturnToCodeReview`；不把 freshness 问题写成新的 QA status，也不新增 digest 或 resolver 分支。

> 共享路径与命名约定看 `.codestable/reference/shared-conventions.md` 第 0 节。

## 独立 QA Task agent（可选）

QA 按上述 gate 决定本地执行或独立 runner。`ResumeQARunner` 必须由主入口 typed union 传入；`LaunchQARunner` 先写报告的 `runner_state: awaiting` 与 `runner_id`，`Awaiting (QARunner ref)` 只从该 id 恢复；owner approval、runner failure、hard block 分别持久化为 `needs-owner-approval`、`runner-failed`、`blocked` 并填写 `runner_reason`，不得静默本地降级。runner 按 agent-conventions 的 plan / read-only 等价 mode 一步启动，但它是辅助执行者，不是 QA owner：

- 主 agent 负责建立 Verification Matrix、决定哪些证据阻塞、核验 runner 输出，并写 `{slug}-qa.md` 的最终 verdict。
- runner 默认只按 behavioral verification 输入投影运行候选，不审代码；如需改测试或配置，必须退回 `cs-feat` implementation 阶段 qa-fix。
- runner 输出经主 agent 核验后只把结果摘要与 evidence locator 写入 QA 报告；原始长输出不复制成 unit artifact。未经核验的结论只能作为 `residual-risk` 或待复核项。
- runner 输出被消费并写入 QA 报告后，按 Task agent 生命周期关闭该 runner；容量失败只在失败后清理最老已完成 agent 并重试一次。
- 普通低风险非功能性 feature 不强制独立 runner，避免把 QA 成本固定放大。

## 输入

进入 QA 前按顺序读取：

- `.codestable/attention.md`
- 同 skill 的 `references/qa/behavioral-verification.md`（按已加载 `cs-feat/SKILL.md` 所在目录解析）
- `{slug}-design.md` 第 3 节场景，以及判定场景所需的明确不做/条件性边界
- `{slug}-checklist.yaml` 中的行为 checks 和必跑命令
- `{slug}-review.md` frontmatter 的 status/round/lane 状态、当前 scope locator，以及 review 报告第 5 节 Test And QA Focus 和 review 报告第 6 节 Residual Risk
- goal / gate 模式下 `{slug}-evidence-pack.md` 的状态、核心证据和 residual-risk 投影；只有 failed / warning / mismatch 或投影不足时才下钻 raw gate/DoD 结果
- `git status --short`
- 项目用户入口和测试入口：README、package scripts、Makefile、CI 配置、历史 acceptance / QA 中与本 feature 相关的命令、API、页面或手工路径

`git status --short` 只用于候选范围和 review freshness preflight，不用于推断实现正确性。工作区有 feature 外的 dirty 文件时只记录 scope 风险；无法确认当前 review 覆盖候选，就在 terminal QA receipt 前返回 `cs-code-review`，不靠 QA 自行复判。

完整设计、完整 review narrative 和 raw gate/DoD 证据都属于 drill-down 输入，不是默认 read set。只有行为场景本身无法解释、review 投影指出未决风险，或 failed/blocked 需要定位复现条件时，才读取直接相关的 canonical 段落或原始证据。

feature type、核心行为、替代证据与 residual-risk 的完整判据以 `behavioral-verification.md` 为准。QA receipt 必须记录分类和 core evidence gate；功能/mixed 场景不能只靠 typecheck/lint/build，非功能性场景也必须验证消费者可观察的契约结果。

## 启动检查

1. `{slug}-design.md` 存在且 `status=approved`。
2. `{slug}-checklist.yaml` 存在，`steps` 全 `done`，`checks` 仍未由 acceptance 全部通过。
3. `{slug}-review.md` 存在，frontmatter `doc_type=feature-review`、`status=passed`，无 unresolved `blocking` findings。
4. goal / gate 模式下 evidence pack 必须存在；先读 projection，只有 failed / warning / mismatch、blocking 未解释或证据不足时下钻 gate/DoD 原始结果。
5. 执行 `qaPreflight`：如果现有 review round/scope 无法证明覆盖当前候选，在 terminal QA receipt 前 `ReturnToCodeReview`。qa-fix 或其他候选变化会让旧 review 过期；QA 不读取源码或完整 diff 建第二套 freshness 判断。
6. 如果已有 `{slug}-qa.md`：
   - `status=passed` 且 review scope/round 仍覆盖当前候选：提示可进入 `cs-feat` acceptance 阶段。
   - `status=failed` / `blocked`：读取旧失败项，确认是否处于 qa-fix 后的复测。
   - 候选 scope 已变化：先回 code review；review passed 后重新 QA，并在报告里记录轮次。

## QA 流程

### 1. 建验证矩阵

按 `references/qa/behavioral-verification.md` 从 design 场景、行为 checks、项目运行入口、review QA focus/residual risk 和 evidence projection 建矩阵：

- Feature type：functional / non-functional / mixed。
- 核心性：core-functional / supporting / non-functional。
- 场景：输入 / 触发 → 期望可观察结果。
- 证据类型：function / integration / E2E / browser / API / CLI / manual / contract test；typecheck/build 只作 supporting evidence。
- 命令或动作：具体命令、页面路径、API 请求、手工步骤。
- 失败判据：什么结果算 fail，不写"看起来正常"。
- 归因：本 feature / 既有基线 / 环境不可用 / 无法判断。

优先使用项目已有测试入口和既有工具，不为了 QA 临时引入新测试框架。需要新增测试代码时，QA 不直接写；把它记为 failed item，回 `cs-feat` implementation 阶段 qa-fix。

### 2. 运行验证

先运行最接近用户入口的 core behavior，再运行边界/失败语义、review 风险焦点和 supporting gates。前端用户行为用 browser/E2E/manual，API/后端/CLI 用真实请求、集成测试或可复现命令。每条证据记录 action、expected、result 和 locator；成功日志不整段复制。不可运行时写具体环境、输入或观察判据缺口，不自动通过。

### 3. 诊断下钻

默认不读实现源码、完整 diff、implementation 汇报或完整 review narrative。只在 failed 或 blocked 的诊断分支，按 finding 范围读取直接相关日志、fixture、配置或代码，确定复现条件与归因；不得输出代码风格、TODO/FIXME、unused import、dead code、架构或可维护性 finding。这些职责仍由 code review、DoD cleanliness 和 acceptance final audit 承担。

### 4. 判定

按 `qaVerdict` 判定。关键场景/必跑命令失败、review 重点未覆盖、功能性 UI/API/运行时缺实际证据都属于
`implementationFailure` 或 `functionalCoreMissing`；只有输入、环境或候选归因无法判断时才是 `QABlocked`（报告写 `status: blocked`）。review freshness 不明已由 preflight 返回 code review，不写 terminal QA verdict。

QA failed 时不要直接修代码。输出报告后进入 `cs-feat` implementation 阶段 qa-fix；qa-fix 修完必须先重跑 `cs-code-review`，再重跑 `cs-feat` QA 阶段。

`residual-risk` 只能承载非核心风险、明确延期项或非功能性无法完全复核的边界。它不能承载“核心功能路径没跑过”“真实用户路径没验证”“必跑命令没执行”这类验收缺口。

## 报告模板

报告路径：`.codestable/features/{feature}/{slug}-qa.md`。

两种正文共用完整 frontmatter；compact 不能删除 runner 恢复字段：

```markdown
---
doc_type: feature-qa
feature: YYYY-MM-DD-slug
status: pending|passed|failed|blocked
runner_state: not-started|awaiting|needs-owner-approval|runner-failed|completed|blocked
runner_reason: ""       # needs-owner-approval|runner-failed|blocked 时必填
runner_id: ""           # awaiting 时必填
tested: YYYY-MM-DD
round: 1
---
```

## compact-passed variant

只用于 `status: passed`。保留原节号 1/2/5/7，供 acceptance 直接读取投影；不复制完整成功日志：

```markdown
# {slug} QA 报告

## 1. Scope And Inputs

- Feature type: functional|non-functional|mixed
- Review scope/round: {scope locator / round}
- Core evidence gate: {核心行为；非功能性写替代行为契约}

## 2. Verification Matrix

| ID | Action | Expected | Result | Evidence |
|---|---|---|---|---|
| QA-001 | `{用户/API/CLI/browser/E2E 动作}` | {可观察结果} | pass | {command+exit / test / response / screenshot locator} |

## 5. Findings

- Open findings: none
- Residual risk: {none / 非核心风险及 acceptance 处理方式}

## 7. Verdict

- Status: passed
- Next: `cs-feat` acceptance 阶段
```

## detailed variant

`failed / blocked / pending`、runner 未完成或存在可复测 finding 时使用完整 detailed variant：

```markdown
# {slug} QA 报告

## 1. Scope And Inputs

- Contracts: {design path / checklist path / review path}
- Evidence: {evidence-pack projection / raw gate-DoD-log locator / none}
- Review scope/round: {scope locator / round}
- Candidate scope: {git status --short 摘要；不作代码审查}
- Feature type: functional|non-functional|mixed
- Core evidence gate: {功能性核心路径列表；非功能性写不需要端到端运行的理由}

## 2. Verification Matrix

| ID | 来源 | 核心性 | 场景 / 风险 | 证据类型 | 命令或动作 | 期望 | 结果 |
|---|---|---|---|---|---|---|---|
| QA-001 | design S1 | core-functional/supporting/non-functional | {描述} | function/integration/E2E/browser/API/CLI/manual/contract | `{动作}` | {期望} | pass/fail/blocked |

## 3. Command Results

- `{命令}` → exit {code}：{摘要}
- 未运行：{命令} → {具体原因 + 是否阻塞}

## 4. Scenario Results

- [ ] QA-001 {场景}：pass/fail/blocked
  - Evidence: {输出 / 截图 / 请求响应 / 手工路径}
  - Notes: {归因 / 风险}

## 5. Findings

### failed

- [ ] QA-001 {失败项}
  - Evidence: {证据}
  - Impact: {为什么影响验收}
  - Expected fix scope: {只描述失败边界，不替实现写方案}

### blocked

- [ ] QA-00N {阻塞项}

### residual-risk

- {无法完全验证但不阻塞的风险；没有写 none}
- 不允许出现：功能性核心路径未运行、真实用户/API/运行时路径未验证、必跑命令未执行。

## 6. Diagnostic Context

- Trigger: {failed / blocked matrix item}
- Reproduction: {最小动作、输入、环境}
- Observed: {实际可观察结果}
- Diagnostic drill-down: {相关 log / fixture / config / code locator / none}
- Attribution: {feature behavior / environment / input / unknown}

## 7. Verdict

- Status: passed|failed|blocked
- Next: `cs-feat` acceptance 阶段 | `cs-feat` implementation 阶段 qa-fix -> `cs-code-review` -> `cs-feat` QA 阶段 | 补齐环境后重跑 `cs-feat` QA 阶段
```

detailed variant 没有某类 finding 时写 `none`，不要删除章节；复测要能对比。旧 full QA 报告继续可读；acceptance 对 `Command Results / Scenario Results / Diagnostic Context（如有）` 按需下钻。

## qa-fix 衔接

如果 QA `failed`：

1. 报告 `status: failed`。
2. 告诉用户下一步进入 `cs-feat` implementation 阶段的 qa-fix 模式。
3. qa-fix 只修 QA failed / blocked items，不处理顺手发现，不扩大 feature 范围。
4. qa-fix 修完会改变 diff，必须重跑 `cs-code-review`；review passed 后再重跑 `cs-feat` QA 阶段。
5. QA passed 后才能进入 `cs-feat` acceptance 阶段。

如果 QA `blocked`：

- 先补环境 / 输入 / review 状态；不把 blocked 写成通过。

如果 QA `passed`：

- 告诉用户下一步是 `cs-feat` acceptance 阶段。

## 退出条件

- [ ] 已读取 attention、behavioral verification contract、design 场景、行为 checks、review 第 5/6 节投影、项目运行入口和 git status scope。
- [ ] 已确认 review passed 且 round/scope 覆盖当前候选；无法确认时已在 terminal receipt 前返回 code review。
- [ ] 已判定 feature type，并写明功能性核心路径或非功能性替代证据理由。
- [ ] 已建立 verification matrix，覆盖 design 关键场景、必跑命令、review Test And QA Focus、review residual risk、evidence pack projection，并标出每项核心性。
- [ ] 已运行可运行的验证命令 / 浏览器 / API / 手工检查，并记录结果。
- [ ] 功能性核心路径都有实际运行证据；缺失则 QA 为 failed / blocked，不能写 passed。
- [ ] 非功能性 feature 如未做 E2E / browser / API，已写明为什么不需要，以及采用了哪些可观察契约证据。
- [ ] 未运行项都有具体原因和阻塞判断。
- [ ] 已写 `.codestable/features/{feature}/{slug}-qa.md`。
- [ ] failed / blocked 时没有进入 acceptance，而是指向 qa-fix 或补环境。
- [ ] passed 时明确告诉用户下一步 `cs-feat` acceptance 阶段。

---

## 容易踩的坑

- 把 QA 写成第二次 code review，不运行任何证据。
- 只跑 typecheck 就宣称前端用户路径通过。
- 把功能性核心路径没跑过写成 residual-risk，然后仍然 passed。
- 对非功能性 feature 机械要求外部 E2E，或反过来只读 diff 而不验证 package、schema、CLI、runtime sync 等消费者契约。
- 在 QA 中检查风格、TODO、unused import 或逐文件实现质量，重复 code review / cleanliness 职责。
- 命令失败但归因不清就写 passed。
- QA 阶段直接修代码，绕过 qa-fix / review 复审。
- qa-fix 后跳过 review，直接重跑 QA 或进入 acceptance。
- 不记录未运行原因，导致 acceptance 无法判断剩余风险。
