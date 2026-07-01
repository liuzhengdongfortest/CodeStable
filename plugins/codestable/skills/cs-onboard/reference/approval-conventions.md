# Approval 约定

本文件会由 `cs-onboard` 复制到 `.codestable/reference/approval-conventions.md`。它负责
human approval report 的全局规则。

## 核心规则

在要求 owner 做选择、批准、授权、接受风险、sign off、merge、deploy、override gate，或回答
interview / grill checkpoint 前，先在相关 `.codestable` unit 写一份人可读的 approval
report。

canonical stage report 如果已经包含 decision、options、recommendation、tradeoffs、
evidence、consequence 和 next action，就可以满足此规则。例如：

- `cs-feat-design` design review;
- `cs-issue-analyze` fix-option analysis;
- `cs-issue-fix` fix-note / implementation review;
- `cs-feat-accept` acceptance report.

如果不存在这样的 stage report，写：

```text
{unit}/approval-report.md
```

需要上下文的决策，不要只问裸多选题。

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

以下情况写 `approval-report.md`：

- 答案会改变 route、scope 或 next work 的 interview / grill checkpoint。
- 在多个可行 workflow 或 canonical spec 之间做 route choice。
- review authorization、implementation Task agent authorization 或 inline-review fallback。
- worktree override、gate override、破坏性操作、secrets、外部购买、merge、deploy 或风险接受。
- blocker / owner-stop 决策。
- 选择要修复、延期、丢弃、迁移或修复历史文档的内容。

## 模板

```markdown
---
doc_type: approval-report
unit: {unit path or slug}
status: pending
reason: {interview | route-choice | review-authorization | risk | merge | blocker | other}
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

## Approval 之后

owner 回答后：

1. 把 `status` 更新为 `approved`、`rejected` 或 `superseded`。
2. 记录选中的 option 和 answer date。
3. 从 `After You Answer` 继续。
4. 保留报告作为历史，不要删除。

如果同一个 unit 后续还需要 approval，复用 `approval-report.md` 作为唯一 approval 表面：
先为旧回答添加带日期的 decision-history 记录，再用新决策替换 pending sections。不要静默
覆盖尚未解决的 pending approval。
