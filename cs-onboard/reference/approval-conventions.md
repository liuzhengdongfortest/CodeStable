# Approval Conventions

This file is copied by `cs-onboard` to
`.codestable/reference/approval-conventions.md`. It owns the global rule for
human approval reports.

## Core Rule

Before asking the owner to choose, approve, authorize, accept risk, sign off,
merge, deploy, override a gate, or answer an interview / grill checkpoint, write
a human-readable approval report in the relevant `.codestable` unit.

Canonical stage reports can satisfy this rule when they already contain the
decision, options, recommendation, tradeoffs, evidence, consequence, and next
action. Examples:

- `cs-feat-design` design review;
- `cs-issue-analyze` fix-option analysis;
- `cs-issue-fix` fix-note / implementation review;
- `cs-feat-accept` acceptance report.

When no such stage report exists, write:

```text
{unit}/approval-report.md
```

Do not ask a bare multi-choice question when the decision needs context.

Use the report language policy from `.codestable/attention.md` for prose. If
attention has no report language policy, use the owner's current conversation
language. Keep the heading names stable so agents can parse the report
reliably.

## Unit Path

Use the closest durable workflow directory:

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

## Triggers

Write `approval-report.md` for:

- interview / grill checkpoints whose answer changes route, scope, or next work;
- route choice between plausible workflows or canonical specs;
- review authorization, implementation subagent authorization, or inline-review fallback;
- worktree override, gate override, destructive action, secrets, external purchase,
  merge, deploy, or risk acceptance;
- blocker / owner-stop decisions;
- choosing what to fix, defer, drop, migrate, or rehabilitate.

## Template

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

Omit `Decision History` for the first approval in a unit. `Options` should be
concrete and mutually exclusive. Mark the recommended option explicitly.
`Non-Automatic Actions` must say what will not happen automatically, such as
commit, merge, deploy, rewrite long-lived specs, or accept risk.

## After Approval

After the owner answers:

1. update `status` to `approved`, `rejected`, or `superseded`;
2. record the selected option and answer date;
3. continue from `After You Answer`;
4. keep the report as history instead of deleting it.

If the same unit later needs another approval, reuse `approval-report.md` as the
single approval surface: add a dated decision-history entry for the old answer,
then replace the pending sections with the new decision. Never silently
overwrite an unresolved pending approval.
