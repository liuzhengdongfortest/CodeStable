# Goal Final Audit Protocol

## 1. 启动

所有 feature accepted 后打印：

```text
CS_ROADMAP_GOAL_AUDIT_START
Roadmap: {roadmap-slug}
Features to verify: <数量>
Commands to re-run: <去重命令列表>
```

读取：

- roadmap 主文档
- items.yaml
- goal-plan.md
- goal-state.yaml
- goal-features/*.md
- 每个 feature 的 design / checklist / review / QA / acceptance / evidence pack / gate results
- 每个 evidence pack 的 provider signals、Residual Risks、E/C/H 相关记录

## 2. 核验

先运行机器一致性 gate：

```bash
python3 .codestable/tools/codestable-goal-consistency-gate.py --roadmap {roadmap-path}
```

失败时不得打印完成标记；按 blocking 项补齐证据或回退状态后重跑。

必须确认：

- 每个 roadmap item 都是 `done`，或有理由 `dropped`。
- 每个 feature acceptance `doc_type=feature-acceptance` 且 `status=passed`。
- 每个 review `status=passed`，没有 unresolved blocking。
- 每个 QA `status=passed`，没有 unresolved failed / blocked。
- checklist steps 全 `done`，checks 全 `passed`。
- residual risk 没有隐藏核心验收缺口。
- provider unavailable 有 fallback reason，provider warning 已被 review / QA / audit 解释。
- 核心完成判断不能只靠 H-only evidence；H-only core checks 非空时必须 handoff 或记录用户显式接受。
- architecture / requirement / roadmap 回写已处理或明确不适用。

## 3. 最终聚合命令

按 goal-plan 执行 final aggregate commands。功能性核心命令不能因耗时跳过。外部网络、凭证、设备不可用时，判断是否属于核心验收路径；核心不可验证则 blocked。

非功能性 roadmap 可用静态 / 一致性 / schema / 文档校验替代，但必须写明理由。

## 4. 工作区与清洁度

检查：

- tracked / staged / unstaged / untracked
- 调试输出
- 临时 TODO / FIXME / XXX
- 注释掉代码
- 同名工具 shim
- 临时 runner、临时下载包、`__pycache__`

未解释命中会阻塞最终完成。

## 5. 审计报告

写 `{roadmap-path}/goal-audit.md`：

```markdown
---
doc_type: roadmap-goal-audit
roadmap: {roadmap-slug}
status: passed|blocked
audited: YYYY-MM-DD
round: 1
---

# {roadmap-slug} Goal 最终审计

## 1. Scope
## 2. Roadmap State
## 3. Final Aggregate Commands
## 4. Core Acceptance Paths
## 5. Deliverables And Writebacks
## 6. QA Residual Risk Review
## 7. Provider And E/C/H Evidence Summary
## 8. Workspace And Cleanliness
## 9. Verdict
```

同时写 `{roadmap-path}/goal-evidence-summary.md` 或在 goal-audit 第 7 节等价内嵌：

- feature evidence packs
- provider unavailable / warnings
- final aggregate commands
- E/C/H summary
- H-only core checks

## 6. 完成与学习反思

无缺口时打印：

```text
CS_ROADMAP_GOAL_AUDIT_COMPLETE
CS_ROADMAP_GOAL_LEARNING_REVIEW
CS_ROADMAP_GOAL_COMPLETE
```

learning reflection 只筛选候选，不自动写 `.codestable/compound/`；需要用户确认后再运行 `cs-keep`。
