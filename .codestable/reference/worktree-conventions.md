# Worktree 与 Finish 约定

本文件由 `cs-onboard` 复制到 `.codestable/reference/worktree-conventions.md`。
需要代码编辑、执行 worktree、commit gate、finish 或 handoff context 时读取。

## 检出模式：探测 + 用户选择

一个 unit（feature / issue / refactor）的全生命周期产物——design / analysis / checklist
与代码——落在**同一条分支**上线性产出，消除合并时 `.codestable/{unit}/{slug}/` 的反复冲突。

是否用独立 worktree，在该 unit **第一次产生持久改动前**探测并交用户选择（见下节）。一经
决定：选独立 worktree 则后续全程在其中；选不切则写 `worktree-override.md`，后续全程在当前
检出。类型化分支为 `feat/{slug}` / `fix/{slug}` / `refactor/{slug}`；epic 以整个大需求为
单位，用 `epic/{slug}`（见下节 epic 特例）。

Goal 可用 `.codestable/goals/YYYY-MM-DD-{slug}` 包装；代码编辑落入子 feature / issue /
refactor 流程时，仍按对应 unit 走探测。

## 改动前 worktree 探测与选择

锚点（第一份持久产物起手）：feature=起草 design / issue=写 report / refactor=scan 起手 /
epic=planning 起手（整个 epic 问一次，子 feature 继承不再问）。brainstorm、intent 初始化
骨架不触发。

1. **先探测已隔离**：命中就绝不嵌套，直接复用当前检出继续。

   ```bash
   [ "$(git rev-parse --git-dir)" != "$(git rev-parse --git-common-dir)" ] && \
   [ -z "$(git rev-parse --show-superproject-working-tree 2>/dev/null)" ] && echo linked || echo main
   ```

   `linked` = 已在 worktree；也可读 `worktree-gate start` 的 `linked` 字段。已有
   `worktree-override.md` 按既定选择走，不再问。
2. **征求同意**（非隔离、无 override、用户未预声明偏好）：说明"接下来开始产生持久改动，是否
   切独立 worktree（`{feat|fix|refactor|epic}/{slug}`）隔离，避免规划与实现冲突"，给切 / 不切。
3. **选切→建 worktree**：优先 harness 原生工具（本项目按 CLAUDE.md 用 paseo 工具；通用回退
   才 `git worktree add -b`，先 `git check-ignore .codestable` 确认忽略状态），`cd` 进入，跑
   start gate 记 baseline。
4. **选不切→写 override**：在 unit 目录写 `worktree-override.md`（reason=用户主动选非
   worktree 模式 / scope / approval），后续不再问。

**epic 特例**：epic 以整个大需求为单位，在 planning 起草前只问一次，子 feature 继承同一
worktree 不再问。`roadmap` 不在 gate 的实现单元根，探测直接用第 1 步的 git 命令判断、原生工具
创建，**不跑 unit start gate**；分支 `epic/{slug}`，override 落 `.codestable/roadmap/{slug}/worktree-override.md`。子 feature 在此 worktree 内跑各自的 start gate（gate 见 linked 即放行）。

## 最短正确用法

1. Start：`cs {goal}`，路由到 feature / issue / refactor / explore / goal。
2. 改动前：按"改动前 worktree 探测与选择"确认检出（切独立 worktree 或写 override），运行 start gate。
3. Review：完成的代码批次经过独立 review。
4. Commit：运行验证、commit planner 和 commit gate。
5. Finish：运行 finish gate，记录 merge readiness。
6. 固化 finish 产物：提交生成的 finish report 文件。
7. Merge：只能在 owner 明确批准后执行。

## 共享规划表面

worktree 不能读取兄弟 worktree 尚未合并的代码 diff。共享意图只通过这些位置流转：

- `.codestable/goals/**`
- `.codestable/features/**`、`.codestable/issues/**`、`.codestable/refactors/**`
- `.codestable/roadmap/**`
- `.codestable/compound/**`
- owner-designated temporary coordination docs

如果执行 worktree 发现计划必须改变，要把计划变化同步回共享规划表面，或停下来交给 owner 判断。

## 建执行 Worktree 时的落地清单

上节选切后，建 worktree 前先确认：

1. 已按上节探测确认当前不在目标 worktree 内（不嵌套）。
2. spec / checklist / analysis / goal state 可读。
3. worktree 路径、分支、范围和兄弟 worktree 边界清楚。
4. worktree 从目标 baseline 创建；除非明确采用 stacked development，不从另一个 feature
   worktree 创建。

实现前运行 start gate：

```bash
python3 .codestable/tools/codestable-worktree-gate.py --root . --json start --unit .codestable/features/YYYY-MM-DD-{slug}
```

goal 包装的工作如果已有子 feature / issue / refactor unit，gate unit 指向子 unit。若 goal
还没有子 unit，在 goal iteration 中记录原因，并采用最轻的适用执行路径。

## Worktree 规则

- 只读取共享规划表面和本 worktree 的代码。
- 兄弟 worktree 的意图只有同步进共享文档后才能读取。
- 出现计划冲突时停下，交给 owner 判断。
- 缺 env / secrets 视为环境阻塞，不视为代码失败。

## 收尾 checkpoint

unit 全流程完成、准备离开 worktree 前：

1. 确认工作区干净、改动已提交、finish gate 已记录 merge readiness。
2. 向用户呈现合并策略：合并到目标分支 / 推分支开 PR / 暂不合并。合并策略始终由用户定。
3. 用户确认后执行；确认合并成功再清理 worktree 与分支。worktree 有未提交改动时不清理。

## 独立代码 Review

每个执行 worktree 在汇报一批实现完成前，必须触发独立 review。review 是完成 gate，不是
commit 前的事后补票。详细 review 流程由 `cs-code-review` 负责；需要输入包时运行：

```bash
python3 .codestable/tools/build-review-packet.py --root . --unit .codestable/features/YYYY-MM-DD-{slug} --stage quality --output /tmp/codestable-review.md --validation "{验证命令} -> {结果}"
```

不要包含 `.env`、token、secret 或本地凭证。reviewer 结果被核验并合并进报告后，按
`.codestable/reference/agent-conventions.md` 的 Task Agent 生命周期关闭。

## Context、Finish 与 Commit

context packet、finish gate、inbox、commit planner 和 backlog 工具的完整用法见
`.codestable/reference/tools-context.md`。常用命令：

```bash
python3 .codestable/tools/build-context-packet.py --root . --unit .codestable/features/YYYY-MM-DD-{slug} --audience handoff --output /tmp/codestable-handoff.md --decided "{已决定}" --remaining "{下一步}"
python3 .codestable/tools/check-context-sufficiency.py --file /tmp/codestable-human-review.md --strict --json
python3 .codestable/tools/codestable-finish-worktree.py --root . --unit .codestable/features/YYYY-MM-DD-{slug} --json --validation "{验证命令} -> {结果}"
python3 .codestable/tools/codestable-worktree-gate.py --root . --json commit --unit .codestable/features/YYYY-MM-DD-{slug}
python3 .codestable/tools/codestable-doctor.py --root . --json
python3 .codestable/tools/codestable-backlog.py --root . --json
python3 .codestable/tools/codestable-worktree-inbox.py --root . --json
```

Finish gate 会写 learning、context-check、merge-readiness 和 inbox 记录。finish 报告后如果
分支变化，状态变为 `stale-report`，必须重跑 finish。
