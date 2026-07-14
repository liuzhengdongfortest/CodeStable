---
doc_type: issue-analysis
issue: 2026-07-13-risk-tiered-short-flow
status: confirmed
root_cause_type: logic
related: [risk-tiered-short-flow-report.md]
tags: [workflow-routing, feature-lanes, review-policy]
github_issue: 43
---

# 风险分级与短流程根因分析

## 1. 问题定位

| 关键位置 | 说明 |
|---|---|
| `plugins/codestable/skills/cs/SKILL.md:76` | 根路由只区分 feature / issue / refactor 等工作类型，不判断 feature 的规模、边界清晰度和风险。 |
| `plugins/codestable/skills/cs-feat/SKILL.md:100` | 只有显式 `wantsFastForward(intent)` 才尝试短流程；未传 flag 时，缺 design 一律在第 102 行进入 Design。 |
| `plugins/codestable/skills/cs-feat/SKILL.md:109` | design approved 后只要没有 goal state 就无条件进入 GoalPackage。 |
| `plugins/codestable/skills/cs-onboard/tools/codestable-workflow-next.py:477` | 可执行恢复工具同样把“approved design + no goal state”固定解释为缺 goal package。 |
| `plugins/codestable/skills/cs-feat/references/fastforward/protocol.md:3` | 短流程协议明确说小功能应直接实现，和主入口只能显式 opt-in 的可达性矛盾。 |
| `plugins/codestable/skills/cs-feat/references/design-review/protocol.md:46` | 所有 design 修订都强制启动新一轮独立 reviewer，没有区分契约变化与文字/映射修正。 |
| `plugins/codestable/skills/cs-code-review/SKILL.md:128` | 任意 diff 变化都要求重新 review；第 220-225 行又要求 blocking 修复后完整重跑，没有 focused closure。 |
| `plugins/codestable/skills/cs-feat/references/acceptance/protocol.md:49` | 已有 accept-inline verification 能力，但 code-review 默认去向仍固定为独立 QA，普通单 feature 无法自然使用。 |
| `tests/test_skill_workflow_scenarios.py:546` | 场景测试把“单 feature 默认 goal package/driver”固化为正确行为，缺少小型明确任务的短流程 oracle。 |

## 2. 失败路径还原

**期望路径**：用户提出明确局部功能 → `cs` 判定为 feature → `cs-feat` 根据风险和边界自动判为 Quick → 实现与目标验证 → 一次独立代码审查 → 简短 ff-note 闭环。

**实际路径**：用户提出明确局部功能 → `cs` 只判定为 feature → 没有显式 `--mode fastforward` → `cs-feat` 因 design 缺失进入 Design → 每次 design 修订都独立重审 → design approved 后强制 GoalPackage/driver → implementation → 任意 review-fix 都完整复审 → QA → 九节 acceptance 与 final audit。

**第一分叉点**：`plugins/codestable/skills/cs-feat/SKILL.md:100` — 短流程选择依赖用户事先知道 flag，而不是依赖任务事实。

**第二分叉点**：`plugins/codestable/skills/cs-feat/SKILL.md:109` 与 `plugins/codestable/skills/cs-onboard/tools/codestable-workflow-next.py:477` — 标准 feature 和长程 Goal 被绑定成同一条路径。

## 3. 根因

**根因类型**：逻辑错误。

**根因描述**：当前模型只有“工作类型”和“显式 fastforward”两个维度，没有独立的执行风险分级。所有未显式选择 fastforward 的 feature 都落入同一标准分支，而该分支又把 goal package、独立 QA 和完整 acceptance 作为默认后继。review 规则只看“文件是否变化”，不看变化是否改变行为或契约，因此轻微修正也会启动完整新轮次。

**是否有多个根因**：是。

1. 主因：Quick 是隐藏的 opt-in 例外，不是基于仓库事实的默认分类结果。
2. 次因：Standard 与 Goal 没有分离，Goal 无条件接管 approved design。
3. 放大器：design/code review 缺少 focused closure，任何变化都重启完整独立审查。
4. 防回归缺口：测试只证明长程 goal 路径存在，没有证明小任务默认不会进入它，也没有覆盖用户反馈触发重新分级。

