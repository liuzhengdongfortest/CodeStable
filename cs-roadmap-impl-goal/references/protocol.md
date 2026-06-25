# CodeStable Roadmap Goal 执行协议

本文件复制到 `{roadmap-path}/goal-protocol.md` 后，由 `/goal` 会话读取。它描述如何按一个已确认的 roadmap 执行包，逐个完成 feature 的实现、代码审查、QA 验证与验收。

## 先读文件

进入 goal 会话后先读取：

- `{roadmap-path}/goal-state.yaml`
- `{roadmap-path}/goal-plan.md`
- `{roadmap-file}`
- `{items-file}`
- `{roadmap-path}/goal-features/*.md`

`goal-state.yaml` 是断点恢复唯一依据。每个 feature 边界都要更新它。

开始执行前确认：

- 所有 feature design 的 frontmatter 都是 `status: approved`。发现 draft design 时停止，要求回到 design review 确认阶段；不要把未批准设计推进到实现。
- `goal-state.yaml` 使用本协议字段：`status`、`baseline_ref`、`current_feature_index`、`features[].status`。发现旧字段如 `current_feature` 或所有 feature accepted 但 `status` 仍是 `ready-to-dispatch` 时，先修正并记录原因；无法确认索引语义时 handoff。
- `goal-plan.md` 写明 roadmap 级核心验收路径、最终聚合测试命令、非功能性替代证据策略。缺失时先补齐计划，不要进入实现循环。

## Goal 模式 gate 接管

本协议只在用户已经确认 roadmap 和全部 feature design 后运行。用户粘贴 `/goal` 代表授权 goal 会话按本协议连续执行后续 impl / review / QA / accept。

普通 `cs-feat-impl` / `cs-code-review` / `cs-feat-qa` / `cs-feat-accept` 中的"汇报后停等用户 review"、"用户终审确认"等阶段 checkpoint，在 goal 模式下改为写入报告和审计记录，不逐 feature 停下等用户。以下情况仍必须停止并打印 `CS_ROADMAP_GOAL_HANDOFF`：

- 需要改变已批准 design、roadmap item、接口契约或 feature 范围
- 独立 reviewer 已启动但 pending / failed / blocked，且没有用户明确降级
- 同一失败项按本文失败恢复三轮仍不通过
- 工作区归因不清、外部凭证 / 环境缺失导致核心行为无法判断
- 功能性核心路径或 roadmap 级核心验收路径无法验证，且 design / goal-plan 未预先把它定义为条件性非阻塞
- 用户主动要求暂停、改方向或终止

---

## 启动标记

打印：

```text
CS_ROADMAP_GOAL_START
Roadmap: <roadmap-slug>
Features: <数量>
Baseline ref: <sha|no-git>
Plan: {roadmap-path}/goal-plan.md
Protocol: {roadmap-path}/goal-protocol.md
```

然后做预检：

1. 校验 git 基线：如果当前在 git 仓库内，`baseline_ref` 必须是 `git rev-parse HEAD` 可解析的 SHA；如果 `baseline_ref: no-git` 但当前是 git 仓库，先把 state 修正为当前 HEAD 并记录原因。当前不是 git 仓库时才允许 `no-git`。
2. 汇总所有 goal-features 中的必跑命令。
3. 成本可接受时先跑一遍。
4. 记录每条命令 green / red。
5. red 时判断：既有问题 / 阻塞问题 / 无法归因。
6. 如果 red 的原因是测试工具 / runner 缺失，优先把工具声明为项目测试依赖或使用项目已有 runner，再重跑原命令；不能创建同名本地 shim、假命令或伪测试结果来让命令变绿。
7. 阻塞或无法归因时不要盲目继续；如果 roadmap 明确有 safety net feature，则先执行对应 feature，否则交还用户。

---

## Feature 循环

按 `goal-state.yaml` 的 `current_feature_index` 和 features 顺序循环。`current_feature_index` 是 0-based；展示给用户的 `Feature: N/总数` 使用 1-based。

### 1. 进入 feature

读取：

