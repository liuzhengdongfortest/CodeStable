---
doc_type: refactor-verification-report
refactor: 2026-07-01-skill-entry-simplification
status: passed-with-limitations
started: 2026-07-02
completed: 2026-07-02
summary: Paseo-agent based verification for every changed CodeStable skill entry completed; limitations recorded.
---

# Skill Entry Simplification Paseo Agent Verification

## 1. 验证标准

本报告替代此前的 state-machine 和主 agent 手工 dogfood，只在 Paseo 独立 agent 真实跑完后给最终结论。

通过标准：

- 构建完整隔离开发 repo。
- 把当前分支 CodeStable skills 复制到隔离 repo，作为唯一被测 skill 源。
- 用独立 Paseo agent 读取被测 skill 文件并执行真实 feature / epic / issue / refactor / docs / review 场景。
- `cs-feat` 和 `cs-epic` 的人工 gate 必须显式模拟确认，并记录状态变化。
- 每个改动 skill 都要映射到独立 agent 证据。
- 发现 Blocking / Important 问题后必须修复并重跑受影响验证。

## 2. 隔离 Repo

Path:

```text
/tmp/codestable-paseo-skill-verify/agent-toy-repo
```

Baseline:

```text
c717de8 baseline calcbox verification repo
pytest -q -> 5 passed
```

Skills under test were copied from this branch to:

```text
.codestable/skills-under-test/
```

## 3. 顶层 Agents

| Group | Agent ID | Provider | Scope |
|---|---|---|---|
| feature | `548f6f56-84d7-48cb-a272-fb2e3d471fe0` | `codex/gpt-5.5` | `cs-feat`, feature stage compatibility entries, `cs-code-review` |
| epic | `409060a1-3baf-4f9d-87ca-34519d05a26b` | `codex/gpt-5.5` | `cs-epic`, `cs-roadmap*`, child feature loop |
| issue | `382271e9-feee-4c40-8e82-ad7688610481` | `codex/gpt-5.5` | `cs-issue`, `cs-issue-*`, `cs-code-review` |
| refactor | `7d883aae-28a4-4981-89b8-5aff55534a65` | `codex/gpt-5.5` | `cs-refactor`, `cs-refactor-ff` |
| docs | `113d6087-771d-4e3c-afe2-c81da1a51a92` | `codex/gpt-5.5` | `cs-docs`, `cs-doc-*`, `cs-docs-neat` |
| compat-router | `64e39ffa-59d7-4663-b7bd-dcca082b5e6e` | `codex/gpt-5.5` | `cs`, `cs-brainstorm`, `cs-req`, `cs-onboard`, all compatibility entries |
| code-review | `ee5e2326-c23a-4376-bd7d-0552edfd08a3` | `claude/opus` | `cs-code-review` as independent gate |

## 4. 已收集报告

| Report | Agent | Status | Evidence |
|---|---|---|---|
| `.codestable/verification/agents/docs-agent.md` | docs | passed | 实际生成 dev guide、API manifest/API reference，并用 `cs-docs-neat` 同步 README；`pytest -q` 通过。 |
| `.codestable/verification/agents/compat-router-agent.md` | compat-router | passed | 覆盖 `cs` route brief、`cs-brainstorm`、`cs-req`、`cs-onboard` 和 15 个兼容入口；每个目标 skill 又由子 agent 只读验证。 |
| `.codestable/verification/agents/refactor-agent.md` | refactor | superseded | 共享隔离 repo 中实际重构过 `format_number`，但被并发 agent 覆盖，独立 reviewer 判定 Blocking；不作为最终通过证据。 |
| `.codestable/verification/agents/issue-agent.md` | issue | passed | 实际完成 bug report、analysis、fix、tests 和 `cs-code-review`；`pytest -q` 通过，review 为 `subagent+ocr` passed。 |
| `.codestable/verification/agents/epic-agent.md` | epic | pass-with-limitations | 实际完成 `statistics-support` epic：roadmap、两个 child features、goal 包、review/QA/acceptance/audit；`pytest -q` 10 passed。goal driver 和 independent reviewer 均为验证降级。 |
| `.codestable/verification/agents/code-review-agent.md` | code-review | passed | 验证无参数不空审、`--range` clean-worktree、双环节 reviewer、blocking 不下游和 report template；另写 `adhoc-range-review.md` 示例。 |
| `.codestable/verification/agents/feature-agent.md` | feature | pass-with-limitations | 实际完成 `add-power` feature：design、design-review、模拟人工确认、goal 包、impl、review、QA、acceptance；`CS_FEATURE_GOAL_COMPLETE`。`cs-feat-ff` 仅验证兼容入口与 protocol 读取，未叠加真实快速代码改动。 |
| clean refactor worktree `.codestable/verification/agents/refactor-clean-agent.md` | refactor-clean | passed | 专用 worktree `/Users/wyattfang/.paseo/worktrees/3g3wtzhu/codestable-refactor-clean` 中完成行为等价 refactor；独立 Paseo reviewer `53b27b3b-6bef-40b5-ac6f-03bf88b43d85` passed；commit gate 通过；`pytest -q` 5 passed。 |

## 5. 改动 Skill 覆盖矩阵

