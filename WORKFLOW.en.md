# CodeStable Workflow and Runtime Structure

## Workflow Layers

CodeStable skills are layered and event-driven:

```text
cs
└── cs-onboard
    ├── cs-req / cs-arch
    ├── cs-roadmap
    │   ├── cs-roadmap-review
    │   └── cs-roadmap-impl-goal
    ├── cs-feat-design -> cs-feat-design-review -> cs-feat-impl -> cs-code-review -> cs-feat-qa -> cs-feat-accept
    ├── cs-issue-report -> cs-issue-analyze -> cs-issue-fix -> cs-code-review
    ├── cs-refactor / cs-refactor-ff -> cs-code-review
    └── cs-learn / cs-trick / cs-decide / cs-explore / cs-note / cs-docs-neat
```

Vertical means layers, not strict time order. Long-lived archives are refreshed repeatedly; the roadmap layer is entered for large needs. Execution is event-driven: new capability goes to feature flow, bugs go to issue flow, and code rot goes to refactor flow. The cross-cut layer is the knowledge flywheel.
`cs-docs-neat` is the phase-close cleanup skill: it reconciles `.codestable/`, README/docs, `CLAUDE.md` / `AGENTS.md`, and agent memory without adding a new archive document type.

## Runtime Structure

After `/cs-onboard`, the project root gets `codestable/`:

```text
codestable/
├── requirements/
├── architecture/
├── roadmap/
├── features/
├── issues/
├── refactors/
├── compound/
├── tools/
└── reference/
```

Key constraints:

- `requirements/` and `architecture/` are long-lived archives and record current state.
- `roadmap/` is the planning layer for large needs.
- `features/`, `issues/`, and `refactors/` use `YYYY-MM-DD-{slug}/` to group one workflow run.
- `compound/` is the single knowledge sink; `doc_type` distinguishes learning / trick / decision / explore.
- `reference/` is released by `cs-onboard`; cross-skill shared docs must go through project-local `codestable/reference/`, not direct references to another skill package.
