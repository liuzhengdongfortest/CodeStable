---
doc_type: issue-review
issue: 2026-07-13-risk-tiered-short-flow
status: passed
reviewer: subagent+ocr
reviewed: 2026-07-14
round: 11
---

# 风险分级与短流程代码审查报告

## 1. Scope And Inputs

- Issue: `.codestable/issues/2026-07-13-risk-tiered-short-flow/`
- Fix note: `risk-tiered-short-flow-fix-note.md`
- Implementation evidence: fix-note 的 RED/GREEN/全量验证记录
- Diff basis: `git status --short`、完整工作区 `git diff`
- Baseline dirty files: 当前 diff 全部属于 GitHub #43；#45/#46/#47 仅建 issue，未混入实现

### Independent Review

- Detection: Paseo Task agent 与 OCR CLI 均可用
- 环节 A 独立隔离 Task agent: Paseo `claude-fable-5` / high / read-only，completed
- 环节 B OCR CLI: completed
- OCR severity mapping: High -> blocking/important，Medium -> nit/suggestion，Low -> discarded
- Merge policy: Paseo、OCR 与主 agent 本地发现已逐条按仓库事实核验
- Gate effect: none；Round 11 + focused closure 合并结论为 0 blocking / 0 important

## 2. Diff Summary

- 新增：四个 routing fixtures、issue report/analysis/fix-note
- 修改：`cs` / `cs-feat` / `cs-code-review` 契约、阶段协议、workflow-next、测试与中英文文档
- 删除：none
- 风险热点：lane 状态恢复、legacy artifact 兼容、review/QA gate 放行条件

## 3. Adversarial Pass

- 假设的生产 bug：恢复工具把已有流程产物恢复到错误 lane，并发出假完成信号。
- 主动攻击过的反例：legacy Epic child、forward/reverse owner 冲突、仅 ff-note 的 Quick、失败 QA/acceptance、伪造 passed review、损坏 YAML、已有 design 强制 quick。
- 结果：Round 1 至 Round 5 的 blocking/important 均进入对应 review-fix；Round 6 独立复审前不定稿 passed。

## 4. Findings

### blocking

- [x] REV-001 `codestable-workflow-next.py:653` legacy Epic child 可被恢复为 Standard
  - Evidence: child 的 goal-state 位于 roadmap；feature 恢复只检查 feature 级 `goal-state.yaml`，且 `--epic-child-batch` 只覆盖 design 批量阶段。
  - Impact: 可跳过 Epic 强制 QA，并输出与 roadmap 状态矛盾的 `CS_FEATURE_STANDARD_COMPLETE`。
  - Expected fix scope: 根据 design 的 roadmap 归属和 roadmap goal-state fail-closed 交回 `cs-epic`。

### important

- [x] REV-002 `codestable-workflow-next.py:187` Quick 的 ff-note 不参与 artifact 恢复
  - Evidence: 仅有 `{slug}-ff-note.md` 时被判为缺 design。
  - Impact: 已闭环 Quick feature 会被重新复活为 design 待办。
- [x] REV-003 `codestable-workflow-next.py:209` Standard 恢复忽略已有 QA 状态
  - Evidence: `{slug}-qa.md status: failed|blocked` 仍路由 accept-inline。
  - Impact: 与 acceptance 协议冲突，可能形成 acceptance/qa-fix 往返。
- [x] REV-004 `codestable-workflow-next.py:240` Standard 的 passed review 不校验独立 reviewer 锚点
  - Evidence: `status: passed` 且 reviewer 缺失或为 self 时仍可完成。
  - Impact: Standard 没有 Goal audit 兜底，可绕过必需的独立 review gate。
- [x] REV-005 `cs-feat/SKILL.md:53` 显式 Quick 可越过已有 design 的已记录 lane
  - Evidence: Quick 判定在 `hasExistingDesign` 前，且未要求把降级结果持久化。
  - Impact: design 仍为 Standard、ff-note 却已生成，恢复状态互相矛盾。

### nit

- [x] REV-006 `cs-feat/SKILL.md:136` `lane == Quick -> Design` 为不可达分支。
- [x] REV-007 `codestable-workflow-next.py:689` `execution_lane` 未做 trim/case 归一。
- [x] REV-008 `codestable-workflow-next.py:329` `acceptance-inline` 与公开 `--stage accept` 命名不一致，完成 marker 未登记。
- [x] REV-009 `codestable-workflow-next.py:685` checklist 在 evidence 和 Standard resolver 重复解析。
- [x] REV-010 `codestable-workflow-next.py:216` passed review/acceptance 未校验 `doc_type`。

