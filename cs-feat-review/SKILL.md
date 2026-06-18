---
name: cs-feat-review
description: feature 流程阶段 2.5——实现完成后的本地代码审查 gate。对照 design / checklist / 实现汇报和当前 git diff 做只读 code review，产出 {slug}-review.md；可选检测 Paseo / 外部 agent 并用独立 audit subagent 辅助审查，但最终由本 skill 合并定级。有 blocking findings 时回到 cs-feat-impl 的 review-fix，通过后进入 cs-feat-qa，不直接验收。触发：用户说"做代码审查"、"review 这个 feature"、"实现完了先 code review"、"跑 cs-feat-review"。
---

# cs-feat-review

## 启动必读

开始任何判断或动作前，先读取 `.codestable/attention.md`；缺失则视为骨架不完整，提示先补齐或运行 `cs-onboard`，不要回退到外部 AI 入口文件。

本阶段是实现完成后、QA 前的独立代码审查 gate。它只读代码和产物，只写 `{slug}-review.md`，不直接修代码、不更新 checklist、不改 design、不替代 QA 或 acceptance。

审查目标不是追求完美代码，而是确认本次改动没有降低系统代码健康，并且确实朝 design 的目标前进。能自动格式化或 lint 的问题不要手工阻塞；会影响正确性、维护性、安全、性能、可测试性、需求满足或后续验收可信度的问题必须指出。

> 共享路径与命名约定看 `.codestable/reference/shared-conventions.md` 第 0 节。

---

## 输入

进入 review 前必须读取：

- `.codestable/attention.md`
- `{slug}-design.md`
- `{slug}-checklist.yaml`
- 实现完成汇报 / 最近实现记录（如果在对话里，按对话事实引用；如果已落文件，读文件）
- `git status --short`
- `git diff`（有 staged diff 时也读 `git diff --cached`）
- diff 涉及的人写代码文件和相邻关键调用点
- design 第 4 节指向的 architecture / requirement / roadmap 相关文档（只读，判断改动是否会影响归并）
- independent reviewer 输出（如果本轮启用了 Paseo 或其他外部 reviewer）

如果工作区有 feature 外的既有 dirty 文件，先记录为 baseline/无关变更；审查结论只针对本 feature 可归因的改动。无法区分归因时写成 `residual-risk`，不要把不确定当通过。

---

## 启动检查

1. `{slug}-design.md` 存在，frontmatter `doc_type=feature-design`、`status=approved`、`feature` 与目录一致。
2. `{slug}-checklist.yaml` 存在，`steps` 全部 `done`，`checks` 仍处于验收前状态（通常是 `pending`）。
3. 当前 diff 能看到本 feature 的实现改动；如果完全没有代码或产物改动，退回 `cs-feat-impl`。
4. 如果已有 `{slug}-review.md`：
   - `status: passed` 且 diff 未变化：提示可进入 `cs-feat-qa`。
   - `status: changes-requested` / `blocked`：读取旧 findings，确认是否处于 review-fix 后的复审。
   - diff 已变化：重新 review，并在报告里记录这是第几轮。

---

## 独立 reviewer 增强项

本阶段默认由当前 agent 完成本地 review；独立 reviewer 是增强项，不是硬依赖。检测不到外部 agent、Paseo 不可用、provider 未配置或用户明确要求快速完成时，可以继续本地 review，并在报告里记录 `Independent reviewer: local-only` / `skipped-by-user`。

但一旦本轮已经启动 independent reviewer，它就成为本轮 review gate 的输入。主 agent 可以先做本地审查草稿，但不能在 independent reviewer 返回前定稿 `{slug}-review.md`、不能给出 `passed`、不能进入 `cs-feat-qa`。如果 reviewer 卡住、失败、权限阻塞或耗时过长，只能把本轮标成 `blocked` / `independent-review-pending`，然后让用户决定：继续等待、重试 reviewer，或明确降级为 local-only review。

先运行本 skill 自带检测脚本。按已加载的 `SKILL.md` 所在目录解析脚本路径，不要按业务仓库根目录猜路径：

```bash
python scripts/detect-review-agent.py --pretty
```

脚本只输出能力 JSON，不启动 agent、不改文件。

优先级：

1. **Paseo 可用**：优先用 Paseo 启动 `audit` 类 subagent 做只读独立审查。启动前先加载 / 读取 `paseo` skill 的当前说明，并遵守它的规则：读取 `~/.paseo/orchestration-preferences.json`，使用 `providers.audit`，不要硬编码 Claude 或 Codex；文件缺失时用合理默认并在报告里说明。不要无限轮询运行中的 agent；如果 reviewer 已启动但结果未返回，停止在 review gate，记录 pending/blocked，等待通知或用户决定。
2. **只有 claude / gemini / aider 等 CLI 可见**：不要自动调用。直接本地 review，除非用户显式要求使用某个 CLI。
3. **没有外部 reviewer**：本地 review。

Paseo subagent prompt 必须只给原始材料和边界，不透露本地 review 结论：

