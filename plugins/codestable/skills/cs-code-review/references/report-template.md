# cs-code-review 报告模板

报告落在来源流程的 spec 目录，文件名 `{slug}-review.md`；feature 来源即 `.codestable/features/{feature}/{slug}-review.md`，issue/refactor 等放各自流程目录。

下面以 feature 来源为例，frontmatter 的 `doc_type` 与身份字段按来源替换（身份字段沿用该来源 spec 产物的字段名）：

| 来源 | `doc_type` | 身份字段 |
|---|---|---|
| feature / feature-ff | `feature-review` | `feature: YYYY-MM-DD-slug` |
| issue | `issue-review` | `issue: YYYY-MM-DD-slug` |
| refactor / refactor-ff | `refactor-review` | `refactor: YYYY-MM-DD-slug` |

`status` / `reviewed` / `round` 各来源通用。`reviewer` 是 gate 锚点字段，按本轮实际启动的独立 Task agent reviewer / OCR 组合写：

| 值 | 含义 |
|---|---|
| `subagent+ocr` | Task agent reviewer（Paseo subagent 或原生 Codex/Claude Task/Agent）+ ocr CLI 均已完成并合并 |
| `subagent` | 仅 Task agent reviewer 完成 |
| `ocr` | 仅 ocr CLI 完成 |
| `self` | 仅主 agent 本地 review |

下游质量 gate 默认要求 `reviewer: subagent` 或 `subagent+ocr`；`ocr` 和 `self` 需配 `CODESTABLE_ALLOW_SELF_REVIEW_FALLBACK=1` 才放行。`status: passed` 时必填 `reviewer`。

```markdown
---
doc_type: feature-review
feature: YYYY-MM-DD-slug
status: passed|changes-requested|blocked
reviewer: subagent+ocr|subagent|ocr|self
reviewed: YYYY-MM-DD
round: 1
---

# {slug} 代码审查报告

## 1. Scope And Inputs

- Design: {path}
- Checklist: {path}
- Evidence pack: {path / none}
- Gate results: {path / none}
- DoD results: {path / none}
- Implementation evidence: {实现汇报 / 对话 / 文件}
- Diff basis: {git status / git diff 摘要}
- Baseline dirty files: {none / 列表 + 归因}

### Independent Review

- Detection: {主 agent 自检结果——Paseo subagent / 原生 Codex/Claude Task/Agent / ocr CLI 各是否可用}
- 环节 A 独立隔离 Task agent: {paseo|native-agent|local-only} + {not-available|pending|completed|failed|blocked|skipped-by-user}
- 环节 B OCR CLI: not-available|completed|failed|skipped-scope-ambiguous|skipped-by-user
- OCR severity mapping: High→blocking/important, Medium→nit/suggestion, Low→discarded
- Merge policy: {各环节结果已逐条本地核验后合并 / 未启用原因 / pending 时不得定稿}
- Gate effect: {none / blocks final verdict until started lanes complete / user-approved downgrade}

## 2. Diff Summary

- 新增：{文件列表}
- 修改：{文件列表}
- 删除：{文件列表}
- 未跟踪 / staged：{文件列表}
- 风险热点：{跨模块 / 权限 / 数据 / 并发 / UI / API / none}

## 3. Adversarial Pass

- 假设的生产 bug：{一句话描述最可能失败的方向}
- 主动攻击过的反例：{design 不一致 / 边界值 / 错误路径 / 状态转换 / 并发时序 / 权限数据隔离 / 持久化回滚 / 测试假阳性}
- 结果：{升级为 findings 的项 / 留给 residual risk 或 QA focus 的项 / none}

## 4. Findings

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

## 5. Test And QA Focus

- QA 必须重点复核：{场景 / 命令 / 手工验证}
- Evidence pack residual risks / gate warnings：{已解释 / 交给 QA 的项}
- 建议新增或加强的测试：{unit / integration / e2e / function / none}
- 不能靠 review 完全确认的点：{列表}

## 6. Residual Risk

- {风险 + QA / acceptance 如何处理；没有写 none}

## 7. Verdict

- Status: passed|changes-requested|blocked
- Next: 按「进入来源」表的通过后去向（feature→`cs-feat` QA 阶段，其余→各自验收/提交） | 来源实现技能 review-fix | 等独立 Task agent reviewer 完成 / 用户确认降级后重跑本审查 | 补齐输入后重跑本审查
```

没有某类 finding 时写 `none`，不要删除章节；下一轮复审要能对比。
