---
doc_type: issue-fix
issue: cs-skills-release-contract-hardening
status: confirmed
path: standard
fix_date: 2026-07-15
related: [cs-skills-release-contract-hardening-analysis.md]
tags: [skills, workflow, spec, release]
---

# CS Skills 发布契约加固修复记录

## 1. 根因摘要

安全规则只停留在局部 prose，没有同时落入 typed state、resume input、runtime gate、持久证据和行为测试。结果是在跨 session、Epic DAG、Goal driver、独立 reviewer 不可用及发布同步场景下出现死锁、隐式授权、证据复用或错误恢复。

## 2. 实际采用方案

1. 拆分 design admission 与 implementation admission：Epic child design 读取完整 DAG，implementation 仍严格要求依赖 `done`。
2. Goal acceptance 与 Epic scoped commit 使用两个独立、可机械核验的命名 `ApprovalRef`；final gate 在完成前复核。
3. code-review lane 持久化 run ref、round 与 pending state；issue/refactor/docs/audit/epic/req/goal 的 checkpoint 都补 typed resume 和 fail-closed 匹配。
4. `cs-goal` 完成要求 acceptance 与 final iteration 双向引用；review/acceptance agent 不可用时 owner-stop，不静默自审。
5. Goal final gate 要求非 dropped roadmap item 与 accepted feature 一一对应，核验 canonical artifact identity，并要求 checklist 的 `steps` / `checks` 都是非空 mapping list 且状态分别为 `done` / `passed`。
6. runtime health 做 source/target 双向 drift；同步删除 target-only package assets，保留精确 legacy allowlist，并在 `.codestable` 根为 symlink 或 source 缺 `gates/`、`references/`、`codestable.gitignore` 时停止且不删除项目内容。
7. `cs-docs-neat` resolution 绑定宿主持久化的 `NeatRunRef`，旧 run 确认不得重放。
8. scope gate 把 `git status` 非零视为结构化失败；DoD/evidence loader 拒绝非法或非 mapping YAML/JSON，无 PyYAML 时严格 fail-closed，不用宽松 parser 猜测状态。
9. Epic feature loop 先持久化 accepted 状态与新 index，再机械复核两份 ApprovalRef，最后 scoped-commit 全部状态；clean check 位于所有状态更新之后。
10. 发布 gate 覆盖完整 tests、package、runtime sync check、doctor 与 diff check。owner 已删除 `AGENTS.md` 的全仓 Markdown 300 行规则；历史 skill-entry 自身的 skill 范围约束保持不变。

## 3. 改动范围

- 主 skill 与协议：`cs-audit`、`cs-code-review`、`cs-docs*`、`cs-epic`、`cs-feat`、`cs-goal`、`cs-issue`、`cs-note`、`cs-onboard`、`cs-refactor`、`cs-req`。
- 共享/runtime：`cs-onboard/references/`、项目 `.codestable/reference/`、workflow-next、goal consistency gate、doctor/runtime sync helper。
- 发布与兼容：eval release protocol、deprecated agent prompts、onboard feedback skeleton、历史 refactor review。
- 测试：workflow/runtime/goal gate/contract/scenario/entry/package 相关套件。

## 4. 验证结果

- 最终独立 Sol closure：blocking / important / minor 均为 `0`；两个无 PyYAML 原复现均 exit 1、结构化 blocked、无 traceback。
- 全量：`585 passed, 1 skipped`；skip 是需显式环境开关的真实 skills CLI E2E。
- package checker：`ok: true`。
- runtime sync check：`ok: true`，`drifted_paths: []`。
- doctor：`ok: true`，`status: implementation-active`，无 findings/backlog。
- `git diff --check`：通过。

## 5. 遗留事项

- 发布版本号、CHANGELOG、commit 与 push 尚未执行；需要 owner 单独授权。
- 未发现需要延期接受的 contract residual risk。
