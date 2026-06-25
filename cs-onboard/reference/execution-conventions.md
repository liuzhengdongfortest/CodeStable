# Execution Conventions

This file is copied by `cs-onboard` to
`.codestable/reference/execution-conventions.md`. It owns shared execution,
worktree, review, finish, and handoff rules.

## Main Coordination And Worktree Execution

CodeStable separates discussion / planning from code edits:

- **Main coordination checkout**: where the owner discusses requirements and
  writes design / analysis / roadmap / checklist, usually the `main` checkout.
- **Execution worktree**: where code changes happen. Each feature / issue /
  refactor uses its own git worktree and a typed branch (`feat/{slug}` / `fix/{slug}` / `refactor/{slug}`) unless the owner
  explicitly approves direct edits in the current checkout.

Goal work may use `.codestable/goals/YYYY-MM-DD-{slug}` as the wrapper unit, but
code edits still obey the feature / issue / refactor worktree rules when those
flows apply.

## Short Correct Usage

1. Start: `cs {goal}`. The agent routes to feature / issue / refactor / explore
   / goal.
2. Implement: `开 worktree 实现`. The agent starts in an execution worktree and
   runs the start gate.
3. Review: `允许 subagent`. Completed code batches require independent review.
4. Commit: `提交这批实现`. Run validation, commit planner, and commit gate.
5. Finish: `finish worktree`. Run finish gate and record merge readiness.
6. Solidify finish artifacts: commit the generated finish report files.
7. Merge: only after explicit owner approval.

## Shared Planning Surface

Worktrees must not read sibling unmerged code diffs. Shared intent travels
through:

- `.codestable/goals/**`
- `.codestable/features/**`, `.codestable/issues/**`, `.codestable/refactors/**`
- `.codestable/roadmap/**`
- `.codestable/compound/**`
- owner-designated temporary coordination docs

If an execution worktree discovers the plan must change, sync the plan change
back through the shared planning surface or stop for owner judgment.

## Before Creating An Execution Worktree

Confirm:

1. whether the current checkout is coordination or execution;
2. the spec / checklist / analysis / goal state is readable;
3. worktree path, branch, scope, and sibling-worktree boundaries are clear;
4. the worktree starts from the target baseline, not from another feature
   worktree unless stacked development is explicit.

Run start gate before implementation:

```bash
python3 .codestable/tools/codestable-worktree-gate.py --root . --json start --unit .codestable/features/YYYY-MM-DD-{slug}
```

For goal-wrapped work, the gate unit should be the child feature / issue /
refactor unit when one exists. If the goal has no child unit yet, record the
reason in the goal iteration and follow the lightest applicable execution path.

## Worktree Rules

- Read only the shared planning surface and this worktree's code.
- Read sibling intent only after it is synchronized into shared docs.
- Stop for owner judgment when plan conflicts appear.
- Treat missing env / secrets as environment blockers, not code failures.

## Independent Code Review

Every execution worktree must trigger independent review before reporting a
completed implementation batch. Review is a completion gate, not a commit-time
afterthought.

If the current conversation has no subagent / delegation authorization, write
`approval-report.md` in the relevant unit before implementation review. The
report must include these approval context fields:

```markdown
Context: CodeStable requires independent implementation review before completion.
Term: Subagent Review = a separate reviewer agent performs read-only review.
Why it matters: P0/P1 issues may otherwise surface after completion.
Options:
1. Subagent Review (recommended) - dispatch a reviewer before completion.
2. Inline Review - valid only if this platform has no subagent support.
Default: Subagent Review.
Non-automatic: This does not commit, merge, push, or accept findings.
Question: Which review authorization should CodeStable use?
```

Generate the smallest useful review packet:

```bash
python3 .codestable/tools/build-review-packet.py --root . --unit .codestable/features/YYYY-MM-DD-{slug} --stage quality --output /tmp/codestable-review.md --validation "{验证命令} -> {结果}"
```

Do not include `.env`, tokens, secrets, or local credentials.

Risk defaults:

- tiny doc / typo: owner self-check is enough;
- small local code: one quality review;
- normal feature / fix: quality review plus owner evidence; add spec review when
  scope may drift;
- schema / security / core runtime: spec, quality, and verification reviews;
- large multi-module work: staged execution with handoff context.

Review results land in `{slug}-review.md` with
`reviewer: subagent`. Use `reviewer: self` only when the platform truly lacks
subagents and `CODESTABLE_ALLOW_SELF_REVIEW_FALLBACK=1` is set.

## Context Packets

For multi-stage handoff:

```bash
python3 .codestable/tools/build-context-packet.py --root . --unit .codestable/features/YYYY-MM-DD-{slug} --audience handoff --output /tmp/codestable-handoff.md --decided "{已决定}" --remaining "{下一步}"
```

For human-facing reports:

```bash
python3 .codestable/tools/build-context-packet.py --root . --unit .codestable/features/YYYY-MM-DD-{slug} --audience human-reviewer --language {en-or-zh} --output /tmp/codestable-human-review.md --decided "{decided}" --remaining "{next step}" --evidence "{verification evidence}"
```

Choose `{en-or-zh}` by mapping `.codestable/attention.md` to a supported tool
language. If the project's report language policy is not covered by the tool's
`--language` choices, write or adapt the human-facing report in the project
language instead of passing the raw attention prose as a CLI value.

Run sufficiency gate before sending:

```bash
python3 .codestable/tools/check-context-sufficiency.py --file /tmp/codestable-human-review.md --strict --json
```

## Finish And Commit Gates

Before finish / merge:

```bash
python3 .codestable/tools/codestable-finish-worktree.py --root . --unit .codestable/features/YYYY-MM-DD-{slug} --json --validation "{验证命令} -> {结果}"
```

Finish gate writes learning, context-check, merge-readiness, and inbox records.
If a branch changes after the finish report, state becomes `stale-report` and
finish must rerun.

Commit finish artifacts as a small final commit when the gate passes:

```bash
git add .codestable/features/YYYY-MM-DD-{slug}/{slug}-learning-report.md \
  .codestable/features/YYYY-MM-DD-{slug}/{slug}-learning-context-check.json \
  .codestable/features/YYYY-MM-DD-{slug}/{slug}-merge-readiness.json
git commit -m "docs: add {slug} finish report"
```

Before commit or final report:

```bash
python3 .codestable/tools/codestable-worktree-gate.py --root . --json commit --unit .codestable/features/YYYY-MM-DD-{slug}
```

Useful status tools:

```bash
python3 .codestable/tools/codestable-doctor.py --root . --json
python3 .codestable/tools/codestable-backlog.py --root . --json
python3 .codestable/tools/codestable-worktree-inbox.py --root . --json
```

Snooze accepted merge deferrals:

```bash
python3 .codestable/tools/codestable-worktree-inbox.py --root . --snooze codex_slug --until 2026-06-12T00:00:00Z --json
```

## Subagent Implementation Choice

Review requires subagents when available. Implementation subagents are optional
and should be proposed when work crosses more than three subsystems, needs
parallel slices, touches high-risk migration / concurrency / runtime contracts,
or exceeds single-thread context. The main thread keeps integration,
verification, and final review ownership.
