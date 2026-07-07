---
name: build-cs-skill
description: "CodeStable skill authoring protocol. Use when creating, refactoring, simplifying, or reviewing cs-* skills under plugins/codestable/skills or .claude/skills. Applies the prompt-as-code framework: classify the skill, define Spec/types/state machine, separate operator rules from references, add machine-checkable contracts, and design decision fixtures. Do not use for normal feature implementation; use cs-feat/cs-issue/cs-docs for product work and cs-skill-lab for full measured experiment loops."
---

# build-cs-skill

## Purpose

Use this skill to turn a CodeStable skill into a small, recoverable, testable protocol. The output is either a new `SKILL.md` or a focused refactor plan for an existing `cs-*` skill.

The governing principle:

```text
SKILL.md is prompt-as-code. Its quality is measured by behavior, recoverability, and testability, not by length.
```

## Scope

Target skill roots:

- `plugins/codestable/skills/<skill-name>/`
- `.claude/skills/<local-skill-name>/`

Before changing a CodeStable skill, read the target `SKILL.md` and only the references needed for the current stage. Preserve user edits and existing compatibility entry points unless explicitly asked to remove them.

## Spec

```haskell
buildCsSkill :: SkillWorkRequest -> SkillWorkOutcome

data SkillWorkRequest = SkillWorkRequest
  { targetSkill  : Path
  , intent       : Create | Refactor | Simplify | Review | AddContracts | AddFixtures
  , constraints  : [Constraint]
  }

data SkillKind
  = OperatorSkill       -- narrow trigger, concrete artifact, explicit state/branching
  | WorkflowSkill       -- orchestrates stages and loads references progressively
  | MethodologySkill    -- broad guidance; should expose an operator entry plus references
  | ReferenceDoc        -- no stable user -> artifact path; should not be an active trigger

data SkillShape = SkillShape
  { trigger        : TriggerContract
  , entryPoint     : FunctionSignature
  , stateModel     : Maybe StateMachine
  , outputContract : OutputContract
  , failureModes   : [FailureMode]
  , contracts      : [MachineContract]
  , fixtures       : [DecisionFixture]
  }

data SkillWorkOutcome
  = PatchApplied [Path]
  | RefactorPlan SkillShape
  | NeedsHuman Reason
```

## Workflow

### 1. Preflight

Read `.codestable/attention.md` when present. If it is missing in a CodeStable repo, report that the repo may need `cs-onboard`; do not substitute `AGENTS.md` or `CLAUDE.md` as the CodeStable source of truth.

Check git status before editing. Do not revert unrelated changes.

### 2. Classify the skill

Classify the target before writing:

| Kind | Use when | Required shape |
|---|---|---|
| `OperatorSkill` | User asks for one concrete artifact or action | `## Spec`, typed inputs/outputs, failure behavior, contracts |
| `WorkflowSkill` | Skill routes through stages such as design/review/QA | state machine, progressive reference loading, checkpoints |
| `MethodologySkill` | Skill contains broad engineering guidance | small operator front door plus reference sections/files |
| `ReferenceDoc` | No clear trigger -> artifact path | remove from active trigger set or mark as reference material |

If a skill mixes kinds, split the active operator protocol from reference material instead of adding more prose.

### 3. Tighten the trigger

Rewrite `description` so it states:

- what user requests should trigger this skill;
- what adjacent requests should not trigger it;
- the expected artifact or workflow boundary.

Avoid broad verbs alone, such as "optimize", "improve", "analyze", or "help". Add exclusions when overlap exists with `cs-feat`, `cs-issue`, `cs-docs`, `cs-epic`, `cs-audit`, `cs-refactor`, or local authoring skills.

### 4. Write the operator protocol first

Put execution-critical content in the first half of `SKILL.md`:

1. startup/preflight;
2. entry intent parsing;
3. `## Spec` with types and the main function;
4. state restoration or branch selection;
5. human checkpoints;
6. failure behavior;
7. output contract.

Move long examples, templates, rationale, and pattern libraries to `references/` or late sections. Do not let background material precede the protocol.

### 5. Make state recoverable

For workflow skills, define restoration from repository facts, not chat history:

```text
repo facts -> state model -> next action
```

Every stage transition must leave durable evidence on disk, such as a status field, review artifact, checklist, result file, marker, or note. "The previous assistant said so" is not recoverable state.

### 6. Add progressive reference loading

State which reference file is loaded for each stage. The skill must not load all references at startup.

Use this wording when relevant:

```text
Load exactly one stage protocol before acting, plus only the support files that protocol requests.
```

### 7. Add machine contracts

If the local validation system supports frontmatter contracts, add `contracts:`. If it does not, still include a `## Machine Contracts` section so the invariants are explicit and can later be wired into validation.

Good contracts protect the skill's skeleton:

```yaml
contracts:
  - grep: "FeatureState"
  - grep: "restoreFeatureStage"
  - grep: "HumanCheckpoint"
  - grep: "progressive reference loading"
  - not-grep: "git push"
  - not-grep: "read all references"
```

Select terms that would be missing only if an important rule was lost. Avoid generic words like `quality`, `check`, `best`, or `review`.

### 8. Design decision fixtures

For important branch logic, draft fixture cases even if the runner is not implemented yet. A fixture should test one decision:

```yaml
name: review-passed-requires-human-confirmation
step: restoreFeatureStage
state:
  has_design: true
  design_status: draft
  design_review: passed
expect:
  result_type: HumanCheckpoint
  reason: ConfirmDesign
  must_not_route_to: GoalPackage
```

Prioritize fixtures for:

- activation/routing;
- stage ordering;
- forbidden actions;
- human checkpoints;
- failure paths;
- fastforward or compatibility shortcuts.

### 9. Define failure behavior

Every skill must say what happens when it cannot safely continue. A good failure result includes:

- current artifact or directory;
- blocking reason;
- next user action;
- files already written;
- whether retry is safe.

Do not silently continue when approved scope, public contracts, data shape, or user-visible behavior would change.

### 10. Keep the file small

Prefer a short `SKILL.md` plus references over a large always-loaded file. As a rule of thumb:

- active protocol: first 150-250 lines;
- examples and templates: references;
- detailed rationale: docs or references;
- scripts: deterministic checks and repeated transformations.

## CodeStable Patterns

### Main workflow skills

For skills like `cs-feat`, `cs-issue`, `cs-epic`, or `cs-docs`, optimize for:

- entry intent parsing;
- repository-fact restoration;
- stage routing;
- human checkpoints;
- progressive reference loading;
- clear final handoff.

### Compatibility skills

For deprecated or compatibility entries, keep them thin. They should set a `requested_stage`, `requested_mode`, or route to the main skill. They should not maintain independent rules.

### Fastforward modes

Fastforward is a mode request, not permission to skip safety. It must state eligibility and rejection conditions. If rejected, route back to the standard workflow and explain why.

### Goal or long-running handoff

When a skill hands work to a goal driver or background agent, specify:

- what artifact is handed off;
- what signal means success, blocked, or needs human;
- what the visible fallback command is;
- which state files make recovery possible.

## Output

When reporting a proposed or completed skill rewrite, include:

- skill kind classification;
- key trigger changes;
- new or changed Spec/state model;
- contracts added or recommended;
- fixtures recommended;
- reference files that remain stage-loaded;
- known gaps or decisions needing maintainer confirmation.

Keep unrelated product changes out of the skill rewrite unless the user explicitly asks for them.