## 4. 影响面

- **影响范围**：所有未显式传 `--mode fastforward` 的单 feature；尤其影响需求清楚、复用既有接口、改动局部且已有目标测试的日常任务。
- **潜在受害模块**：`cs` 路由说明、`cs-feat` 状态机、workflow-next 恢复工具、design/code review、README/skill catalog 和 workflow scenario tests。`cs-epic` 的长程 goal 路径应保持不变。
- **数据完整性风险**：无业务数据风险；但 lane 迁移若处理不当会让已有 feature 恢复到错误阶段。兼容规则应为：已有 `goal-state.yaml` 始终按 Goal 恢复；epic child 始终交回 Epic；无 goal state 的 standalone approved design 才按 Standard 恢复。
- **严重程度复核**：维持 P1。功能可完成且有显式 fastforward 绕过，但默认路径稳定制造高额时间和 agent 成本。

## 5. 修复方案

### 方案 A：只把 Quick 改为自动判定

- **做什么**：在 `cs-feat` 的 Design 分支前增加 `quickEligible`，满足“需求明确、局部、复用已有契约、有目标验证”时自动进入现有 FastForward；增加用户抱怨流程过重时重新判定。
- **优点**：改动小，直接解决 #43 的主要案例，复用成熟 fastforward 协议。
- **缺点 / 风险**：Standard 仍无条件生成 goal package；重复 review、QA/acceptance 膨胀仍存在，问题只关闭一部分。
- **影响面**：`cs`、`cs-feat`、fastforward 文档和路由测试。

### 方案 B：建立 Quick / Standard / Goal 三条 lane

- **做什么**：
  - Quick 自动选择：需求明确、局部、复用既有契约、已有目标验证；产物仅 ff-note，保留首次独立代码审查。
  - Standard：存在新契约或跨模块决策，但适合当前 run 完成；走 design/review/implementation/code review/accept-inline，不默认生成 goal package 或独立 QA 报告。
  - Goal：仅在用户明确要求长程自主执行、显式 `--stage goal-package`、已有 goal state 或 Epic 批量上下文时进入；保留完整 QA/acceptance。
  - design/code review 首轮独立审查保留；只有行为、公开契约、安全、数据、并发或架构发生实质变化才完整复审。test/docs/type/metadata/nit-only 修正由主 agent 做 focused closure 并记录 diff 与目标验证；无法确定分类时 fail-closed 完整复审。
  - 用户说“这是小改动 / 流程太重 / 文档比代码多”时必须暂停并重新分类，若风险条件阻止降级则说明具体原因。
- **优点**：同时修复入口失配、Goal 默认化和重复审查三个根因；lane 按风险而非模型名称判断；现有 accept-inline 能力可直接复用。
- **缺点 / 风险**：要同步 skill 契约、workflow-next、设计元数据、README 和场景测试；需明确旧 artifact 的恢复兼容。
- **影响面**：`cs`、`cs-feat`、`cs-code-review`、workflow-next、相关 reference、README/SKILL_CATALOG 和测试。

### 方案 C：引入可配置风险分数

- **做什么**：按文件数、模块数、契约、安全、迁移、验证等维度计分，再用阈值选择 lane；项目可配置阈值。
- **优点**：判定可量化、可扩展，适合大型组织差异化治理。
- **缺点 / 风险**：为当前问题引入新的配置和伪精度；模型容易围绕分数做形式化判断，维护成本高于收益。
- **影响面**：除方案 B 的文件外，还需要 schema、配置文档和迁移逻辑。

### 推荐方案

**推荐方案 B**。它用少量明确的风险条件把三种执行语义分开，复用现有 fastforward、accept-inline 和 goal 协议，能关闭 #43 的全部主要失败点；同时保留 Epic/显式 Goal 的严格流程，不以降低质量门槛换速度。

用户于 2026-07-13 明确确认方案 B。
