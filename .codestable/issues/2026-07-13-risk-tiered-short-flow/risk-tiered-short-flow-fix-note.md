---
doc_type: issue-fix
issue: 2026-07-13-risk-tiered-short-flow
path: standard
fix_date: 2026-07-13
related: [risk-tiered-short-flow-analysis.md]
tags: [workflow-routing, feature-lanes, focused-review]
github_issue: 43
review_status: passed
---

# 风险分级与短流程修复记录

## 1. 实际采用方案

采用已确认的方案 B：把单 feature 的执行语义拆成 Quick / Standard / Goal 三条 lane。

- Quick：需求明确、改动局部、复用既有契约、有目标验证且没有高风险边界时自动选择；只保留实现、验证、首次独立代码审查和简短 ff-note。
- Standard：需要 design 或跨模块决策，但在当前 run 完成；approved design 不再默认创建 goal package，code review 后进入 accept-inline。
- Goal：仅在用户显式要求长程执行、已有 goal state 或 Epic 上下文时启用；保留 goal driver、独立 QA 和完整 acceptance。
- Review：首次独立审查不变；只有可精确归因的 test/docs/type/metadata/nit-only 修正可走 focused closure，实质变化或不确定情况完整独立复审。
- 用户反馈：出现“这是小改动 / 流程太重 / 文档比代码多”等信号时必须暂停并重新分类。

兼容策略：旧 design 缺 `execution_lane` 且没有 goal state 时按 Standard；已有 `goal-state.yaml` 始终按 Goal；Epic child 仍由唯一 Epic goal owner 接管，forward/reverse claim 冲突 fail-closed。

## 2. 改动文件清单

- 路由与流程契约：`plugins/codestable/skills/cs/SKILL.md`、`cs-feat/SKILL.md`、`cs-code-review/SKILL.md`。
- 阶段协议：fastforward、design、design-review、implementation、QA、acceptance 及 review report template。
- 可执行恢复：`plugins/codestable/skills/cs-onboard/tools/codestable-workflow-next.py`，增加 Quick/Standard 状态恢复、Epic parent ownership、reviewer/QA/doc_type gate 与 lane 冲突 fail-closed。
- Runtime reference：更新 package source 的 `tools.md`，并通过 runtime sync 同步 `.codestable/reference/tools.md`。
- 用户文档：中英文 README、WORKFLOW、SKILL_CATALOG。
- 回归覆盖：workflow-next、skill contract、workflow scenario 测试，以及 `rt-f15` 至 `rt-f18` routing fixtures。
- 闭环记录：本 issue 的 report、analysis 和 fix-note。

没有修改 #45、#46、#47 对应的安装更新、standalone 版本和 current-session 实现。

## 3. 验证结果

### RED

- 目标命令：6 个新增 lane/review 用例。
- 结果：`6 failed`。
- 失败证据：Standard 仍返回 `goal_package`；Goal evidence 没有 lane；skill 文本缺 Quick/Standard/Goal、用户反馈重分类和 focused closure 契约。
- Round 1 review-fix：首批 16 个对抗用例全部失败，复现 Epic child 假完成、Quick 被恢复为 design、QA failed 越过、伪 reviewer 放行和重复 checklist I/O；追加的 lane 冲突/Goal 优先 2 个边界用例同样失败。
- Round 2 review-fix：2 个新增用例均失败；batch=true 的 approved child 返回 `CS_FEATURE_STANDARD_COMPLETE`，roadmap-owned draft child 返回 `feature-design-confirmation`。
- Round 3 review-fix：metadata-less legacy child 的未完成/已完成两态均走错 Standard，权威 SKILL Spec 同时缺 roadmap owner 契约。
- Round 4 review-fix：可读但无关的 identity mismatch state 误阻塞 Standard/Quick，且 reverse ownership 的负向/fail-closed 分支缺测试与路径诊断。
- Round 5 review-fix：15 个目标反例中 `14 failed, 1 passed`；复现 design metadata 指向缺失 state 时漏掉外部真 owner、forward owner 未发现第二 claim、Quick 吞掉 failed/blocked QA/acceptance，以及损坏 frontmatter/checklist/feature 或 Epic goal-state 输出 traceback。
- Round 6 review-fix：pre-goal-package child 的 draft/approved 两态均失败，分别错误进入单 feature confirmation 与 `CS_FEATURE_STANDARD_COMPLETE`；`roadmap` / `roadmap_item` 仅写一个的两态也继续了 standalone 流程。
- Round 7 review-fix：metadata-less pre-goal child 的显式 items pointer 两态均失败，draft 错误进入 `feature-design-confirmation`，approved 全产物错误输出 `CS_FEATURE_STANDARD_COMPLETE`；显式 pointer 目标缺失时还会错误回退到 slug glob。
- Round 8 review-fix：Standard/Quick 的短 slug 后缀碰撞均被错误认领为 Epic；forward items/goal owner 均漏检同文件或跨 roadmap 第二 claim；合法 YAML 的错误 items 容器 fail-open，错误 feature 类型则输出 traceback 而非 JSON。
- Round 9 review-fix：reverse/forward goal owner 遇到合法 YAML 转义 NUL 的 `feature_dir` 时均输出裸 traceback，stdout 不是 JSON。
- Round 10 review-fix：design roadmap slug 含 NUL 时 traceback；reverse goal owner 对错误 `features` 容器/row fail-open；items 显式 pointer 含 NUL 时被当作目标缺失并产生假完成。
- Round 11 review-fix：forward goal owner 排除整份 goal-state，静默漏掉同文件第二 row 对当前 feature 的 claim。