### suggestion

- 后续可为 Standard review 记录 reviewed commit，防止 passed 后 diff 漂移。

### learning

- 状态机测试应优先锁定 artifact 组合和 next action，不能只断言 skill 文案存在。

### praise

- Goal state 优先于 recorded lane、非法 lane fail-closed、runtime source/copy 同步均已有有效测试。

## 5. Test And QA Focus

本地 closure：REV-001..REV-010、R2/R3/R4、R5-001..003、Round 6 至 Round 11 findings 均已有对应状态机/契约测试；workflow-next 102 passed、相关 198 passed、正式全量 434 passed；R11-001 focused closure 已通过。

- 必测：roadmap goal-state + approved legacy child 且不带 batch flag。
- 必测：ff-note-only Quick 的 review pending/fixing/passed 三态。
- 必测：Standard QA failed/blocked 与 reviewer 缺失/self。
- 必测：已有 design 从 Standard 降级 Quick 后可跨进程恢复。
- 不运行付费多模型 routing eval；fixtures 的真实模型测量继续明确标为待执行。

## 6. Residual Risk

- Quick 自动分类仍是模型判断；本轮只验证契约与机械状态恢复，真实模型准确率留给后续付费 campaign。

## 7. Verdict

- Status: passed
- Next: issue review gate 已闭合，可进入 `cs-issue` 收尾提交阶段。

## 8. Round 2 Review

- Reviewer: Paseo `claude-fable-5` / high / plan-read-only，agent `6dac3fd9-806b-484b-bc1f-1f8769475047`
- OCR: 9 files reviewed，0 comments
- Verdict: `changes-requested`（0 blocking，2 important）
- [x] R2-001 `codestable-workflow-next.py:653` `epic_child_batch` 未参与 lane 分类，可产生 Standard 假完成。
  - RED: approved child + passed review/acceptance + 无 roadmap goal-state + batch=true，实际返回 `CS_FEATURE_STANDARD_COMPLETE`。
  - GREEN: batch context 记录 `execution_lane=goal` / source=`epic-child-batch`，reviewed child 交回 `return-to-cs-epic-batch-loop`。
- [x] R2-002 `codestable-workflow-next.py:849` roadmap goal-state 拥有的 draft child 先停单 feature ConfirmDesign。
  - RED: draft + passed design-review + 唯一 roadmap owner，实际返回 `feature-design-confirmation`。
  - GREEN: 显式 batch 分支优先，其次 roadmap owner；两者均在单 feature ConfirmDesign 前交回 Epic。
- Verify: 目标 `2 passed`，workflow-next `40 passed`，相关 `135 passed`，正式全量 `371 passed in 4.96s`；plugin checker/runtime sync/diff check 均通过。

## 9. Round 3 Review

- Reviewer: Paseo `claude-fable-5` / high / plan-read-only，agent `92a5678c-5f1d-4623-abf5-e18fe5870216`
- OCR: 9 files reviewed，0 comments；报告部分文件有内部 warning，无 finding
- Verdict: `changes-requested`（0 blocking，2 important）；R2-001/R2-002 与 REV-001..REV-010 均确认未回归
- [x] IMP-1 metadata-less legacy child 无法被 parent `features[].feature_dir` 反向认领。
  - RED: 产物未齐时错误进入 Standard implementation；产物齐全时错误输出 `CS_FEATURE_STANDARD_COMPLETE`。
  - GREEN: metadata 缺失时结构化扫描 roadmap goal-state，按 resolved `feature_dir` 反向唯一认领；损坏或多 owner fail-closed。
- [x] IMP-2 `cs-feat/SKILL.md` 权威 Spec 未建模 roadmap owner，模型路径与工具矛盾。
  - RED: Spec 缺 `roadmapOwner`、`hasRoadmapOwner(s)` 与 `features[].feature_dir` 反向认领契约。
  - GREEN: FeatureState、lane 分类、restore guard 和 Epic 恢复散文同步，roadmap owner 在单 feature ConfirmDesign 前交回 Epic。
- Verify: 目标 `3 passed`，workflow-next `42 passed`，相关 `138 passed`，正式全量 `374 passed in 5.04s`；plugin checker/runtime sync/source-copy/diff check 均通过。

