# CodeStable Context 与 Finish 工具

本文件会由 `cs-onboard` 复制到 `.codestable/reference/tools-context.md`。它补充
`tools.md` 中的 context、finish、inbox、commit 和 backlog 工具说明。

## 1. build-context-packet.py

生成可持久保存的 context packet，供下一阶段 agent、reviewer、人类 reviewer、owner 或
learner 使用，避免复制完整聊天历史。

```bash
python3 .codestable/tools/build-context-packet.py --root . --unit .codestable/features/YYYY-MM-DD-{slug} --audience handoff --output /tmp/codestable-handoff.md \
  --decided "Use staged review packets" \
  --rejected "Do not adopt full Team pipeline" \
  --risk "Verification can be skipped if no gate enforces evidence" \
  --remaining "Run maintainer verifier after push" \
  --evidence "uvx --with pytest pytest -> passed"
```

Audiences：

- `handoff`：下一阶段 agent / reviewer 上下文，固定六段结构。
- `human-reviewer`：供人类 review 的完整上下文报告。
- `owner-decision` / `owner-judgment`：决策辅助上下文，永远不替代
  `approval-report.md`。
- `learner`：learning report 上下文。
- `interviewee`：真实 interview / retrospective 大纲。

owner approval checkpoint 必须先按 `approval-conventions.md` 写该 unit 的
`approval-report.md`。如果 context packet 有用，把它作为证据附加或引用，不要创建
`*-owner-context.md` 作为审批表面。

Handoff 输出章节：

- `Decided`
- `Rejected`
- `Risks`
- `Files`
- `Remaining`
- `Evidence`

非 handoff audience 输出 `Decision Brief`、`Working Context` 和 `Evidence Appendix`。
把 `.codestable/attention.md` 映射到工具支持的 `--language` 值（`en` 或 `zh`）。
当项目报告语言策略不被工具支持时，分享前把生成的 packet 改写成项目语言。secret-like
路径和 token 会被脱敏。

## 2. check-context-sufficiency.py

检查生成的 handoff / audience 报告是否有可识别结构、secret-like 文本、具体文件和证据。

```bash
python3 .codestable/tools/check-context-sufficiency.py --file /tmp/codestable-human-review.md --strict --json
```

派发 human reviewer / Task agent reviewer 前，或把 context packet 作为 approval report
证据分享前使用。

## 3. codestable-finish-worktree.py

merge 前运行执行 worktree 的 finish gate。它生成 learning report、context sufficiency
check、merge readiness JSON 和本地 inbox item。它不会 merge、rebase、commit、删除
worktree，也不会替代 merge approval。

```bash
python3 .codestable/tools/codestable-finish-worktree.py --root . --unit .codestable/features/YYYY-MM-DD-{slug} --json \
  --validation "uv run pytest -> passed" \
  --validation "CLI smoke -> passed"
```

生成文件：

- `{slug}-learning-report.md`
- `{slug}-learning-context-check.json`
- `{slug}-merge-readiness.json`
- `$(git rev-parse --git-common-dir)/codestable/worktree-inbox/{branch}.json`

关键规则：

- 只在 linked execution worktree 中运行。
- 除可刷新 finish-gate 产物外，保持 worktree 干净。
- 必须有 implementation review evidence。
- learning report 的 `covered_head` 之后 branch HEAD 变化时必须重跑。
- 缺 validation、缺 review 或存在 blocking backlog 时失败。

## 4. codestable-worktree-inbox.py

读取 Git common-dir 中跨 branch / worktree 的 merge 提醒。

```bash
python3 .codestable/tools/codestable-worktree-inbox.py --root . --json
python3 .codestable/tools/codestable-worktree-inbox.py --root . --snooze codex_slug --until 2026-06-12T00:00:00Z --json
python3 .codestable/tools/codestable-worktree-inbox.py --root . --abandon codex_slug --reason "owner canceled" --json
```

状态：`ready-to-merge`、`stale-report`、`merged`、`blocked`、`abandoned`。
snoozed item 仍可见，但在到期或变 stale 前不会提示 merge。

## 5. plan-commits.py

只读 commit planner。它按逻辑 bucket 对 dirty paths 分组，并标记 migration doc-sync、
runbook doc-sync、tracked ignored files、large files 和 live writers。它不会 stage 或 commit。

```bash
python3 .codestable/tools/plan-commits.py --root . --json
```

常见 buckets：`code`、`tests`、`docs`、`migrations`、`database_docs`、`data`、
`logs`、`codestable`、`installed_skill`、`unknown`。

## 6. codestable-backlog.py

最终汇报前扫描 `.codestable/` 中的人审与 follow-up backlog。

```bash
python3 .codestable/tools/codestable-backlog.py --root . --json
```

它报告 `needs-human-review`、`Human review required`、显式 `Follow-up:` 行、
`## Follow-Ups` bullet、accepted / deferred P2 和 `attention.md` candidates。它跳过
`.codestable/reference/` 和 `*-review-packet.md`，忽略已解决 follow-up 记录，并把
canceled lifecycle 文件视为历史。
