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
  | Awaiting WaitReason
  | HumanCheckpoint Reason
  | NeedsHuman Reason
  | Completed Summary
```

The spec should define the smallest data model needed to make decisions. Do not model every file field unless it affects routing, safety, or output.

## Haskell Contract Standard

Use Haskell-style notation as a compact decision contract, not as decoration and not as a claim that
the Markdown compiles. Follow the shape used by typed iteration protocols: declare the boundary,
close the decision domains, encode branch priority in equations/guards, state path-wide invariants,
and make termination observable.

For a branched protocol, prefer this minimum shape:

```haskell
contractDecision :: Input -> State -> Outcome

data Input = Start Request | Resume RepoFacts | Retry Evidence
data State = Pending | Active Progress | Terminal Result
data Outcome = Run Step | Completed Result | Blocked Reason
data Reason = InvalidTransition | MissingEvidence | ExternalUnavailable

contractDecision _ (Terminal result) = Completed result
contractDecision (Start request) Pending
  | valid request = Run Initialize
  | otherwise     = Blocked MissingEvidence
contractDecision (Resume facts) state = selectFromFacts facts state
contractDecision _ _ = Blocked InvalidTransition

mayComplete state = terminal state && requiredEvidencePresent state
```

Apply these rules:

- Give each public decision function a `::` signature. Types may remain domain names, but input and
  output boundaries must be visible.
- Define finite alternatives with `data`; use constructors consistently in the equations, prose,
  persisted artifacts, runtime router, and fixtures.
- Make guard order express priority. Put terminal/invalid precedence first when it must win, and put
  a wildcard fallback last so it cannot swallow a meaningful `Failed` / `Blocked` distinction.
- Keep failure categories distinct when they imply different recovery: retryable failure, missing
  evidence, human checkpoint, and terminal rejection are not one catch-all branch.
- Use `NeedsHuman` for missing input/capability, `HumanCheckpoint` only for an actual owner decision,
  `Awaiting` for already-started external work, and `Blocked` for an observable terminal or retryable
  failure. Waiting is not approval, and missing evidence is not an owner decision.
- Every `HumanCheckpoint` must have an explicit resume input or persisted state transition. A pending
  cross-skill handoff must retain its target and complete context so approval can resume without
  reclassification or chat-memory reconstruction.
- In a staged workflow, the canonical main entry's tagged resume union must carry every stage-level
  resume decision. A closed `Resume*` type inside a reference is still unreachable if the main entry
  cannot represent and forward it.
- Every `Awaiting` branch must persist a machine-readable state plus the external run id before it
  returns. The restore path must reject missing ids and ambiguous legacy `blocked` states.
- Express global conditions with `where` or a named predicate (`mayComplete`, `invariant`,
  `converged`); do not hide a required branch or completion condition in a comment.
- For iterative protocols, define `step`/`advance`, convergence, and termination separately. A
  component evolved in iteration n is not stable until a later iteration validates it in practice.
- End every decision surface in an observable outcome or explicit invalid transition. Do not leave
  ellipses, implied defaults, or prose-only branches inside the contract.

Reference-only or template documents do not need Haskell. Use it only where a closed decision,
transition, lifecycle, gate, or invariant exists.

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

## Runtime Alignment

When a workflow also has a deterministic router/hook, define one explicit normalization from persisted facts to the Spec state:

```text
artifact fields -> Spec state -> outcome
```

Keep these aligned:

- persisted field/value names and Spec constructors;
- guard order, especially invalid-state and terminal-state precedence;
- dispatch vs fallback handoff vs already-running driver;
- completion/handoff behavior when stale driver metadata remains;
- routing fixture inputs and expected outcomes.

The runtime is executable enforcement of the Spec, not permission to leave a contradictory prompt state machine in `SKILL.md`. Tests should call the real router and reject deprecated fixture keys; do not rely only on a hand-written test model.

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

## Review Report Template

```text
Classification:
Refactor depth: minimal hardening patch | full protocol refactor
Trigger contract:
Spec:
Process protocol:
State restoration:
Runtime alignment:
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

## CodeStable Shape Patterns

- **Main workflow skills**（cs-feat / cs-issue / cs-epic / cs-docs）: optimize for entry intent parsing, repository-fact restoration, stage routing, human checkpoints, progressive reference loading, clear final handoff.
- **Compatibility shims**: keep thin — set `requested_stage` / `requested_mode` and route to the main skill; never maintain independent rules.
- **Cross-skill handoffs**: route to the canonical main entry and preserve context; do not preselect that skill's internal stage, mode, or lane. Compatibility shims are the only exception because passing a legacy preset is their complete contract.
- **Fastforward modes**: a mode request, not permission to skip safety; must state eligibility and rejection conditions; if rejected, route back to the standard workflow and explain why.
- **Goal / long-running handoff**: specify what artifact is handed off, what signal means success / blocked / needs-human, the visible fallback command, and which state files make recovery possible.

## Output Contract

Final answers should include:

- what changed or what was decided;
- current stage/status;
- files written;
- next action or checkpoint;
- validation run or reason validation was not run.

Do not end with vague "let me know" guidance when there is a concrete next step.