- goal-features/{feature-slug}.md
- feature design
- feature checklist
- roadmap item
- 当前代码上下文

进入实现前核验：

- feature design `status: approved`
- checklist `steps` 非空且未完成项只使用 `pending`
- checklist `checks` 非空且验收前只使用 `pending`
- roadmap item 与 goal-state 中的 `roadmap_item` / `feature_dir` 一致

把当前 feature 状态改为 `implementing`，然后打印：

```text
CS_ROADMAP_GOAL_FEATURE_START
Feature: <N>/<总数> <feature-slug>
Design: <路径>
Checklist: <路径>
Depends on: <依赖|none>
Mandatory commands: <命令列表>
Evidence required: <证据列表>
```

### 2. 执行 cs-feat-impl

按 `cs-feat-impl` 规则执行：

- 做基线预检。
- 按 checklist steps 顺序执行。
- 每步完成立刻把对应 step 的状态从 `pending` 改为 `done`。
- 实现阶段不要修改 `checks`；checks 只由 acceptance 阶段从 `pending` 改为 `passed` 或 `failed`。
- 每步留下证据：命令 / 手工 / 浏览器 / API / diff。
- 每步做清洁度检查。
- 普通实现完成汇报写入本 feature 证据记录；goal 模式不在这里停等用户 review。
- 失败时走本文“失败恢复”。

### 3. 执行 cs-code-review

按 `cs-code-review` 规则执行：

- 读取 design、checklist、实现证据、`git status --short`、`git diff` 和相关代码。
- 只读审查；不要在 review 阶段直接修代码。
- 写 `{feature-slug}-review.md`。
- 输出 blocking / important / nit / suggestion / learning / praise / residual-risk 分级。
- 把 review 的 Test And QA Focus 交给 QA 覆盖，acceptance 复核 QA evidence。

如果有 blocking findings，打印：

```text
CS_ROADMAP_GOAL_REVIEW_FIX
Feature: <feature-slug>
Findings: <REV 编号列表>
Next: cs-feat-impl review-fix then rerun cs-code-review
```

然后按 `cs-feat-impl` 的 review-fix 模式只修 blocking findings，修完回到本节重跑 `cs-code-review`。review 未 passed 时不能进入 QA / acceptance。

### 4. 执行 cs-feat-qa

按 `cs-feat-qa` 规则执行：

- 读取 design、checklist、review、实现证据、`git status --short`、`git diff` 和项目测试入口。
- 只读运行验证；不要在 QA 阶段直接修代码。
- 写 `{feature-slug}-qa.md`。
- 覆盖 design 关键场景、必跑命令、review Test And QA Focus、review residual risk。
- 记录命令退出码、浏览器 / API / 手工证据、未运行原因和清洁度结论。
- 功能性或 mixed feature 的核心运行路径必须有实际运行证据；环境不可用导致核心路径无法判断时，QA 必须 `blocked`，不能写 residual-risk 后继续。
- 非功能性 feature 可以用静态检查、diff 复核、文档一致性、schema/快照/类型/构建/目标测试作为替代证据；QA 报告必须写明为什么不需要端到端运行。

如果 QA failed / blocked，打印：

```text
CS_ROADMAP_GOAL_QA_FIX
Feature: <feature-slug>
Findings: <QA 编号列表>
Next: cs-feat-impl qa-fix then rerun cs-code-review and cs-feat-qa
```

然后按 `cs-feat-impl` 的 qa-fix 模式只修 QA failed / blocked items。qa-fix 改变 diff，修完必须回到 `cs-code-review`，review passed 后再重跑 `cs-feat-qa`。QA 未 passed 时不能进入 acceptance。

### 5. 执行 cs-feat-accept

按 `cs-feat-accept` 规则执行：