## 10. Round 4 Review

- Reviewer: Paseo `claude-fable-5` / high / plan-read-only，agent `91f47cd0-1a09-4271-a214-30a307deaf4f`
- OCR: 9 files reviewed，0 comments
- Verdict: `changes-requested`（0 blocking，2 important）；IMP-1/IMP-2 及更早 findings 均确认未回归
- [x] R4-001 可读但 identity mismatch 的无关 roadmap state 全局误阻塞 metadata-less Standard/Quick，且诊断缺具体路径。
  - RED: 无关 Standard/Quick 两态均 blocked；identity mismatch 真指向当前 feature、损坏 YAML、多 owner、缺 item 的 blocked/evidence 均无路径。
  - GREEN: 可读 mismatch 仅在 `feature_dir` 指向当前 feature 时阻塞；不可解析/非 mapping 继续全局 fail-closed；blocking 与 evidence 写具体 state 路径。
- [x] R4-002 reverse ownership 负向/fail-closed 分支无固定测试。
  - GREEN: 固化合法 0 owner、无关 mismatch Standard/Quick、mismatch 真 claim、损坏 YAML、跨 roadmap/同 state 多 claim、匹配行缺 item 共 8 个状态断言。
- Verify: reverse matrix `8 passed`，workflow-next `50 passed`，相关 `146 passed`，正式全量 `382 passed in 5.02s`；plugin checker/runtime sync/source-copy/diff check 均通过。

## 11. Round 5 Review

- Reviewer: Paseo `claude-fable-5` / high / plan-read-only，agent `133b4cc8-7420-4df7-93ac-8e410c5cab57`
- OCR: 9 files reviewed，0 comments
- Verdict: `changes-requested`（0 blocking，3 important）；R4-001/R4-002 及更早 findings 均确认未回归
- [x] R5-001 design metadata 指向的 roadmap 无 goal-state 时，外部 roadmap 的真实 claim 被忽略；forward owner 也未检测第二 claim。
  - RED: 两个 owner 冲突场景分别错误输出 Standard complete 或继续交回单一 Epic owner。
  - GREEN: forward state 缺失或已证明 owner 后都执行排除自身的反向扫描；实际 claim 与预期 owner 不一致时按具体 state 路径 fail-closed。
- [x] R5-002 Quick 忽略同目录内 failed/blocked QA 或 acceptance，可带失败证据假完成。
  - RED: 四组 failed/blocked 质量证据均错误输出 `CS_FEATURE_QUICK_COMPLETE`。
  - GREEN: Quick 对已存在的 QA/acceptance 只兼容 `doc_type` 正确且 `status: passed` 的产物，其他状态返回 `resolve-quick-quality-conflict` 并给出路径。
- [x] R5-003 损坏 frontmatter、checklist 或普通 goal-state 抛裸 traceback，破坏 `--json` 机器契约。
  - RED: feature 七类 artifact 与 Epic goal-state 共八类路径均抛解析异常，CLI 无合法 JSON。
  - GREEN: artifact parse error 统一转为含路径和异常类型的结构化 `blocked`；CLI exit 1 且 stderr 无 traceback。
- Verify: 目标 `15 passed`，workflow-next `65 passed`，相关 `161 passed`，正式全量 `397 passed in 5.43s`；plugin checker/runtime sync/source-copy/JSON/Markdown/diff check 均通过。

## 12. Round 6 Review

- Reviewer: Paseo `claude-fable-5` / high / plan-read-only，agent `8f1c74b6-c764-48fc-b1ca-ac6e51bc0d64`
- OCR: 9 files reviewed，0 comments
- Verdict: `changes-requested`（0 blocking，1 important）；R5-001/R5-002/R5-003 与更早 findings 均确认未回归
- [x] IMP-R6-1 pre-goal-package 的 Epic child 可被当作 standalone Standard 推进，与 SKILL 的 design roadmap ownership 契约矛盾。
  - RED: parent roadmap/items 存在且 goal-state 尚未生成时，draft child 返回 `feature-design-confirmation`，approved 全产物 child 返回 `CS_FEATURE_STANDARD_COMPLETE`。
  - GREEN: 完整 design metadata 经 parent `items.yaml` 唯一条目证明后记录 `roadmap_owner_source: roadmap-items` 并交回 `cs-epic`；items 缺失、损坏、identity 不符或条目不唯一 fail-closed。
