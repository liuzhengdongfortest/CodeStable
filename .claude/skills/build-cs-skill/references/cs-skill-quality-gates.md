# CodeStable Skill Quality Gates

Use this reference when reviewing whether a `cs-*` skill is maintainable and testable.

## Prompt-As-Code Rule

A skill is an executable protocol, not an explanatory article. Quality comes from:

- narrow trigger;
- explicit state model;
- process protocol appropriate to the skill kind;
- recoverable outputs;
- clear failure behavior;
- small active protocol;
- machine-checkable invariants;
- decision fixtures for risky branches.

Longer is not automatically better. Extra context can reduce reliability when it hides the rules the agent must follow.

## P0/P1/P2/P3 Sorting

Sort every paragraph by priority:

| Level | Meaning | Best location |
|---|---|---|
| P0 | Safety/security that must not rely on prompt obedience | hooks, scripts, sandbox, CI |
| P1 | Workflow contract the agent must follow | top-level `SKILL.md`, `## Spec`, contracts |
| P2 | Quality preference needing judgment | review checklist, QA protocol |
| P3 | Background, examples, rationale, templates | `references/` or docs |

Refactor when P3 appears before P1, or when the first 150 lines do not tell the agent how to act.

## Progressive Loading Gate

For skills with references, check:

- main `SKILL.md` names each reference;
- each reference has a clear load condition;
- startup does not read every reference;
- each stage loads one protocol first;
- support files are loaded only when the protocol asks for them.

Good wording:

```text
Load exactly one stage protocol before acting, plus only the support files that protocol requests.
```

## Idempotent Context Loading Gate

Progressive loading answers *which* reference a stage loads; this gate answers *whether a project fact already in context must be re-read*. They are complementary — stage granularity vs session granularity.

Project facts (`attention.md`, `CONTEXT.md`, `adrs/`, `compound/`, prior `features/` designs) are read to load project conventions and prevent term conflicts / ADR violations. That value is real on the first read in a fresh context, but re-reading the same fact later in one session (per-skill preflight re-reading `attention.md`, brainstorm→design, multi-round design, or epic×N children) only burns tokens. Startup steps worded as "必读 / 总是先搜 / 共同必读 / 先跑 preflight" encode unconditional re-reads.

For any startup step that loads project facts, check:

- does it say to reuse already-loaded facts instead of unconditionally re-Glob+Read?
- is the first-read value (term-conflict / ADR check) preserved, not deleted?
- for batch fan-out (epic → child designs), is the skip driven by a **structural flag**, not wording?

Good wording (soft guard, single-session continuation):

```text
首次进入该工作项时读 CONTEXT.md / adrs / compound（防术语冲突、防违反已拍板决策）；
若本会话/本阶段已加载过这些全局输入，则复用已读摘要，不重复 Glob+Read。
```

Batch fan-out needs a structural flag, not wording — a soft "reuse if already read" cannot be relied on across N dispatched child stages, because the model has no durable signal that a sibling already loaded the fact. Thread an internal flag (reuse an existing one such as `epic_child_batch` rather than inventing a new state field) so the parent loads global inputs once and children skip explicitly. This mirrors **Measured Rules 6**: batch repetition is a structural gap, not a wording problem.

**Fixture note (why this gate ships contract-only).** The current `routing_decision` scorer compares only the final decision JSON; the api harness is single-turn, tool-less, and hands repo facts in as pre-recovered text. "Did not re-read a file" is therefore inexpressible and unscorable today. Guard this gate with a frontmatter contract (anchor the skip sentence in a SKILL.md body) + `test_skill_contracts.py` + the structural flag, not with a measured fixture. A measured fixture is future work needing a multi-turn, tool-enabled harness or an action-assertion scorer; a routing eval run here is a no-regression check on existing decisions only, never validation of this guard.

## Contract Gate

Contracts protect the skeleton of the skill. They do not prove the agent will make the right decision.

Good contract targets:

- the routing function name (`restoreXStage` / `selectXAction`) when the Spec is the sole routing truth;
- behavioral invariant phrases (required artifacts, checkpoint sentences, forbidden-action rules);
- forbidden actions as `not-grep`;
- critical marker names.

Bad contract targets:

- bare Spec type names (`XState`, `XOutcome`, `HumanCheckpoint`, `CheckpointReason`) — they only prove the Spec block exists, not that any behavior is protected (measured: routing eval 2026-07 showed they add no behavioral value);
- generic words like `quality`, `review`, `check`, `best`;
- strings that appear in examples but not in the actual rule;
- brittle sentences likely to change during normal editing.

If frontmatter contracts are not supported in the local system, keep the invariant list in `## Machine Contracts` so it can be wired later.