- 先确认 `{feature-slug}-review.md` 存在、`status=passed`，且没有 unresolved blocking findings。
- 再确认 `{feature-slug}-qa.md` 存在、`status=passed`，且没有 unresolved failed / blocked items。
- 填 acceptance 报告。
- acceptance frontmatter 必须是 `doc_type=feature-acceptance`、`status=passed`；无法通过时写 `status=blocked` 并 handoff。
- 把 checklist checks 从 `pending` 更新为 `passed`；失败项先标 `failed`，修复并重验后再改 `passed`。
- 更新 checklist 时只改目标 `steps` 或 `checks` 块，避免用全文件批量替换把 `steps.status` 和 `checks.status` 混在一起。
- 按 design 第 4 节更新 architecture。
- 按 requirement 字段回写 requirement。
- 按 roadmap / roadmap_item 回写 items.yaml 和 roadmap 主文档。
- 做 feature 级最终审计。
- 普通 acceptance 的用户终审确认在 goal 模式下由 feature 验证标记和最终 roadmap 审计承接；不要逐 feature 停等终审。

### 6. Feature 验证标记

打印：

```text
CS_ROADMAP_GOAL_FEATURE_VERIFY
Feature: <feature-slug>
Implementation: pass|fail
Review: pass|fail
QA: pass|fail
Acceptance: pass|fail
Commands: <命令退出码摘要>
Deliverables: <present|missing 摘要>
Cleanliness: pass|fail
Roadmap item: done|not-done
Knowledge candidates: <候选|none>
```

全部通过后：

1. 把 goal-state 当前 feature 状态改为 `accepted`。
2. 把 `current_feature_index` 指向下一条。
3. 确认 feature review 报告存在且 `status=passed`，没有 unresolved blocking findings。
4. 确认 feature QA 报告存在且 `status=passed`，没有 unresolved failed / blocked items；且没有把功能性核心路径未运行、真实用户/API/运行时路径未验证、必跑命令未执行写成 residual-risk 后放行。非功能性 feature 必须有替代证据理由。
5. 确认 feature checklist 中所有 steps 都是 `done`、所有 checks 都是 `passed`。
6. 打印：

```text
CS_ROADMAP_GOAL_FEATURE_DONE
Feature <feature-slug> accepted. State updated.
```

如果用户中途发新消息，先推进到最近的安全边界：实现中停在当前 step 验证并落状态后；review / QA / accept 中停在当前阶段报告落盘后。然后询问是继续、修改后续 feature specs，还是停止。不要在半写入状态直接切任务。

---

## 失败恢复

适用于实现标准、review blocking 修复、QA failed 修复、验收 checks、必跑命令、交付物、清洁度。

### 第一次失败：诊断并重试

打印：

```text
CS_ROADMAP_GOAL_FAILURE_DIAGNOSE
Feature: <feature-slug>
Failed item: <失败项>
Tried: <已尝试>
Hypothesis: <根因假设>
Next: retry same item once
```

只重试失败项，不推进下一步。

### 第二次失败：窄范围修复说明

写：

```text
{roadmap-path}/goal-features/<feature-slug>-repair.md
```

内容包含：

- 失败项
- 根因
- 允许修改的文件 / 文档
- 必跑验证
- 禁止扩大范围
- 如果失败源于测试工具缺失，只允许补项目依赖、锁文件或既有 runner 配置；禁止新增 `pytest.py`、`jest`、`go` 等同名 shim 或伪造外部工具。

执行这份修复说明，然后回到原检查项重验。

### 第三次失败：交还用户

打印：

```text
CS_ROADMAP_GOAL_HANDOFF
Feature: <feature-slug>
Failed item: <失败项>
Attempts: <三次尝试摘要>
Suggested next move: <建议>
State: blocked
```

把 goal-state 改为 `blocked`，停止。不要打印完成。

---

## 清洁度检查

每个 feature 都检查完整工作区（有 baseline_ref 就看相对 baseline 的变化，否则看当前 diff）：

- 新增调试输出：`console.log` / `print` / `fmt.Println` / 临时 logger
- 新增临时 `TODO` / `FIXME` / `XXX`
- 注释掉的代码
- 未使用 import
- 超出本 feature 范围的文件改动
- 为绕过验证而新增的同名工具 shim，例如 `pytest.py`、`jest`、`go`、`node`

