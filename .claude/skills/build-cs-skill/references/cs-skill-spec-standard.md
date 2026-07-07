# CodeStable Skill Spec Standard

Use this reference when authoring or refactoring a CodeStable `SKILL.md`.

## Minimum Shape

Every active `cs-*` skill should have:

- precise frontmatter `description`;
- startup/preflight rule when the skill reads repo state, writes files, dispatches agents, or depends on CodeStable setup;
- entry intent parsing rule;
- `## Spec` with a main function and core data types;
- process protocol appropriate to the skill kind;
- state restoration or branch-selection logic;
- failure behavior;
- output contract;
- progressive reference loading rules when references exist.

Compatibility shims may be shorter, but they should route to a main skill instead of duplicating rules.

## Target Skill Preflight

Use preflight in the generated or refactored target skill when that skill can be affected by CodeStable setup or dirty repo state:

- reads or writes `.codestable/`;
- scans repo facts or git diff;
- creates artifacts;
- dispatches agents or goal drivers;
- depends on project initialization.

For these target skills, a typical preflight is:

```text
1. Read `.codestable/attention.md`.
2. If missing, stop or route to `cs-onboard`.
3. Check git status when edits may occur.
4. Preserve unrelated user changes.
```

Do not force this shape onto pure compatibility shims or reference-only material.

## Trigger Contract

The `description` is the trigger surface. Write it as:

```text
Use when <specific request>. Produces <artifact/workflow>. Do not use for <adjacent skills>.
```

Good descriptions include exclusions for nearby skills:

- `cs-feat`: feature work and product behavior changes.
- `cs-issue`: bug diagnosis and fixes.
- `cs-docs`: user/developer documentation.
- `cs-epic`: multi-feature decomposition.
- `cs-audit`: repo-wide investigation.
- `eval-cs-skill`: measured experiment loops.

Avoid broad trigger words without scope: `improve`, `optimize`, `analyze`, `review`, `help`.

## Spec Section

Use compact Haskell-style signatures to force clear behavior:

```haskell
csSkillName :: Request -> Outcome

data Request = Request
  { args      : Args
  , intent    : Maybe Intent
  , repoFacts : RepoFacts
  }

data Outcome
  = RoutedTo Stage
  | ArtifactWritten Path
  | HumanCheckpoint Reason
  | NeedsHuman Reason
  | Completed Summary
```

The spec should define the smallest data model needed to make decisions. Do not model every file field unless it affects routing, safety, or output.

## Workflow Skills

For workflow skills such as `cs-feat`, `cs-issue`, `cs-docs`, or `cs-epic`, define:

```haskell
restoreState :: RepoFacts -> WorkflowState
selectNextAction :: WorkflowState -> EntryIntent -> Outcome
```

State must come from repository facts, not chat memory. Durable facts include:

- files under `.codestable/`;
- status fields in artifacts;
- review/QA/acceptance files;
- marker files;
- git diff and commits;
- explicit notes written to artifacts.

Also include a compact `## Workflow` before detailed decision rules. Good workflow text looks like:

```text
1. Run preflight.
2. Parse entry intent.
3. Restore state from repo facts.
4. Select next stage.
5. Load only that stage protocol.
6. Execute or stop at checkpoint.
7. Exit with recoverable state.
```

This section is for human and agent orientation. Detailed branch logic belongs in state restoration and decision rules.

## Non-Workflow Operators

For single-step operators, use `## Operation` or `## Algorithm` instead of forcing a workflow:

```text
1. Read input/context.
2. Validate preconditions.
3. Produce the artifact or decision.
4. Validate the output.
5. Report result or failure.
```

For compatibility shims, do not add a workflow. State the target skill and the exact `requested_stage`, `requested_mode`, or arguments passed through.

## Failure Behavior

Every active skill must say when it stops. Use `NeedsHuman` or `HumanCheckpoint` when:

- the target artifact cannot be identified;
- requested stage conflicts with repository facts;
- scope is ambiguous;
- approved design or public contract would change;
- a referenced protocol or required file is missing;
- automation handoff fails;
- continuing would hide risk from the user.

Report the current artifact, blocking reason, safe next action, and files already written.

## Output Contract

Final answers should include:

- what changed or what was decided;
- current stage/status;
- files written;
- next action or checkpoint;
- validation run or reason validation was not run.

Do not end with vague "let me know" guidance when there is a concrete next step.
