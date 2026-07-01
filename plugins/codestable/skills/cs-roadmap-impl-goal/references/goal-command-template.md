# Roadmap Goal 指令模板

`cs-roadmap-impl-goal` 在完成两次用户确认、写完 goal 执行包并自查通过后，按本模板输出 fenced `/goal`。替换 `{slug}`，保留 `{feature-slug}` 运行时占位。

```text
/goal "执行 CodeStable roadmap 目录 .codestable/roadmap/{slug} 下的 goal 执行包。先读取 goal-protocol.md、goal-protocol-feature-loop.md、goal-protocol-gates.md、goal-protocol-audit.md、goal-state.yaml、goal-plan.md；这是已由用户确认 roadmap 和全部 feature design 后的 goal 模式，按 goal-plan.md 的 Gate Policy 与 goal-protocol-gates.md 的 gate 接管规则执行。按 goal-state.yaml 的 features 顺序循环处理每个 feature：读取 goal-features/{feature-slug}.md、对应 design 和 checklist，完成 cs-feat-impl，再完成 cs-code-review；如果 review 有 blocking findings，按 review-fix 修复后重跑 cs-code-review；review passed 后完成 cs-feat-qa；如果 QA failed / blocked，按 qa-fix 修复后重跑 cs-code-review 和 cs-feat-qa；QA passed 后完成 cs-feat-accept，并更新 goal-state.yaml 与 roadmap items。每个 feature 验证通过后打印 CS_ROADMAP_GOAL_FEATURE_DONE。所有 feature 完成后，按 goal-protocol-audit.md 做最终 roadmap 审计。只有当 CS_ROADMAP_GOAL_COMPLETE 出现在 transcript 中，且所有 feature 都已 review passed、QA passed 且 accept、最终审计通过、没有 CS_ROADMAP_GOAL_HANDOFF，本 goal 才算完成。"
```