```text
你是 CodeStable feature 的独立代码审查 agent。只读，不修改文件，不更新 checklist/design。

请读取：
- .codestable/attention.md
- {design_path}
- {checklist_path}
- 当前 git status / git diff / staged diff
- diff 涉及的人写代码和相邻关键调用点

按 cs-feat-review 的严重度语义输出：blocking / important / nit / suggestion / learning / praise / residual-risk。
每条 finding 必须有 file:line 或仓库事实证据、影响、建议修复边界。
额外输出 Test And QA Focus：QA 必须重点复核的场景、建议新增或加强的测试、review 无法确认的点。
不要写 {slug}-review.md；只把审查结果回传给主 agent。
```

主 agent 仍是最终审查责任方：必须逐条核验 independent reviewer 的 finding，去重、定级、合并进 `{slug}-review.md`。未经本地仓库事实核验的外部结论只能写 `residual-risk` 或忽略，不能直接升级成 `blocking`。

## 审查流程

### 1. 上下文与范围

- 用 design 第 1/2/3 节确认目标、明确不做、关键决策、验收场景。
- 用 checklist steps 确认实现声称已经完成的范围。
- 用 `git status` / `git diff` 列出真实改动文件，标出新增、修改、删除、未跟踪、staged。
- 判断 diff 大小和风险：跨模块、跨边界、数据迁移、权限/安全、并发/异步、用户可见 UI、公共 API、测试缺口。

### 2. 独立审查合并

- 记录 detection 结果：`paseo-subagent` / `local-review-with-agent-cli-available` / `local-review`。
- 如果没有启动 independent reviewer：记录 `not-available` / `skipped-by-user` / `local-only`，本地 review 可以定稿。
- 如果启动了 Paseo subagent：先做本地 review 草稿，但最终 verdict 必须等 independent reviewer 返回。不要轮询运行中的 notify-on-finish agent；等通知、用户带回结果或下一轮继续。
- 如果 independent reviewer 返回：逐条做本地事实核验，能复现 / 有证据才合并；证据不足只写 residual risk 或不采纳。
- 如果 independent reviewer 失败、权限阻塞、超时或仍在运行：不要默默降级；报告 `status: blocked`，在 Independent Review 写 `pending|failed|blocked` 和 agent id / 原因，下一步交给用户决定继续等、重试或降级 local-only。
- 报告里保留来源：哪些 finding 来自 independent reviewer，哪些是本地 review 发现。

### 3. 整体审查

先看整体，再看行级细节：

- design fit：实现是否满足 design，又没有偷偷扩范围。
- 架构 fit：新代码是否放在正确层次，是否绕过既有抽象、引入反向依赖或过度耦合。
- 复杂度：是否为当前问题引入过度泛化、补丁分支、参数膨胀、大函数/大类继续膨胀。
- 测试策略：现有测试和新增测试是否能证明关键场景；测试是否会在代码坏掉时真实失败。
- 风险面：错误处理、数据校验、安全边界、权限、并发、幂等、性能、可观测性、回滚/卸载。
- 文档/归并影响：是否出现 acceptance 必须回写的 architecture / requirement / roadmap 变更。

### 4. 行级审查

对人写代码逐文件审查，至少覆盖：

- 逻辑正确性：边界值、空值、异常路径、状态转换、时序问题、off-by-one。
- 错误处理：错误语义是否明确，是否吞错，是否把恢复逻辑和业务逻辑搅在一起。
- 数据与安全：输入验证、注入风险、敏感信息、权限检查、跨租户/跨用户隔离。
- 性能与资源：重复 IO、N+1、无界循环/缓存、内存泄漏、未释放资源。
- 并发/异步：竞态、死锁、取消、重入、重复提交、幂等。
- 可维护性：命名是否沿用 design 术语，是否复用已有 helper，是否新增重复逻辑。
- 清洁度：调试输出、临时 TODO/FIXME、注释掉代码、未使用 import、方案外文件。

生成代码、锁文件、大数据文件可以抽样，但报告里要说明抽样范围。人写业务代码不能跳过不看。

### 5. 结论

把发现按严重度归类，并给出明确 verdict：

- `passed`：没有 blocking；important 已修复、无重要项、或用户明确接受延后。
- `changes-requested`：有 blocking，或 important 多到会影响验收可信度。
- `blocked`：缺少关键输入、diff 归因无法判断、设计/实现状态不满足 review 前置条件，或本轮已启动 independent reviewer 但结果仍 pending / failed / blocked 且用户尚未确认降级。

---

## 严重度

- `blocking`：必须先修。会导致功能不满足 design、数据/安全/权限风险、明显 bug、验收无法可信执行、严重架构倒退、测试完全覆盖不到关键风险。
- `important`：应该修；若用户决定延后，必须在 review 报告和 acceptance residual risk 中明确记录。
- `nit`：小的清晰度或一致性建议，不阻塞。
- `suggestion`：替代实现思路，不要求本次采用。
- `learning`：知识性说明，不要求动作。
- `praise`：记录值得保留的好做法；少量即可。
- `residual-risk`：review 无法完全消除的不确定性，需要 QA / acceptance 重点复核。

