---
doc_type: feature-acceptance
feature: 2026-07-17-lean-workflow-artifacts
status: passed
audit_state: completed
audit_reason: ""
auditor_id: ""
acceptance_authorization_ref: ""
accepted: 2026-07-17
round: 1
---

# Lean Workflow Artifacts 验收报告

> 阶段：阶段 3（验收闭环）
> 验收日期：2026-07-17
> 关联方案：`.codestable/features/2026-07-17-lean-workflow-artifacts/lean-workflow-artifacts-design.md`

## 1. 接口契约核对

- [x] `build-review-packet.py` 新增 `--transport workspace|portable`、repeatable `--include-path`、`--validation-tail-lines` 和 `--output -`。
- [x] 缺省 `transport=portable`；无新 flag 的文件输出与 1.0.4 legacy builder 在同一最终工作区逐字节一致。
- [x] scoped transport 拒绝仓库外路径、仓库根 `.`, absolute repo root 与规范化回根路径；精确文件/目录 allowlist 正常工作。
- [x] workspace 输出 locator、selected changed paths、validation reference 和 reviewer contract，不含 fenced body。
- [x] scoped portable 只带 allowlist 内文档/diff/untracked body，secret-like 内容省略，validation 保留有限 tail。
- [x] review `compact-passed` 保留完整 frontmatter、`reviewer/round/lane_*` 和第 4/5/6/7 节；异常状态使用 detailed variant。
- [x] Goal QA `compact-passed` 保留 runner 字段与第 1/2/5/7 节；failed/blocked/pending 使用 detailed variant。

流程图节点均有落点：implementation -> code review -> Standard inline behavioral verification -> acceptance；Goal/显式 QA 保留独立 QA receipt；qa-fix 后仍先回 code review。

## 2. 行为与决策核对

- [x] human document、workflow receipt、ephemeral transport 与 consumer projection 已进入共享 artifact contract。
- [x] 持久化判断与读取深度判断分离；未来消费者、不可重建性和 drill-down trigger 决定写入/读取。
- [x] 同 workspace reviewer 直接按 locator 回源；remote/file handoff 才生成 scoped portable packet。
- [x] passed review/QA 正文按 verdict 收紧；pending/ref/reason 和异常复测信息未被删除。
- [x] QA owner 改为 behavioral verification：执行功能/integration/E2E/browser/API/CLI/manual/contract 行为，不承担代码质量 finding。
- [x] Standard accept-inline 与 Goal QA 共用 `references/qa/behavioral-verification.md`，Standard 未生成 `{slug}-qa.md`。
- [x] acceptance 消费投影后完成 owner/requirement/roadmap/知识与 final audit，不重复逐文件 code review。

明确不做均守住：未迁移历史 artifact；未新增 store/index/RAG/runtime journal、digest wire、QA block kind/status、resolver 分支、worktree/branch 策略或旧 roadmap runtime。

挂载点反向核对：

- M1 artifact convention：source/runtime 文件逐字一致，system overview 与 representation classification 已登记。
- M2 packet CLI/tools：builder、transport module、tools reference 与 packet tests 一致。
- M3 reviewer transport：agent-conventions 与 independent-review 均明确 workspace locator / remote portable。
- M4 review projection：主 skill 与 report template 一致，code-review 不反向读取 cs-feat-local reference。
- M5 QA/implementation：behavioral contract、verdict template、qa-fix 顺序和 ephemeral implementation summary 一致。
- M6 acceptance：projection-first、Standard inline 和 final human audit 已同步。

拔除沙盘：删除上述 M1-M6 与新增测试/serializer 后可回到 legacy packet/full report 行为；没有额外 store、manifest schema 或历史迁移残留。

## 3. 验收场景核对

### Inline Verification Matrix

| ID | 来源 | 核心性 | 动作 | 期望 | 结果 / Evidence |
|---|---|---|---|---|---|
| QA-001 | S1 | core | artifact classification contract test | 分离 persistence/read-depth/drill-down | pass；semantic test |
| QA-002 | S2/S3 | core | `pytest -q tests/test_review_packets.py` | workspace 无正文、portable scoped/secret/tail、stdout、legacy golden | pass；7 passed |
| QA-003 | S2 | core | CLI `--transport workspace --include-path . --output -` | fail-closed，不生成 packet | pass；exit 1，`include path must not select repository root` |
| QA-004 | S3 | core | 1.0.4 builder 与当前 builder 在最终工作区分别生成 no-new-flag packet 后 `cmp` | 字节完全一致 | pass；`cmp` exit 0 |
| QA-005 | S4/S6/S8 | core | compact review + workflow/Goal/doctor regression | canonical status/reviewer/resolver 不回退 | pass；CMD-001 364 passed |
| QA-006 | S5/S7/S9 | core | behavioral/projection/route scenario tests | QA 职责、旧 verdict route、Standard inline/evidence drill-down 契约成立 | pass；9 passed |
| QA-007 | package/runtime | supporting | package checker + runtime sync | 新 serializer 入包，managed refs 无 drift | pass；package ok / runtime status ok |