- [x] LOCAL-R6-1 design 只写 `roadmap` 或只写 `roadmap_item` 时被当作 metadata-less feature，可误走 standalone 或错误反向 owner。
  - RED: 两种单字段形态均继续 standalone 流程。
  - GREEN: metadata 必须同时为空或成对存在；不完整时返回 `blocked / fix-feature-roadmap-metadata`。
- Non-blocking nits accepted for this issue: forward 同 state 第二行 claim、合法非 mapping frontmatter/goal-state 诊断、lane conflict 提示方向、错名 review artifact fallback；不影响本轮 blocking/important gate。
- Verify: Round 6 ownership `5 passed`，workflow-next `70 passed`，相关 `166 passed`，正式全量 `402 passed in 5.40s`；plugin checker/runtime sync/source-copy/JSON/ruff/Markdown/diff check 均通过。

## 13. Round 7 Review

- Reviewer: Paseo `claude-fable-5` / high / plan-read-only，agent `68744f37-f398-48a9-9da8-322105b0bfd2`
- Verdict: `changes-requested`（0 blocking，1 important）；Round 1 至 Round 6 已关闭 findings 均确认未回归
- [x] R7-001 metadata-less pre-goal-package Epic child 只查 roadmap goal-state，不查 parent items，可进入单 feature confirmation 或输出 Standard 假完成。
  - RED: items 以显式 `feature:` 指向当前目录时，draft 返回 `user_gate / feature-design-confirmation`，approved 全产物返回 `complete / CS_FEATURE_STANDARD_COMPLETE`；显式缺失 pointer 还会错误回退 slug glob。
  - GREEN: metadata-less 路径在无 goal-state owner/error 后反向扫描 parent items；显式 pointer 具有权威性，`feature: null` 才使用 metadata/glob 回退；唯一 owner 交回 Epic，多 claim/损坏 items 带路径 fail-closed，无关 items 不误伤 standalone。
  - Consistency: forward items owner 校验 pointer 必须匹配当前 feature；Epic `find_feature_dir` 与 feature 反向 owner 共用 pointer 路径解析，跨入口测试锁定相同结论。
- Non-blocking nits retained as residual risk: NUL 路径值的结构化诊断、items artifact action 命名、items identity 缺失、其他诊断细节；不影响 R7-001 的 blocking/important gate。
- Verify: Round 7 items ownership 新增 `12 passed`，workflow-next `82 passed`，相关 `178 passed`，正式全量 `414 passed in 5.56s`；plugin checker/runtime sync/source-copy/JSON/ruff/Markdown/diff check 均通过。

## 14. Round 8 Review

- Reviewer: Paseo `claude-fable-5` / high / plan-read-only，agent `6d3edc23-322b-4d31-b389-aca7e5d477b7`
- OCR: 9 files reviewed，0 comments
- Verdict: `changes-requested`（1 blocking，1 important）；Round 1 至 Round 7 已关闭 findings 均确认未回归
- [x] R8-001 未锚定 `*-{slug}` 回退把 `auth/user-auth`、`export/small-export` 后缀碰撞误认作 Epic owner。
  - RED: standalone Standard 错误 `return-to-cs-epic`；已完成 Quick 被复活为 `cs-feat design`。
  - GREEN: 用 `feature_slug_from_dir` 精确匹配目录 slug；多精确匹配经 Epic/feature 两入口结构化 fail-closed。
- [x] R8-002 forward items/goal owner 证明后未按条目排除自身并反查第二 items claim。
  - RED: 同文件第二行与跨 roadmap 第二 claim 均静默放行。
  - GREEN: `(items_path, roadmap_item)` 作为排除键，其他行/roadmap 继续参与冲突扫描并保留路径。
- [x] LOCAL-R8-003 合法 YAML 的错误 items/feature 类型会 fail-open 或破坏 `--json` 机器契约。
  - RED: items mapping exit 0 进入 Standard；`feature: []` 输出 traceback 且 stdout 非 JSON。
  - GREEN: 共享 list-of-mappings/string-or-null 校验，reverse/forward/Epic 三入口均 exit 1、JSON blocked、stderr 空且含具体路径。
- Non-blocking: sibling 损坏 design 的 owner 诊断波及、review commit 锚点等保留为 residual risk；ruff 验证已明确实际 `--ignore E402` 调用。
- Verify: Round 8 新增 `13 passed`，workflow-next `95 passed`，相关 `191 passed`，正式全量 `427 passed in 5.78s`；等待 Round 9 复审前不提前标 passed。