不要把个人偏好升级成 blocking。blocking 必须能用仓库事实、design 契约、可靠工程原则或可复现实例支撑。

---

## 报告模板

报告路径：`.codestable/features/{feature}/{slug}-review.md`。

```markdown
---
doc_type: feature-review
feature: YYYY-MM-DD-slug
status: passed|changes-requested|blocked
reviewed: YYYY-MM-DD
round: 1
---

# {slug} 代码审查报告

## 1. Scope And Inputs

- Design: {path}
- Checklist: {path}
- Implementation evidence: {实现汇报 / 对话 / 文件}
- Diff basis: {git status / git diff 摘要}
- Baseline dirty files: {none / 列表 + 归因}

### Independent Review

- Status: not-available|skipped-by-user|local-only|pending|completed|failed|blocked
- Detection: paseo-subagent|local-review-with-agent-cli-available|local-review|skipped
- Provider / agent: {providers.audit / agent id / none}
- Raw output: {摘要 / 路径 / none}
- Merge policy: {已逐条核验 / 未启用原因 / pending 时不得定稿}
- Gate effect: {none | blocks final verdict until completed / user-approved downgrade}

## 2. Diff Summary

- 新增：{文件列表}
- 修改：{文件列表}
- 删除：{文件列表}
- 未跟踪 / staged：{文件列表}
- 风险热点：{跨模块 / 权限 / 数据 / 并发 / UI / API / none}

## 3. Findings

### blocking

- [ ] REV-001 `{file:line}` {问题}
  - Evidence: {仓库事实 / design 契约 / 失败路径}
  - Impact: {为什么阻塞 QA / acceptance}
  - Expected fix scope: {只描述问题边界，不替实现写方案}

### important

- [ ] REV-00N `{file:line}` {问题}
  - Evidence: {证据}
  - Impact: {影响}

### nit

- [ ] REV-00N `{file:line}` {建议}

### suggestion

- [ ] REV-00N {建议}

### learning

- {可复用经验或注意点}

### praise

- {值得保留的做法}

## 4. Test And QA Focus

- QA 必须重点复核：{场景 / 命令 / 手工验证}
- 建议新增或加强的测试：{unit / integration / e2e / function / none}
- 不能靠 review 完全确认的点：{列表}

## 5. Residual Risk

- {风险 + QA / acceptance 如何处理；没有写 none}

## 6. Verdict

- Status: passed|changes-requested|blocked
- Next: `cs-feat-qa` | `cs-feat-impl` review-fix | 等 independent reviewer 完成 / 用户确认降级后重跑 `cs-feat-review` | 补齐输入后重跑 `cs-feat-review`
```

没有某类 finding 时写 `none`，不要删除章节；下一轮复审要能对比。

---

## review-fix 衔接

如果有 `blocking`：

1. 报告 `status: changes-requested`。
2. 告诉用户下一步触发 `cs-feat-impl` 的 review-fix 模式。
3. review-fix 只修 blocking findings；important 是否修由用户或实现者判断，但不能顺手扩大范围。
4. review-fix 完成后必须重跑 `cs-feat-review`，不能直接进入 `cs-feat-qa` 或 `cs-feat-accept`。

如果只有 `important`：

- 默认建议先修；如果用户明确接受延后，报告里把它移入 residual risk，并允许进入 `cs-feat-qa`。

如果没有 blocking，且 important 已处理或被明确接受：

- 报告 `status: passed`。
- 告诉用户下一步是 `cs-feat-qa`。

---

## 退出条件

- [ ] 已读取 attention、design、checklist、实现证据、git status、git diff 和相关代码。
- [ ] 已确认 checklist steps 全 done；否则退回 `cs-feat-impl`。
- [ ] 已运行 independent reviewer 检测，或记录为什么跳过。
- [ ] 如果没有启动 independent reviewer，已记录 not-available / skipped-by-user / local-only 原因。
- [ ] 如果启动了 independent reviewer，已等到 completed 并逐条本地核验合并 / 驳回 findings；否则报告 `status: blocked`，没有进入 QA。
- [ ] 已做整体审查和行级审查。
- [ ] 已明确区分 blocking / important / nit / suggestion / learning / praise / residual-risk。
- [ ] 已写 `.codestable/features/{feature}/{slug}-review.md`。
- [ ] 有 blocking 时没有进入 QA / acceptance，而是指向 `cs-feat-impl` review-fix。
- [ ] 无 blocking 时明确告诉用户下一步 `cs-feat-qa`。

---

## 容易踩的坑

- 边 review 边修代码，把只读 gate 变成实现阶段。
- 只看实现汇报，不看真实 `git diff`。
- 只看测试是否通过，不判断测试是否有效。
- 把格式、命名偏好、个人写法升级成 blocking。
- 发现设计外实现却不回到 design 契约判断。
- 外部 reviewer 的结论没经本地事实核验就直接照抄成 blocking。
- 启动 independent reviewer 后结果还没回来，就把本地 review 定稿为 passed。
- independent reviewer 卡住时不问用户就默默降级成 local-only。
- blocking 修完后跳过复审，直接验收。
- review 报告没有落盘，导致 acceptance 没有可追溯输入。