未解释命中 = 验证失败。确实是功能本身需要的日志 / debug 能力，必须在 design 或 goal-feature spec 中写明例外范围。

---

## 知识回写候选

每个 feature accept 后，列出但不要擅自写入：

- 环境 / 命令 / 工作流事实 → `cs-note`
- 可复用坑点 / 调试经验 → `cs-learn`
- 稳定 convention / 架构决定 → `cs-decide`
- 用户或开发指南变化 → `cs-guide`
- 公开 API / 组件 / 命令参考变化 → `cs-libdoc`

architecture / requirement / roadmap 回写是 acceptance 必做动作，不需要额外征求；其他知识沉淀按用户确认执行。

---

## 最终 Roadmap 审计

最后一个 feature accepted 后，不能直接完成。必须生成 `{roadmap-path}/goal-audit.md`，并在 transcript 中打印审计摘要。最终审计是 roadmap 级 gate，不是把每个 feature 的 QA/acceptance 摘要拼起来。

先打印：

```text
CS_ROADMAP_GOAL_AUDIT_START
Roadmap: <roadmap-slug>
Features to verify: <数量>
Commands to re-run: <去重命令列表>
```

审计步骤：

1. 重读 roadmap 主文档、items.yaml、goal-plan.md 和所有 goal-features。
2. 确认每个 item 都是 `done`，或有理由 `dropped`。
3. 重读每个 feature 的 design / checklist / review / QA / acceptance，确认 acceptance `doc_type=feature-acceptance` 且 `status=passed`。
4. 按 goal-plan 汇总最终聚合测试命令：build / typecheck / lint / unit / integration / e2e / smoke / docs/schema 校验。功能性 roadmap 至少应包含能覆盖最终用户/API/CLI/运行时闭环的命令或手工/API/browser smoke；非功能性 roadmap 可用静态 / 一致性 / schema / 文档校验替代，但必须写明理由。
5. 去重重跑最终聚合测试命令。不能因为耗时跳过功能性核心命令；命令因外部网络、凭证、服务、设备不可用或成本过高而无法运行时，判断它是否是核心验收路径：核心路径无法验证则 `blocked`，非核心项才可记 residual-risk / trust-prior。
6. 逐条核验 roadmap 级核心验收路径：
   - 功能性核心路径必须有实际运行证据：e2e / browser / API / CLI / manual smoke / integration test 任一合理组合。
   - 真实用户路径、真实 API、真实 runtime turn、权限/取消/持久化等被 roadmap 标为成功标准的项，不能只用 typecheck / lint / diff review 代替。
   - 如果 design / goal-plan 预先定义“无 auth / 无设备 / CI 环境下只验证 unavailable path”，必须同时验证替代路径和 skip reason；否则不能通过。
   - 非功能性路径写明替代证据：静态检查、diff 复核、文档一致性、schema/快照/类型/构建/目标测试。
7. 从仓库事实核验交付物：文件、配置 key、schema、路由、文档、roadmap 状态。
8. 检查完整工作区：tracked / staged / unstaged / untracked。
9. 检查全 run 清洁度，尤其确认没有为绕过验证留下同名工具 shim、`__pycache__`、临时 runner、临时下载包。
10. 统计 `re-verified` 和 `trust-prior-verify`；截图 / 手工项不能重跑时记为 trust-prior。功能性核心路径不能只靠 trust-prior 通过，除非有明确前置证据路径和当前复核理由。
11. 确认每个 review 报告都 passed，且没有 unresolved blocking findings。
12. 确认每个 QA 报告都 passed，且没有 unresolved failed / blocked items；扫描 residual-risk，确认没有功能性核心未验证项。
13. 确认 architecture / requirement / roadmap 回写存在。
14. 确认知识候选已处理、明确延后或列给用户。
15. 做 learning reflection：从整个 goal 的失败恢复、最终审计补强、设计/实现/review/QA 反复、跨 feature 约束中筛选可复用经验。

把审计结果写入 `{roadmap-path}/goal-audit.md`：

