---
name: build-cs-skill
description: "CodeStable skill authoring protocol. Use when creating, refactoring, simplifying, or reviewing cs-* skills under plugins/codestable/skills or .claude/skills. Applies the prompt-as-code framework: classify the skill, define Spec/types/state machine, separate operator rules from references, add machine-checkable contracts, and design decision fixtures. Do not use for normal feature implementation; use cs-feat/cs-issue/cs-docs for product work and eval-cs-skill for full measured experiment loops."
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

## References

Load these files only when the current task needs that layer:

- `references/cs-skill-spec-standard.md`: read when writing or refactoring `description`, `## Spec`, state models, failure behavior, or output contracts.
- `references/cs-skill-quality-gates.md`: read when reviewing a skill for prompt-as-code quality, P1/P3 separation, contracts, progressive loading, or regression risk.
- `references/cs-skill-fixture-patterns.md`: read when designing decision fixtures for routing, checkpoints, forbidden actions, failure paths, fastforward, or compatibility entries.

## Spec

```haskell
buildCsSkill :: SkillWorkRequest -> SkillWorkOutcome

data SkillWorkRequest = SkillWorkRequest
  { targetSkill  : Path
  , intent       : Create | Refactor | Simplify | Review | AddContracts | AddFixtures
  , userIntent   : UserIntent
  , targetRepo   : Path
  , constraints  : [Constraint]
  }

data RefactorDepth
  = MinimalHardeningPatch
  | FullProtocolRefactor

data ProcessProtocol
  = WorkflowProtocol
  | DomainProtocol
  | LifecycleProtocol
  | OperationProtocol
  | AlgorithmProtocol
  | ShimRoute
  | ReferenceOnly

data SkillKind
  = OperatorSkill       -- narrow trigger, concrete artifact, explicit state/branching
  | WorkflowSkill       -- orchestrates stages and loads references progressively
  | MethodologySkill    -- broad guidance; should expose an operator entry plus references
  | ReferenceDoc        -- no stable user -> artifact path; should not be an active trigger

data SkillShape = SkillShape
  { trigger        : TriggerContract
  , entryPoint     : FunctionSignature
  , refactorDepth  : RefactorDepth
  , process        : ProcessProtocol
  , stateModel     : Maybe StateMachine
  , outputContract : OutputContract
  , failureModes   : [FailureMode]
  , contracts      : [MachineContract]
  , fixtures       : [DecisionFixture]
  }

data SkillWorkOutcome
  = PatchApplied [Path]
  | RefactorPlan SkillShape
  | ReviewReport SkillShape
  | NeedsHuman Reason

selectRefactorDepth :: UserIntent -> RefactorDepth
selectRefactorDepth(intent)
  | explicitMinimal(intent) -> MinimalHardeningPatch
  | otherwise               -> FullProtocolRefactor

classifySkill :: SkillSource -> SkillKind
selectProcessProtocol :: SkillKind -> ProcessProtocol
selectProcessProtocol(kind) =
  case kind of
    WorkflowSkill    -> WorkflowProtocol
    OperatorSkill    -> OperationProtocol
    MethodologySkill -> DomainProtocol
    ReferenceDoc     -> ReferenceOnly

buildSkillShape :: SkillSource -> UserIntent -> SkillShape
validateSkillShape :: SkillShape -> ValidationReport
```

## Workflow

### 1. Workspace safety

`build-cs-skill` creates or edits skill files; it does not execute a product CodeStable workflow. Do not require `.codestable/attention.md` just to author or refactor a skill.

Before editing, check git status in the target repository. Preserve unrelated user changes. Do not revert or move existing skill files unless explicitly requested.

When authoring an active `cs-*` skill that will run inside CodeStable projects, include that target skill's CodeStable preflight rule. The generated target skill should read `.codestable/attention.md` when it depends on project setup, repo state, artifact writes, or recoverability. That rule belongs in the target skill, not in `build-cs-skill` itself.

### 2. Choose refactor depth

Default to `full protocol refactor` unless the user explicitly asks for a minimal patch, a small additive change, or no behavior-preserving rewrite.

Use these labels exactly:

| Depth | Meaning | Completion bar |
|---|---|---|
| `minimal hardening patch` | Add a small safety layer while preserving the existing shape | trigger tightening, small `## Spec`, or contracts only |
| `full protocol refactor` | Rewrite the active skill body into a complete prompt-as-code protocol while preserving behavior | all required protocol sections below |

A change that only adds description exclusions, a small `## Spec`, and machine contracts is a `minimal hardening patch`, not a `full protocol refactor`. If the user asked to refactor, simplify, or apply the build-cs-skill framework, produce a full protocol refactor or clearly state that the current proposal is only minimal hardening and ask whether to continue.

A full protocol refactor must include all of these, even when behavior is unchanged:

1. tightened frontmatter description;
2. `## Spec` with entry function, request, state, outcome, and failure types;
3. process protocol appropriate to the skill kind;
4. explicit state restoration and next-action selection functions;
5. state machine mirrored as decision rules, not only left as a prose table;
6. progressive reference loading with allowed and forbidden loading behavior;
7. human checkpoint rules and non-bypass conditions;
8. failure behavior;
9. output contract;
10. machine contracts or recommended frontmatter contracts;
11. decision fixture recommendations.

