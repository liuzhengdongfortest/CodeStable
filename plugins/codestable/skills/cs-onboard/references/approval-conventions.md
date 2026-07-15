# Approval 约定

本文件会由 `cs-onboard` 复制到 `.codestable/reference/approval-conventions.md`。它负责
human approval report 的全局规则。

## 核心规则

在要求 owner 做选择、批准、授权、接受风险、sign off、merge、deploy、override gate，或回答
interview / grill checkpoint 前，先在相关 `.codestable` unit 写一份人可读的 approval
report。

canonical stage report 如果已经包含 decision、options、recommendation、tradeoffs、
evidence、consequence 和 next action，就可以满足此规则。例如：

- `cs-feat` design review;
- `cs-issue` fix-option analysis;
- `cs-issue` fix-note / implementation review;
- `cs-feat` acceptance report.

如果不存在这样的 stage report，写：

```text
{unit}/approval-report.md
```

需要上下文的决策，不要只问裸多选题。

## Spec

```haskell
data ApprovalTrigger
  = InterviewCheckpoint | RouteChoice | ReviewAuthorization
  | RuntimeOverride | GateOverride | DestructiveAction | SecretUse
  | ExternalPurchase | MergeOrDeploy | RiskAcceptance | BlockerDecision
  | RepairOrDeferDecision
data ApprovalStatus = Pending | Approved | Rejected | Superseded
data ApprovalSurface = CanonicalStageReport Path | ApprovalReport Path | NeedUnitIdentity
data ApprovalRef = ApprovalRef Path DecisionId

selectSurface :: Unit -> Maybe StageReport -> ApprovalSurface
selectSurface unit stageReport
  | coversDecisionContract stageReport = CanonicalStageReport (path stageReport)
  | Just path <- approvalPath unit      = ApprovalReport path
  | otherwise                          = NeedUnitIdentity

recordAnswer :: ApprovalReport -> OwnerAnswer -> Date -> ApprovalReport
recordAnswer report answer date = report
  { status = decisionStatus answer
  , decisionHistory = appendDecision answer date (decisionHistory report)
  , pendingSections = nextDecisionOrEmpty report answer
  }

approvalRefValid :: Unit -> ApprovalReport -> ApprovalRef -> Bool
approvalRefValid unit report (ApprovalRef path decision) =
  path == unit / "approval-report.md" && namedApproval report decision == Approved
```

正文语言遵守 `.codestable/attention.md` 的报告语言策略。若 attention 没有报告语言策略，
使用 owner 当前对话语言。标题名保持稳定，便于 agent 可靠解析。

## Unit 路径

使用最近的持久 workflow 目录：

- goal: `.codestable/goals/YYYY-MM-DD-{slug}/approval-report.md`
- feature: `.codestable/features/YYYY-MM-DD-{slug}/approval-report.md`
- issue: `.codestable/issues/YYYY-MM-DD-{slug}/approval-report.md`
- refactor: `.codestable/refactors/YYYY-MM-DD-{slug}/approval-report.md`
- roadmap: `.codestable/roadmap/{slug}/approval-report.md`
- brainstorm / interview: `.codestable/brainstorms/{slug}/approval-report.md`
- root route choice with no existing unit:
  `.codestable/brainstorms/{slug}/approval-report.md`
- unknown route: create or choose the unit first; if impossible, stop and ask
  only for the missing unit identity.

## 触发条件

命中任一 `ApprovalTrigger` 就调用 `selectSurface`。已有 canonical stage report 只有完整包含
decision、互斥 options、recommendation、tradeoffs、evidence、consequence 和 next action 时才可复用。

## 模板

```markdown
---
doc_type: approval-report
unit: {unit path or slug}
status: pending
reason: {interview | route-choice | review-authorization | risk | merge | blocker | other}
approvals: {} # 可被 runtime 消费的命名决策，例如 goal-acceptance: approved
created_at: YYYY-MM-DD
---

# Approval Report

## Decision History

## Decision Needed

## Why Now

## Context

## Options

## Recommendation

## Risks And Tradeoffs

## Non-Automatic Actions

## After You Answer
```

一个 unit 的第一次 approval 可以省略 `Decision History`。`Options` 要具体且互斥。明确标出
推荐选项。`Non-Automatic Actions` 必须说明哪些动作不会自动发生，例如 commit、merge、
deploy、重写长期 specs 或接受风险。

需要被 runtime 消费的授权使用 `approval-report.md#<decision-id>`；fragment 是 `approvals`
中的 key，不是聊天标签。只有同 unit 的 canonical 文件且对应值为 `approved` 才有效；状态字段
只写 `approved`、ref 非空、路径越界或文件缺失都不能放行。

## Approval 之后

owner 回答后按 `recordAnswer` 更新状态、选择项、日期与历史，再从 `After You Answer` 继续；
报告作为历史保留，不删除。

如果同一个 unit 后续还需要 approval，复用 `approval-report.md` 作为唯一 approval 表面：
先为旧回答添加带日期的 decision-history 记录，再用新决策替换 pending sections。不要静默
覆盖尚未解决的 pending approval。
