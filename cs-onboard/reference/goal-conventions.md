# Goal Conventions

This file is copied by `cs-onboard` to
`.codestable/reference/goal-conventions.md`. It defines the shared runtime shape
for `cs-goal`.

## Purpose

Goals are bounded start/end work units. The owner defines the outcome and
acceptance signal; AI interviews / grills briefly, writes a start report,
implements, verifies, self-iterates, and writes iteration reports. A goal can
close only after subagent functional acceptance of the produced result.

Use goals when the request says "reach this result", "run until accepted",
"self-iterate", "AI implements autonomously", or "grill me first".

## Report Language

All goal report prose follows `.codestable/attention.md`. If attention has no
report language policy, use the owner's current conversation language. Do not
hard-code required two-language report pairs in this shared convention.

Use the canonical unsuffixed files below by default. Add language-suffixed
copies only when attention explicitly requires multiple language copies.

## Directory

```text
.codestable/goals/YYYY-MM-DD-{slug}/
├── state.yaml
├── goal.md
├── functional-acceptance.md
└── iterations/
    └── 001.md
```

The directory date is the goal creation date. `state.yaml.goal` remains the bare
slug so humans and agents can compare related dated units without parsing the
filesystem name.

`state.yaml` is the machine source of truth. Markdown is human-readable context.
Recovery priority is `state.yaml` > latest iteration frontmatter > Markdown
body.

`functional-acceptance.md` is created only during the terminal acceptance gate,
not as an empty file at goal start.

`goal.md` is the start report from interview / grill. It must exist before
implementation and include objective, start point, acceptance, non-goals, owner
decisions, unresolved assumptions, and next action.

## State Model

```text
active | complete | blocked
```

Required `state.yaml` fields:

- `schema_version`
- `goal`
- `status`
- `objective`
- `start_point`
- `acceptance`
- `non_goals`
- `budget`
- `current_iteration`
- `next_action`
- `blocker_signature`
- `blocker_count`
- `owner_stop`
- `updated_at`

`current_iteration` means the last completed iteration, not the next
in-progress attempt.

## Iteration Numbering

Before changing `current_iteration`, compute the next `{nnn}` as:

```text
max(state.yaml.current_iteration, highest existing iterations/{nnn}*.md) + 1
```

Write `iterations/{nnn}.md`, then leave `state.yaml.current_iteration` equal to
that completed number. Never overwrite an existing iteration file. If attention
requires language variants, write the corresponding `iterations/{nnn}.{lang}.md`
copies as well.

## Reporting

Each completed iteration writes the canonical report:

- `iterations/{nnn}.md`

Reports are not command logs. One iteration equals a coherent implementation and
verification attempt. Include the same semantic content even when attention
requires extra language variants: understanding, implementation approach,
changes, verification evidence, problems, next attempt, and state update.

Before `status: complete`, write:

- `functional-acceptance.md`

This report records subagent functional acceptance of the product / artifact
against the owner acceptance criteria. Include reviewer, scope, functional
evidence, verdict, residual risks, and the final iteration that cites it. Tests
alone are not enough to complete a goal.

## Strict Owner Stops

Stop only when:

- acceptance criteria conflict;
- objective / start / terminal condition has major ambiguity;
- continuing changes long-lived specs, public contract, or capability boundary
  beyond the recorded goal;
- the same blocker repeats for three consecutive iterations;
- budget is exhausted or nearly exhausted;
- risk acceptance, secrets, destructive action, external purchase, merge, or
  deployment approval is required.

Routine technical choices and ordinary failed attempts stay AI-owned.