### 3. Classify the skill

Classify the target before writing:

| Kind | Use when | Required shape |
|---|---|---|
| `OperatorSkill` | User asks for one concrete artifact or action | `## Spec`, typed inputs/outputs, failure behavior, contracts |
| `WorkflowSkill` | Skill routes through stages such as design/review/QA | state machine, progressive reference loading, checkpoints |
| `MethodologySkill` | Skill contains broad engineering guidance | small operator front door plus reference sections/files |
| `ReferenceDoc` | No clear trigger -> artifact path | remove from active trigger set or mark as reference material |

If a skill mixes kinds, split the active operator protocol from reference material instead of adding more prose.

### 4. Tighten the trigger

Rewrite `description` so it states:

- what user requests should trigger this skill;
- what adjacent requests should not trigger it;
- the expected artifact or workflow boundary.

Avoid broad verbs alone, such as "optimize", "improve", "analyze", or "help". Add exclusions when overlap exists with `cs-feat`, `cs-issue`, `cs-docs`, `cs-epic`, `cs-audit`, `cs-refactor`, or local authoring skills.

### 5. Write the operator protocol first

Put execution-critical content in the first half of `SKILL.md`:

1. target preflight when applicable;
2. entry intent parsing;
3. `## Spec` with types and the main function;
4. process protocol appropriate to the skill kind;
5. state restoration or branch selection;
6. human checkpoints;
7. failure behavior;
8. output contract.

Choose the process section by skill kind:

| Skill kind | Required process section |
|---|---|
| `WorkflowSkill` | `## Workflow`, `## Protocol`, or `## Lifecycle` with the runtime path in 5-7 ordered steps |
| `OperatorSkill` | `## Operation` or `## Algorithm` with the input -> action -> output path |
| compatibility shim | no workflow required; state target skill and passed intent |
| `ReferenceDoc` | no workflow required; state why it is reference material |

For target skills, include a preflight step when the skill touches `.codestable/`, scans repo state, writes artifacts, dispatches agents, or depends on project initialization. For pure formatting, routing shims, or reference-only materials, a separate preflight step is usually unnecessary.

For workflow skills, the process section should be shorter than the detailed decision rules and explain what the agent actually does from startup to recoverable exit. Do not replace it with only a type signature or only a routing table.

Move long examples, templates, rationale, and pattern libraries to `references/` or late sections. Do not let background material precede the protocol.

### 6. Make state recoverable

For workflow skills, define restoration from repository facts, not chat history:

```text
repo facts -> state model -> next action
```

Every stage transition must leave durable evidence on disk, such as a status field, review artifact, checklist, result file, marker, or note. "The previous assistant said so" is not recoverable state.

### 7. Add progressive reference loading

State which reference file is loaded for each stage. The skill must not load all references at startup.

Use this wording when relevant:

```text
Load exactly one stage protocol before acting, plus only the support files that protocol requests.
```

### 8. Add machine contracts

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

### 9. Design decision fixtures

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

### 10. Define failure behavior

Every skill must say what happens when it cannot safely continue. A good failure result includes:

- current artifact or directory;
- blocking reason;
- next user action;
- files already written;
- whether retry is safe.

Do not silently continue when approved scope, public contracts, data shape, or user-visible behavior would change.

For `build-cs-skill` itself, return `NeedsHuman` when:

- `targetSkill` is missing or ambiguous;
- the requested output location is unclear;
- the target file has unrelated user changes in sections that must be edited;
- a full protocol refactor would require behavior changes but the user requested behavior-equivalent edits only;
- the target skill references missing protocol files and the intended behavior cannot be inferred;
- the user asks for measured evaluation rather than authoring/refactor; route to `eval-cs-skill` instead.

### 11. Keep the file small

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

When reporting a proposed or completed skill rewrite, use this structure:

```text
Classification:
Refactor depth: minimal hardening patch | full protocol refactor
Trigger contract:
Spec:
Process protocol:
State restoration:
Stage routing / decision rules:
Progressive reference loading:
Human checkpoints:
Failure behavior:
Output contract:
Machine contracts:
Decision fixtures:
Preserved behavior / unchanged sections:
Open maintainer decisions:
```

If the output is not a full protocol refactor, explicitly name which required sections are missing and why.

Keep unrelated product changes out of the skill rewrite unless the user explicitly asks for them.

## Output Contract

`build-cs-skill` final responses must include:

- target skill path;
- classification;
- refactor depth;
- files changed or planned;
- validation result, or reason validation was not run;
- missing confirmations or maintainer decisions;
- next concrete action.

When editing files, distinguish files actually changed from sample files or proposed fixtures.

## Machine Contracts

Keep these invariants in the body unless the local validator supports frontmatter `contracts:`:

```yaml
contracts:
  - grep: "SkillWorkRequest"
  - grep: "RefactorDepth"
  - grep: "ProcessProtocol"
  - grep: "selectRefactorDepth"
  - grep: "selectProcessProtocol"
  - grep: "FullProtocolRefactor"
  - grep: "MinimalHardeningPatch"
  - grep: "Target Skill Preflight"
  - grep: "Output Contract"
  - not-grep: "read `.codestable/attention.md` just to author"
```
