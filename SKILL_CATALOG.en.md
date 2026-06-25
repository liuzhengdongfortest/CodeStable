# CodeStable Skill Catalog

| Group | Skill | Purpose |
|---|---|---|
| Root entry | `cs` | Unified entry that introduces the system and routes open-ended intents to the right `cs-*` skill |
| Onboard | `cs-onboard` | Bring CodeStable into a new repo or one with scattered docs |
| Requirement and architecture | `cs-req` | Curate and accumulate raw requirement docs |
| Requirement and architecture | `cs-arch` | Draft or update architecture docs under `codestable/architecture/` |
| Roadmap | `cs-roadmap` | Plan big work up front: high-level design, interface contracts, sub-feature breakdown |
| Roadmap | `cs-roadmap-review` | Independent planning review gate before human roadmap approval |
| Roadmap | `cs-roadmap-impl-goal` | Turn an approved roadmap into a runnable goal that executes impl / review / QA / accept per feature |
| Discussion entry | `cs-brainstorm` | Triage fuzzy ideas: direct design, feature brainstorm, or roadmap |
| Feature flow | `cs-feat` | Sub-flow entry for new features |
| Feature flow | `cs-feat-design` | Draft `{slug}-design.md` as the single input for what follows |
| Feature flow | `cs-feat-design-review` | Independent feature design review gate before human approval |
| Feature flow | `cs-feat-impl` | Code in the order the design lays out |
| Feature flow | `cs-code-review` | Read-only code review gate after implementation |
| Feature flow | `cs-feat-qa` | Local QA verification gate after code review |
| Feature flow | `cs-feat-accept` | Verify implementation against the design and close the loop |
| Feature flow | `cs-feat-ff` | Ultra-light lane: no design, no phases, direct implementation |
| Issue flow | `cs-issue` | Sub-flow entry for issue fixing |
| Issue flow | `cs-issue-report` | Turn a problem into a reproducible, traceable report |
| Issue flow | `cs-issue-analyze` | Find root cause, assess risk, propose options |
| Issue flow | `cs-issue-fix` | Targeted fix, verification, and fix-note |
| Refactor flow | `cs-refactor` | Beta main refactor flow |
| Refactor flow | `cs-refactor-ff` | Beta light refactor lane |
| Knowledge sink | `cs-learn` | Sink pitfalls or good practices into learning docs |
| Knowledge sink | `cs-trick` | Curate reusable patterns or library usage as prescriptive references |
| Knowledge sink | `cs-decide` | Record settled tech choices, architectural decisions, and long-term constraints |
| Knowledge sink | `cs-note` | Append one-line startup notes to `.codestable/attention.md` |
| Explore and docs | `cs-explore` | Targeted code exploration; sink “ask -> read -> conclude” into evidence |
| Explore and docs | `cs-audit` | Audit code for bug, security, performance, maintainability, and architecture risks |
| Explore and docs | `cs-guide` | Write outward-facing developer guides |
| Explore and docs | `cs-libdoc` | Generate reference docs for public library surfaces |
| Explore and docs | `cs-docs-neat` | Reconcile `.codestable/`, README/docs, `CLAUDE.md` / `AGENTS.md`, and agent memory at phase close |