### GREEN

- 初始目标用例：`6 passed`；Round 1 review-fix：`18 passed`；Round 2：`2 passed`；Round 3：`3 passed`；Round 4 reverse matrix：`8 passed`；Round 5：`15 passed`；Round 6 ownership：`5 passed`；Round 7 items ownership：`12 passed`；Round 8 owner hardening：`13 passed`；Round 9 goal-state path hardening：`2 passed`；Round 10 owner input hardening：`4 passed`；Round 11 row-level owner exclusion：`1 passed`；workflow-next 全组：`102 passed`。
- Round 7 GREEN：metadata-less child 可由 parent items 的权威显式 pointer 或 `feature: null` + 命名回退反向唯一认领；同文件/跨 roadmap 多 claim、损坏 items fail-closed；无关 items 不误伤；forward item pointer 必须匹配当前 feature；Epic 与 feature 两个入口共享 pointer 解析语义。
- Round 8 GREEN：目录回退按 `feature_slug_from_dir` 精确匹配且多精确目录 fail-closed；forward items/goal owner 排除本条目后反查剩余 items claim；错误 items 容器或 feature 类型在 reverse/forward/Epic 三入口均返回带路径的结构化 blocked JSON。
- Round 9 GREEN：goal-state `feature_dir` 的类型、Path 构造与 resolve 在 reverse/forward 两入口统一 fail-closed；NUL 路径均 exit 1、JSON blocked、stderr 空且带 goal-state 路径。
- Round 10 GREEN：共享 `checked_yaml_path` 覆盖 roadmap slug、items pointer、goal-state feature_dir；reverse goal owner 拒绝非 list-of-mappings 的 `features`；三类异常均结构化 blocked，不再 fail-open 或 traceback。
- Round 11 GREEN：goal-state owner 排除键改为 `(goal_state_path, roadmap_item)`，同文件第二 claim 与跨文件 claim 对称 fail-closed。
- 相关回归：`198 passed`，覆盖 workflow-next、entry simplification、workflow scenarios 和 skill contracts。
- 正式测试目录全量：`pytest -q tests`，`434 passed in 6.24s`，600 秒进程组超时保护。
- Plugin checker：`ok: true`，`findings: []`；ruff 使用 `--ignore E402`（工具 bootstrap 的既有 re-exec import 风格）通过。
- Runtime sync：写入和 `--check --json` 均为 `status: ok`；package source 与 repo-local `tools.md` 内容一致。
- JSON fixtures：`rt-f15` 至 `rt-f18` 均通过结构化解析；skill contract 测试通过。
- 清洁度：`git diff --check` 通过；修改的 Markdown 均不超过 300 行；plugin 目录无 `__pycache__` / `*.pyc` 残留。

裸 `pytest` 会收集隔离实验种子并因当前环境没有 `taskhub` 出现 18 个 collection errors；仓库正式 `tests/` 全量已通过。本次未运行付费多模型 routing eval 或真实 agent E2E，fixtures 的 results 文档已明确标记尚未重新测量。

## 4. 遗留事项

- #45：skills update 删除已安装的 cs 系列技能。
- #46：`cs-feedback --session current` 多候选定位。
- #47：standalone 安装的 runtime 版本为 unknown。
- 本次新增 routing fixtures 待后续统一付费多模型 campaign 测量；不阻塞规则、运行时状态机和机械回归落地。
- Round 11 独立审查初始为 `changes-requested`（0 blocking，1 important）；R11-001 完成 RED/GREEN、全量验证与 OCR 0 comments 后，原 reviewer focused closure `passed`（0 blocking，0 important），最终 review gate 已闭合。