## Haskell Contract Semantics Gate

For every changed Haskell-style block, apply the Haskell Contract Standard in
`cs-skill-spec-standard.md`. Check semantics, not just the fence:

- at least one typed boundary (`::`) or closed `data` domain identifies what the contract decides;
- at least one equation/guard maps inputs and state to an outcome;
- terminal, failed, blocked, checkpoint, and invalid states remain distinct where recovery differs;
- wildcard branches are last and do not make a specific branch unreachable;
- named invariants and termination predicates agree with the completion prose;
- every stage-level resume decision is representable in the canonical main entry and forwarded to
  the selected stage; a locally closed reference type does not prove end-to-end resume coverage;
- every `Awaiting` branch has persisted state/reason/run-id evidence and the real restore path rejects
  missing ids plus ambiguous legacy `blocked` states;
- constructors and field names agree with sibling protocols, persisted artifacts, fixtures, and the
  real runtime router when one exists.

A generic test may prove that the contract has a domain and decision surface. Risky branches still
need exact scenario assertions; syntax cannot prove semantic completeness.

## Regression Ladder

Choose the cheapest layer that can fail on the defect, then add downstream evidence when the change
crosses a boundary:

1. **Shape**: frontmatter, reference links/classification, Markdown line limits, required/forbidden
   anchors, schema parsing.
2. **Contract semantics**: Haskell domain + decision surface, constructor vocabulary, guard order,
   explicit negative/terminal branches.
3. **Cross-file**: template/runtime copy equality, shared-convention vocabulary, main-entry/deep-
   protocol agreement, deprecated term absence.
4. **Scenario**: exact repository facts -> exact outcome, plus the nearest unsafe sibling outcome as
   a negative assertion. One decision per fixture.
5. **Runtime conformance**: invoke the real router/hook/parser where it exists; never validate a
   separately hand-written mirror as production evidence.
6. **Forward test**: give a fresh agent the original task and raw artifacts, without the intended
   answer or suspected defect. Use measured multi-model eval only after deterministic layers pass.

Every review finding or user correction that changes behavior must gain a regression at the nearest
deterministic layer. Where practical, verify that the test fails against the pre-fix text/code. A
marker-only test does not close a branch bug; pair it with an exact scenario or cross-file assertion.
Do not report the whole suite green when an infrastructure timeout prevented a layer from completing.

## Live Host Safety Gate

Classify every planned command before execution:

| Impact | Allowed behavior |
|---|---|
| `Hermetic` | no external daemon or user home; preferred default |
| `Isolated` | temporary HOME/cache/socket/endpoint and test-owned children only |
| `LiveReadOnly` | identity/capability snapshots only; no lifecycle mutation |
| `LiveMutating` | explicit owner approval and a dedicated disposable environment required |

For developer machines with active host-managed agent sessions:

- forbid stop/restart/archive/close/kill of external services and forbid broad `pkill`/`killall`;
- never write the user's agent home, route index, socket, endpoint, or provider config;
- isolate integration tests with a per-run temporary home, endpoint, route/cache, and bounded timeout;
- run heavy suites, Go validation, multi-target builders, and package installs serially with an
  explicit worker/resource budget; fixed-concurrency builders must not overlap other heavy work;
- clean up only a PID recorded as created by this run, after an immediate match on PID, UID, argv,
  process start identity, and expected temp path/parent. On any mismatch, preserve it and report;
- for `LiveReadOnly`, compare before/after PID, UID, argv, version/server id, home, and listen address;
  any identity change fails the gate even if assertions passed.

Completion requires: deterministic targeted layers passed; skipped heavy/live layers and reasons are
listed; every test-owned child is reaped or preserved with an ownership warning; external host
identity is unchanged. CI or a quiet disposable host should own the final full-suite/build matrix.

## Behavior Gate

For each important branch, ask:

- What repository facts trigger it?
- What artifact proves it happened?
- What would be unsafe to skip?
- Can a fixture test the decision?

If a branch cannot be tested directly, at least document the expected input state and output outcome.

## Family Audit Coverage Gate

When a request covers every skill or reference in a family, recursively discover the filesystem set first and compare it with the reviewed/classified set by equality. Include every non-`SKILL.md` Markdown file, including root-level `reference.md`, not only `references/**/*.md`. Keep active entries, compatibility shims, Haskell contracts, and structured references in explicit disjoint sets. A sampled list or a one-way subset assertion cannot prove that a newly added skill/reference was reviewed.

For cross-skill routing, assert that upstream operators target the canonical main entry without selecting its internal stage/lane. Compatibility shims may pass a legacy preset; ordinary brainstorm, router, audit, or workflow handoffs may not.

## Runtime Alignment Gate

