# Spec 治理工具

本文说明 `cs-onboard` 复制到 `.codestable/reference/` 的项目 runtime helper。工具从当前
`cs-onboard` skill 包运行：

```bash
python3 <cs-onboard skill dir>/tools/codestable-spec-governance.py --root . --json <command>
```

## 命令

### `route`

在 design、roadmap、requirement 或 acceptance 前选择候选长期 spec：

```bash
python3 <cs-onboard skill dir>/tools/codestable-spec-governance.py --root . --json route \
  --query "source scout query coverage before crawl"
```

JSON 输出 `selected_specs`、`excluded_specs`、`clarification_required` 和
`allowed_to_skip_requirement_delta`。

没有选中 spec 时默认进入 owner clarification；只有查询命中显式 local-skip 模式（例如纯前端
展示微调）才例外。该结果不能被当成跳过 requirement review 的授权。

### `clarify`

把 owner clarification 追加到既有 spec，不重写全文：

```bash
python3 <cs-onboard skill dir>/tools/codestable-spec-governance.py --root . --json clarify \
  --file .codestable/requirements/source-discovery.md \
  --question "Which source field is canonical?" \
  --answer "Use retrieved_at plus intent bucket." \
  --anchor RQ-2
```

相同 question/answer 可幂等重跑。

### `create-delta`

创建 feature-local requirement delta，不直接修改长期 requirement：

```bash
python3 <cs-onboard skill dir>/tools/codestable-spec-governance.py --root . --json create-delta \
  --unit .codestable/features/YYYY-MM-DD-source-query-coverage \
  --requirement source-discovery \
  --added "The system records query intent coverage before crawl." \
  --scenario "source scout records coverage gap" \
  --owner-decision approved
```

文件路径为 `{unit}/{slug}-req-delta.md`。

### `apply-delta`

把已批准 delta 机械写入目标 requirement 的 change log：

```bash
python3 <cs-onboard skill dir>/tools/codestable-spec-governance.py --root . --json apply-delta \
  --delta .codestable/features/YYYY-MM-DD-source-query-coverage/source-query-coverage-req-delta.md \
  --target .codestable/requirements/source-discovery.md
```

未批准 delta 返回 `delta_not_approved`。

### `inventory`

把现有 spec 分类为 `current-trusted`、`current-unreviewed`、`drift-suspected`、
`historical`、`superseded` 或 `orphaned`：

```bash
python3 <cs-onboard skill dir>/tools/codestable-spec-governance.py --root . --json inventory
```

旧 spec 即使为 `status: current`，只要没有显式 `owner_review_state`，仍归为
`current-unreviewed`，不能视为 trusted。

inventory 需要 review 或交给 owner 时，写人读 rehabilitation artifact：

```bash
python3 <cs-onboard skill dir>/tools/codestable-spec-governance.py --root . --json inventory \
  --output .codestable/audits/YYYY-MM-DD-spec-governance/inventory.md
```

artifact 列出分类计数、每个 spec item，以及 `current-unreviewed` / `drift-suspected`
的 owner follow-up。同一状态重跑不会重写文件。

### `analyze`

运行只读 acceptance/design 一致性检查：

```bash
python3 <cs-onboard skill dir>/tools/codestable-spec-governance.py --root . --json analyze \
  --unit .codestable/features/YYYY-MM-DD-source-query-coverage
```

缺 approved req delta 的 capability-boundary 变更、缺 delta 证据的 dirty requirement
重写都会被阻塞；`drift-suspected` spec 交给 owner 裁决。

## 边界

该工具是确定性的，不决定产品意图、不合并 spec、不重写旧 requirement。需要人类决策时，
先按 `approval-conventions.md` 写 approval report，再通过 clarification 或 approved delta
落实；context packet 只能作为证据，不能代替审批表面。