| Skill | Current evidence | Status |
|---|---|---|
| `cs` | compat-router top agent + child agent `83c6b4de-8ded-4156-b2b3-aeb61475ec13` | passed |
| `cs-brainstorm` | compat-router child agent `5e2bdb93-5e13-44ac-8961-a291b6ff5340` | passed |
| `cs-req` | compat-router child agent `c3e8269e-58d1-4c80-b98b-480294c9089d` | passed |
| `cs-onboard` | compat-router child agent `86f8754e-f47f-4829-85a3-30e5a9ea16d8` | passed |
| `cs-docs` | docs agent real documentation workflow | passed |
| `cs-doc-tutorial` | docs agent + compat-router child agent | passed |
| `cs-doc-api` | docs agent + compat-router child agent | passed |
| `cs-docs-neat` | docs agent README/index sync | passed |
| `cs-refactor` | clean refactor worktree real workflow | passed |
| `cs-refactor-ff` | clean refactor worktree ff compat note + compat-router child agent | passed |
| `cs-feat` | feature agent real feature workflow | pass-with-limitations |
| `cs-feat-design` | feature agent design + compat-router child agent | passed |
| `cs-feat-design-review` | feature agent design-review + compat-router child agent | passed |
| `cs-feat-impl` | feature agent implementation + compat-router child agent | passed |
| `cs-feat-qa` | feature agent QA + compat-router child agent | passed |
| `cs-feat-accept` | feature agent acceptance + compat-router child agent | passed |
| `cs-feat-ff` | feature agent ff-note + compat-router child agent; no code fastforward | pass-with-limitations |
| `cs-epic` | epic agent real roadmap/goal workflow | pass-with-limitations |
| `cs-roadmap` | epic agent planning stage + compat-router child agent | pass-with-limitations |
| `cs-roadmap-review` | epic agent review stage + compat-router child agent | pass-with-limitations |
| `cs-roadmap-impl-goal` | epic agent goal-package stage + compat-router child agent | pass-with-limitations |
| `cs-issue` | issue agent real bug workflow | passed |
| `cs-issue-report` | issue agent + compat-router child agent | passed |
| `cs-issue-analyze` | issue agent + compat-router child agent | passed |
| `cs-issue-fix` | issue agent + compat-router child agent | passed |
| `cs-code-review` | dedicated code-review agent + issue agent passed with `subagent+ocr` | passed |

## 6. 目前发现

- 入口参数当前统一为 `argument-hint` + `--stage` / `--mode`；无参数路径均有“扫描仓库事实并恢复状态机”的默认行为。
- `cs-feat` / `cs-epic` 文档已表达：只在 design / roadmap gate 等用户确认；确认后生成 goal 包并优先派发可见 Goal driver，失败时打印 `/goal`。
- compat-router 报告中提到 “`cs-docs` / `cs-epic` 可能未注册” 是隔离 agent 运行时清单限制；当前主会话 skills 清单已经包含 `codestable:cs-docs` 和 `codestable:cs-epic`。
- compat-router 对 Goal driver fallback 的疑问已复核：`cs-feat` 和 `cs-epic` 的 goal protocol / command template 均生成可粘贴 `/goal` 指令。
- refactor 子 reviewer `ea5828ac-632f-4f5b-be84-ad5b999defb9` 返回 Blocking/Important：共享隔离 repo 中 refactor 产物被并发 agent 覆盖，不能算通过。已用专用 clean worktree `/Users/wyattfang/.paseo/worktrees/3g3wtzhu/codestable-refactor-clean` 重跑并通过：独立 reviewer passed、commit gate passed、`pytest -q` 5 passed。
- issue agent 暴露隔离 repo 骨架缺 `.codestable/tools/codestable-worktree-gate.py` 和 `.codestable/reference/shared-conventions.md`。这是隔离 repo 构建限制，最终报告必须说明哪些 gate 是按协议人工执行，哪些 gate 被机械执行。
- epic agent 完成了两条 child feature 的长程闭环，但没有真实派发后台 goal driver，也没有真实 independent reviewer；报告已显式降级，不能作为生产 driver 可视化能力的完整证明。
- code-review agent 发现两条非阻塞建议：`report-template.md` 可补 ad-hoc/`--range` frontmatter 样例；independent-review protocol 可明确 `--from/--to` committed OCR 模式。
- feature agent 完成标准链路，但 `cs-feat-ff` 没有实际代码改动，只验证了兼容入口转入 fastforward protocol；最终结论需标为限制项。

## 7. 已跑主仓库静态验证

```text
pytest -q tests/test_skill_workflow_scenarios.py tests/test_skill_entry_simplification.py -> 53 passed
python tools/check-plugin-package.py --root . --json -> ok
git diff --check -> clean
single-md <= 300 lines check -> clean
```

## 8. 最终状态

最终结论：通过，但带限制项。

限制项：

- `cs-feat-ff` 只验证兼容入口和 fastforward protocol 读取，没有额外叠加真实代码 fastforward 改动；标准 feature 链路已完整跑通。
- `cs-epic` 的长程 goal loop 在当前 agent 中模拟推进，未真实派发后台 goal driver；reviewer 降级为 self/local-only 并已记录。
- 共享隔离 repo 并发验证会污染 diff；已用 clean refactor worktree 复测关闭 refactor Blocking。

最终命令证据：

```text
主仓库 pytest -q -> 134 passed
主仓库 python tools/check-plugin-package.py --root . --json -> ok
主仓库 git diff --check -> clean
主仓库 single-md <= 300 lines check -> clean
共享验证 repo pytest -q -> 10 passed
clean refactor worktree pytest -q -> 5 passed
clean refactor worktree codestable-worktree-gate commit -> ok
```
