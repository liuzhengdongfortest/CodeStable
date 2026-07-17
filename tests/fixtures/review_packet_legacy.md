# CodeStable Implementation Review Packet

- root: `{ROOT}`
- unit: `.codestable/features/demo`
- stage: `implementation`

## Reviewer Mission

Review the implementation as an independent Task agent. Verify the code directly from the packet instead of trusting the implementer summary.

## Stage Focus

scope drift, hidden behavior changes, missing tests, maintainability, edge cases, security, and production safety

## Reviewer Output Contract

- Lead with findings, ordered by severity.
- Include severity (`P0`/`P1`/`P2`/`P3`) and confidence for each finding.
- Reference concrete files, code, docs, or validation evidence when possible.
- If there are no blocking findings, say so explicitly and list residual risks or test gaps.

## Unit Documents
### `.codestable/features/demo/demo-design.md`

```
---
doc_type: feature-design
status: approved
---
# Demo
```

## Git Diff Stat

```
### unstaged
No unstaged diff.

### staged
No staged diff.
```

## Focused Diff

No safe changed paths to diff.

## Validation Commands And Results
- pytest -> passed

## Reviewer Risk Prompts
- Check database and migration safety.
- Check concurrency and race conditions.
- Check idempotency and rerun behavior.
- Check crash-resume persistence.
- Check provider cost and production writes.
- Check deterministic LLM boundary for IDs, paths, enums, and foreign keys.
