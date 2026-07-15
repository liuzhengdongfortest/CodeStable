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
- approval-report.md 的 `goal-acceptance` / `goal-commits` 命名决策
- goal-features/*.md
- 非 dropped roadmap items 与 goal-state accepted features 的一一对应关系
- 每个 feature canonical 目录内的 design / checklist / review / QA / acceptance / evidence pack / gate results
- 每个 evidence pack 的 provider signals、Residual Risks、E/C/H 相关记录

## 2. 核验

先运行机器一致性 gate：

```bash
python3 <cs-onboard skill 目录>/tools/codestable-goal-consistency-gate.py --roadmap {roadmap-path}
```

失败时不得打印完成标记；按 blocking 项补齐证据或回退状态后重跑。

```haskell
data AuditOutcome = AuditComplete | RepairAudit | AuditHandoff GoalHandoffReason

auditPassed :: AuditEvidence -> Bool
auditPassed a = and
  [ allItemsTerminal a             -- done | dropped(reason)
  , roadmapFeatureBijection a      -- item feature 指针与 accepted feature 无缺失、额外或重复
  , canonicalFeatureEvidence a     -- 路径、doc_type、feature identity 均归属当前 feature
  , goalAuthorizationsValid a      -- 同 roadmap canonical approval-report 的两份命名授权
  , allFeatureArtifactsPassed a    -- review + QA + acceptance
  , allChecklistPassed a           -- steps done + checks passed
  , noCoreResidualRisk a
  , providerRisksExplained a
  , noUnapprovedHOnlyCoreCheck a
  , writebacksCompleteOrNA a
  , consistencyGatePassed a
  ]

auditOutcome :: AuditEvidence -> AuditOutcome
auditOutcome a
  | auditPassed a                        = AuditComplete
  | not (noUnapprovedHOnlyCoreCheck a)   = AuditHandoff UnapprovedHOnlyCoreCheck
  | coreEnvironmentMissing a             = AuditHandoff CoreEvidenceUnavailable
  | corePathUnverified a                 = AuditHandoff CorePathUnverified
  | sameAuditFailureCount a >= 3         = AuditHandoff RepeatedFailure
  | otherwise                            = RepairAudit
```

## 3. 最终聚合命令

按 goal-plan 执行 final aggregate commands。功能性核心命令不能因耗时跳过。外部网络、凭证、设备不可用时，判断是否属于核心验收路径；核心不可验证则 `AuditHandoff CoreEvidenceUnavailable`。

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