## 15. Round 9 Review

- Reviewer: Paseo `claude-fable-5` / high / plan-read-only，agent `dceb0881-02e7-4981-b36a-1f0dd612c0e2`
- OCR: 9 files reviewed，0 comments
- Verdict: `changes-requested`（0 blocking，1 important）；R8-001/R8-002/LOCAL-R8-003 与历史 findings 均确认未回归
- [x] LOCAL-R9-001 reverse/forward goal owner 对合法 YAML 转义 NUL 的 `features[].feature_dir` 调用 `Path.resolve()` 时裸 traceback。
  - RED: 两入口 CLI stdout 为空、stderr traceback，无法解析 JSON。
  - GREEN: 两处同时校验 string 类型并捕获 Path/resolve 的 `ValueError`/`OSError`；reverse 写入 invalid state，forward 返回 owner error，均含 goal-state 路径。
- Non-blocking: items 重复同 slug、同文件错误文案、第二 items 文件、reviewer/commit 锚点保留为 nit/suggestion，不扩大本 issue。
- Verify: Round 9 新增 `2 passed`，workflow-next `97 passed`，相关 `193 passed`，正式全量 `429 passed in 6.47s`；等待 Round 10 复审前不提前标 passed。

## 16. Round 10 Review

- Reviewer: Paseo `claude-fable-5` / high / plan-read-only，agent `1bb3eb52-777c-4688-be4c-9e986242496b`
- OCR: 9 files reviewed，0 comments
- Verdict: `changes-requested`（0 blocking，3 important）；LOCAL-R9-001 与历史 findings 均确认未回归
- [x] R10-001 design `roadmap` slug 含合法 YAML 转义 NUL 时进入 `glob()` 裸 traceback。
- [x] R10-002 reverse goal owner 对 mapping `features` 或非-mapping row 静默跳过，可继续错误 owner/Standard 路径。
- [x] R10-003 items 显式 pointer 含 NUL 时 `Path.exists()` 吞异常，reverse 当作无 claim 并可假完成。
  - RED: roadmap slug stdout 非 JSON；两种 goal-state features 形状 exit 0；NUL pointer exit 0 输出 Standard complete。
  - GREEN: `checked_yaml_path` 统一 string/NUL/Path 校验，显式 pointer 在 exists 前 resolve；reverse goal rows 统一 list-of-mappings 校验，三类均带 artifact 路径 blocked。
- Non-blocking: items 重复同 slug、同路径重复文案、第二 items 文件与 reviewer/commit 锚点继续保留为 nit/suggestion。
- Verify: Round 10 新增 `4 passed`，workflow-next `101 passed`，相关 `197 passed`，正式全量 `433 passed in 6.23s`；等待 Round 11 复审前不提前标 passed。

## 17. Round 11 Review

- Reviewer: Paseo `claude-fable-5` / high / plan-read-only，agent `9375e60c-706d-4442-a72b-900997b43ace`；OCR 两轮均为 9 files / 0 comments。
- Initial verdict: `changes-requested`（0 blocking，1 important，4 nit）；Round 10 三项与全部历史 findings 确认未回归。
- [x] R11-001 forward goal owner 以整文件排除自身，漏检同一 goal-state 第二 row 对同一 feature 的 claim。
  - RED: 完整 metadata + 同 state 两个 item 指向同 feature 时返回 `continue / return-to-cs-epic`。
  - GREEN: 排除键改为 `(goal_state_path, roadmap_item)`；只跳过已证明行，其余 rows 继续唯一性检查。
- Non-blocking: NUL item slug 输入加固、诊断文案与 epic goal-state 最小 shape 校验保留为 nit/suggestion；plugin bytecode 残留已清理。
- Verify: ownership focused `7 passed`，workflow-next `102 passed`，相关 `198 passed`，正式全量 `434 passed in 6.24s`；ruff/plugin checker/runtime sync/source-copy/fixtures/Markdown/diff check 均通过。
- Focused closure: `passed`（0 blocking，0 important）；六组对抗覆盖同文件不同/相同 item、跨文件 claim、无关 row 与 metadata-less reverse，R11-001 已关闭。
- Combined verdict: `passed`；保留 4 个 nit / residual risk，不阻塞 #43。