场景 S1-S9 全部通过。功能入口是 packet CLI；其余协议行为由 contract/scenario/resolver fixture 从消费者输出验证，没有用 typecheck 或 diff review 替代核心行为证据。

Review 投影重点已覆盖：legacy bytes、workspace 正文缺席、portable secret/tail、root/traversal、stdout、compact resolver parity 和 Standard inline。failed/blocked 项为 none。

Dogfood read trace：

- Inline QA 阶段读取 design 第 3 节、checklist behavior checks、review 第 5/6 节、behavioral verification reference、测试/CLI 入口和 `git status` scope。
- Inline QA 阶段没有重新加载实现源码、完整 diff、implementation 汇报、完整 review narrative 或 raw gate/DoD；Standard 本就没有 evidence pack/raw gate artifact。
- Inline QA 通过后，acceptance final audit 才按自身职责重读完整 design、最终 diff、managed refs 和 requirement。此边界是可观察纪律，不宣称 runtime sandbox。

## 4. 术语一致性

- human document / workflow receipt / ephemeral transport / consumer projection / behavioral verification 在 design、shared reference、skill contract 和 README 中语义一致。
- 禁用方向（artifact store、persistent index、runtime journal、candidate digest、QA block kind）未进入实现或新 schema。
- `workspace` / `portable` 只描述 transport；`compact-passed` / `detailed variant` 只描述 verdict-sensitive body，不新增 status。

## 5. 领域影响盘点

- 新名词均是 workflow 文档分类，不是项目领域实体；无需写 `requirements/CONTEXT.md`。
- 本轮没有新增跨模块 runtime service、第三方依赖或难回退 wire schema；无需 ADR。
- 若未来把 receipt 升级为 versioned cross-workflow wire contract，需要独立 design 并重新判断 ADR。

## 6. Requirement Delta / Clarification 回写

- 关联 requirement：`.codestable/requirements/demand-driven-skill-runtime.md`，当前仍为 `draft`。
- 本 feature 只实现其中“按当前动作加载规则和证据”的最小 protocol slice，没有完成或改写整项能力愿景，也没有 owner-approved req delta。
- 结论：requirement 保持 draft，本轮不自由改写、不标 current、不修改 `implemented_by`；验收报告记录实际覆盖范围即可。

## 7. Roadmap 回写

- design 未设置 `roadmap` / `roadmap_item`，本 feature 非 roadmap 起头；跳过 roadmap 状态写回。

## 8. Attention 候选盘点

- 无新增 attention 候选。稳定规则已经进入按需加载的 `artifact-conventions.md` 与对应 skill/reference；把它复制进每次必读 attention 会反向增加 token。

## 9. 遗留

- workspace packet 会静默省略 secret-like changed path；同 workspace reviewer 可从 `git status` 回源，内容和值不会泄漏。后续可考虑仅输出 omitted count。
- QA read boundary 是 protocol + fixtures + dogfood 约束，不是 runtime 禁读机制；后续需靠 scenario/dogfood 持续守护。
- `tests/test_skills_cli_distribution.py` 的真实 skills CLI E2E 需要显式外部 CLI 环境，本轮按既有条件跳过 1 项。
- `cs-code-review/SKILL.md` 与 QA protocol 均正好 300 行，后续新增规则应继续抽 conditional reference，而不是扩写主文件。

## 10. 最终审计

- 验证证据来源：accept-inline behavioral verification；未生成独立 QA artifact。
- 聚合命令：CMD-001 `364 passed`；CMD-002 `622 passed, 1 skipped`；CMD-003 package `ok: true`；CMD-004 runtime sync `status: ok`, no drift；CMD-005 clean。
- 独立审查：Claude Opus 4.8 high Plan Mode round 1/2 均无 blocking/important；最终 review 为 compact `status: passed`, `reviewer: subagent`。
- Packet bytes（implementation-stage dogfood）：legacy 849,540；workspace locator 4,243（-99.50%）；scoped portable 226,825（-73.30%）。legacy 带 47 个 untracked blocks，workspace 0，scoped portable 仅 9 个 allowlist 内新增文件。
- Receipt body template：review detailed 3,092 -> compact 501 bytes（-83.80%）；QA detailed 2,013 -> compact 635 bytes（-68.46%）。
- QA 默认输入类别：12 -> 8；移除源码、完整 diff、implementation 汇报与正常路径 raw gate/DoD。
- 场景复核：re-verified 9 / trust-prior-verify 0。
- 交付物复核：shared/runtime reference、packet serializer/CLI、review/QA/acceptance/implementation contract、README、tests、review/acceptance 均存在。
- 完整工作区复核：本 feature scope 已覆盖 tracked/untracked；`.codestable/attention.md`、VISION、其他 feature/requirement/roadmap 是用户既有并行 baseline，未修改或吸收。
- Cleanliness：无 debug/TODO/FIXME/注释掉代码/无用 import；两个 `print` 是 CLI stderr/输出契约；`git diff --check` clean。
- 知识出口：artifact 规则已进 shared reference；无 attention/CONTEXT/ADR/compound 新候选。
- 技术结论：通过；Standard owner 已于 2026-07-17 终审确认。