`SKILL.md` remains the sole prompt routing truth. When a deterministic router, hook, or persisted state schema also exists, it is executable enforcement of that Spec and must be semantically identical.

Check all four surfaces together:

- Spec fields and enums map explicitly to persisted artifact fields/values;
- guard order and terminal-state precedence match runtime code;
- outcomes distinguish continue, dispatch, report, handoff, completion, and invalid/unknown state;
- fixtures use the current Spec field names and cover risky runtime branches.

Conformance tests must invoke the real runtime router where one exists. A separately hand-written "test router" can test a desired story while both prompt and production runtime drift, so it is not alignment evidence. Also add static assertions for deprecated fixture keys and critical Spec/runtime outcome names. Any state-schema change invalidates affected historical routing results until the updated fixtures are rerun.

## Refactor Completeness Gate

Label the depth before judging quality:

- `minimal hardening patch`: only tightens trigger, adds a small Spec, adds contracts, or fixes one local rule.
- `full protocol refactor`: rewrites the active skill body into a complete recoverable protocol.

A full protocol refactor must include trigger contract, Spec, process protocol appropriate to the skill kind, state restoration or branch selection, decision rules when needed, progressive loading when references exist, human checkpoints when applicable, failure behavior, output contract, machine contracts, runtime alignment when applicable, and fixture recommendations. A proposal that only adds three sections is useful hardening, but it is not a full refactor.

## Measured Rules（routing eval 2026-07，7 skill × 3 模型 × k3，[measured]）

以下规则有量化依据（evidence: `experiments/cs-issue-routing-001/results.md`）：

1. **Spec 必须是唯一的 prompt 路由真相，不与散文状态机表格并列**。确定性 runtime 只能作为同一 Spec 的可执行 enforcement，并须通过 Runtime Alignment Gate。并列冗余接近装饰甚至有害：cs-epic 上「表格+Spec 并列」(0.833) 低于重构前只有表格的原版 (0.867)；替代后 0.989。
2. **Spec 的行为增益与原规则含混度成正比**（cs-docs +0.43 > refactor +0.22 > epic +0.12 > feat +0.10 > issue ±0）。规则本就简单清晰的 skill 不必为形式重写。
3. **增益集中在非顶级模型与复杂/嵌套分支**（epic 批量上下文、fastforward 资格、多产物状态恢复）。顶级模型对表达形式不敏感。
4. **给中小模型的分支澄清要显式排除错误选项**（负向澄清），只加正向描述可能引入新歧义：cs-feat ff 分支加「并说明」后 haiku 从全对变全错（答成 NeedsHuman），改为「结果是 RoutedTo Design（不是 NeedsHuman、不是 checkpoint）」后三模型全对。
5. **decision fixture 的 oracle 必须宽容语义等价措辞**（`result_type_any`/`target_any`），且先抽查 observed 再下 verdict——未校准的严格 oracle 会对无 Spec 词汇的旧版本系统性不公平（cs-docs original 校准前 0.222 → 校准后 0.528）。
6. **措辞优化两轮无效 → 查结构缺失，别继续磨措辞**。模型在某分支上持续答错且答案集中在"最接近的枚举项"，通常是 Spec 生命周期有分支没形式化（模型无 guard 可走）：cs-goal rt-g02 两轮枚举限定 0.33→0.33，补上 grill 入口 guard 后一轮 0.33→0.89。routing 函数必须覆盖从触发到退出的**完整**生命周期（含入口/重建/降级分支），guard 顺序即优先级，不可达的尾分支是 bug。

## Anti-Patterns

Fix these before adding more prose:

- Spec branch function AND a prose state-machine table both present (duplicate routing truths — measured harmful, see Measured Rules 1);
- active skill has no `## Spec`;
- workflow skill has no concise `## Workflow`, `## Protocol`, or `## Lifecycle`;
- single-step operator has no `## Operation` or `## Algorithm`;
- stage routing relies on chat history;
- prompt Spec、persisted state、runtime router、fixtures 使用不同字段或终态优先级；
- 测试复制一份手写 router，却不调用真实 runtime 做 alignment；
- compatibility skill duplicates main rules;
- fastforward mode has no rejection criteria;
- implementation details appear before routing rules;
- reference files are loaded eagerly;
- failure path says only "ask user" without current artifact and next action;
- skill can continue past a human checkpoint without explicit confirmation;
- unconditionally re-reads project facts (CONTEXT/ADR/compound) already loaded earlier in the same session or batch.

## Review Output

When reviewing a skill, report:

- skill kind;
- trigger overlap risks;
- missing or weak Spec pieces;
- P1/P3 ordering issues;
- contracts to add;
- fixtures to add;
- references to split or defer-load;
- one or two highest-leverage edits.