```markdown
---
doc_type: roadmap-goal-audit
roadmap: {roadmap-slug}
status: passed|blocked
audited: YYYY-MM-DD
round: 1
---

# {roadmap-slug} Goal 最终审计

## 1. Scope

- Roadmap: {path}
- Items: {path}
- Goal plan: {path}
- Features: {数量}
- Feature type summary: functional {N} / non-functional {N} / mixed {N}

## 2. Roadmap State

- Items done/dropped/pending: {统计}
- Goal-state current_feature_index: {值}
- Goal-state status: {值}

## 3. Final Aggregate Commands

| 命令 | 类型 | 核心性 | 退出码 | 结果 | 说明 |
|---|---|---|---|---|---|
| `{cmd}` | build/unit/e2e/smoke/docs | core/supporting/non-functional | 0 | pass | {摘要} |

## 4. Core Acceptance Paths

| ID | 路径 | Feature / Roadmap 来源 | 证据 | 结果 |
|---|---|---|---|---|
| CORE-001 | {用户/API/CLI/运行时路径} | {来源} | {命令/手工/API/browser 证据} | pass/fail/blocked |

## 5. Deliverables And Writebacks

- Deliverables: present/missing 摘要
- Architecture / requirement / roadmap writebacks: pass/fail

## 6. QA Residual Risk Review

| Feature | Residual risks | Core gap hidden? | Trust-prior items | Action |
|---|---|---|---|---|
| {feature-slug} | none / list | no / yes | none / list + evidence source | pass / blocked |

- Core gaps hidden in residual-risk: none / list
- Non-core residual risks: list / none
- Trust-prior items: list + evidence source

## 7. Workspace And Cleanliness

- git status summary
- untracked/staged/unstaged review
- debug/TODO/shim/temp files: pass/fail

## 8. Verdict

- Status: passed|blocked
- Coverage: {re-verified} re-verified / {trust-prior} trust-prior
- Blocking gaps: none / list
```

打印：

```text
CS_ROADMAP_GOAL_AUDIT_VERIFY
Roadmap items: <done>/<total>
Commands: <摘要>
Core paths: <pass|fail|blocked>
Deliverables: <present>/<total> present
Cleanliness: pass|fail
Writebacks: pass|fail
Knowledge exits: handled|deferred|none
Coverage: <re-verified> re-verified / <trust-prior> trust-prior
Audit report: {roadmap-path}/goal-audit.md
```

如果有缺口：

1. 写 `{roadmap-path}/audit-repair-<round>.md`。
2. 只修审计失败项，不扩大范围。
3. 重跑审计。
4. 三轮仍失败则打印 `CS_ROADMAP_GOAL_HANDOFF`，把 state 改为 `blocked`，停止。

如果无缺口：

先打印 learning reflection，不直接写知识库：

```text
CS_ROADMAP_GOAL_LEARNING_REVIEW
Pitfall candidates:
- <候选|none>
Knowledge candidates:
- <候选|none>
Not worth archiving:
- <一次性上下文|none>
Recommended next step: <run cs-learn after user confirmation|none>
```

筛选规则：

- pitfall：失败恢复、误判、测试假设、环境/工具坑，后续任务可能重复踩。
- knowledge：更好的默认做法、工作流改进、可复用设计/验证模式。
- not worth archiving：只属于本次业务、不会复用、已被 architecture / requirement / roadmap 回写覆盖的事实。
- 有候选时只建议用户确认后运行 `cs-learn`；不要自动创建或修改 `.codestable/compound/`。

```text
CS_ROADMAP_GOAL_AUDIT_COMPLETE
Roadmap: <roadmap-slug>
Audit rounds: <轮数>
Coverage: <re-verified> re-verified / <trust-prior> trust-prior
Audit report: {roadmap-path}/goal-audit.md
```

然后打印：

```text
CS_ROADMAP_GOAL_COMPLETE
Roadmap <roadmap-slug> complete.
Features accepted: <数量>
Final audit passed.
Manual follow-up: <run cs-docs-neat to reconcile docs/memory|none>
```

只有 `CS_ROADMAP_GOAL_COMPLETE` 出现，`/goal` 才算满足。
