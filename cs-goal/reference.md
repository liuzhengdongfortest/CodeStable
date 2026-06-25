# cs-goal Reference

Use this file for templates and recovery rules after `cs-goal` triggers.

## Report Language

Read `.codestable/attention.md` before writing reports. If it contains a report
language policy, follow it. If it does not, use the owner's current conversation
language. Do not hard-code a required two-language pair in this skill.

Use canonical unsuffixed report paths by default. Add language-suffixed copies
only when `.codestable/attention.md` explicitly asks for multiple language
copies.

## Directory

```text
.codestable/goals/YYYY-MM-DD-{slug}/
├── state.yaml
├── goal.md
├── functional-acceptance.md
└── iterations/
    └── 001.md
```

`{slug}` is short English kebab-case, and the date is the goal creation date.
The dated directory name is the filesystem unit; the `state.yaml` `goal` field
remains the bare slug. Reuse an active matching goal instead of creating a
duplicate.

Create `functional-acceptance.md` only during the terminal acceptance gate, not
as an empty file at goal start.

If attention explicitly requires language variants, use suffix copies such as
`goal.{lang}.md`, `functional-acceptance.{lang}.md`, and
`iterations/{nnn}.{lang}.md`. `state.yaml` remains the machine source of truth.

## state.yaml Schema

```yaml
schema_version: 1
goal: "{slug}"
status: active # active | complete | blocked
objective: "{owner-level outcome}"
start_point: "{known starting condition}"
acceptance:
  - "{observable done signal}"
non_goals:
  - "{explicitly out of scope}"
budget:
  kind: none # none | time | iterations | token | owner-defined
  limit: null
current_iteration: 0
next_action: "{smallest useful next attempt}"
blocker_signature: null
blocker_count: 0
owner_stop: null
updated_at: "YYYY-MM-DD"
```

Recovery priority:

1. `state.yaml`
2. latest iteration frontmatter
3. Markdown body

## Start Report

`goal.md` is the durable start report produced from the interview / grill. It
must exist before implementation begins and include:

- objective;
- starting point;
- acceptance criteria;
- non-goals;
- owner decisions;
- unresolved assumptions;
- next action.

These reports are human-readable context only. `state.yaml` remains the machine
source of truth so later agents do not infer state from report prose.

## Next Iteration Number

`state.yaml.current_iteration` means the last completed iteration, not the next
in-progress attempt.

Before changing `current_iteration`, compute the next `{nnn}` as:

```text
max(state.yaml.current_iteration, highest existing iterations/{nnn}*.md) + 1
```

Format it with three digits, write `iterations/{nnn}.md`, then leave
`state.yaml.current_iteration` equal to that completed number. Never overwrite
an existing iteration file. Add language-suffixed copies only when attention
requires them.

## goal.md Template

Use headings in the project's report language while preserving these section
semantics:

```markdown
---
doc_type: goal
goal: {slug}
status: active
---

# {Goal Name}

## Objective

## Starting Point

## Acceptance Criteria

## Non-Goals

## Decisions And Assumptions

## Current State

## Next Action
```

## Iteration Frontmatter

```yaml
---
doc_type: goal-iteration
goal: "{slug}"
iteration: 1
status_after: active # active | complete | blocked
next_action: "{same meaning as state.yaml}"
blocker_signature: null
updated_at: "YYYY-MM-DD"
---
```

## Iteration Headings

Use headings in the project's report language while preserving these section
semantics:

```markdown
# Iteration 001

## Current Understanding

## Implementation Approach

## Changes This Iteration

## Verification Evidence

## Problems Encountered

## Next Attempt

## State Update
```

## Iteration Rules

- Write reports only at iteration end.
- Include fresh verification evidence, even when the iteration failed.
- If nothing changed, say so and explain what was learned.
- Keep historical failed attempts in iteration reports; do not rewrite them into
  success.
- Update `state.yaml` with the iteration report so resume sees the same
  completed iteration, next action, and status that humans read.

## Functional Acceptance Report

Before `status: complete`, dispatch a subagent for product-facing functional
acceptance. Record the result in `functional-acceptance.md`.

The report must include:

- reviewer and subagent role;
- acceptance criteria checked;
- functional evidence beyond tests alone;
- verdict: pass, fail, or inconclusive;
- residual risks and follow-up;
- the final iteration that cites this acceptance.

Tests, linters, and builds are verification evidence, but completion requires
subagent functional acceptance. If subagent dispatch is unavailable or not
authorized, write `approval-report.md` and owner-stop instead of marking the
goal complete.

## Owner Stop Record

When stopping, update `state.yaml`:

```yaml
status: blocked
blocker_signature: "{stable short phrase}"
blocker_count: 3
owner_stop: "{question or approval needed}"
next_action: "Wait for owner decision on {topic}."
```

The latest iteration report must explain:

- what decision is needed;
- why AI cannot safely continue;
- options or expected answer shape;
- what will happen after the owner answers.

## Relationship To Other Flows

`cs-goal` may create or reference feature, issue, refactor, roadmap, or decision
artifacts when their rules apply. The goal state remains the wrapper for
autonomous iteration; child artifacts remain the source of truth for their own
workflow.
