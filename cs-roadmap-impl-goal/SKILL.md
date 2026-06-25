---
name: cs-roadmap-impl-goal
description: CodeStable 大需求端到端 goal 编排技能。用于用户给出一个较大软件需求，并希望先用 cs-roadmap 沉淀 roadmap，经 cs-roadmap-review 通过后用户确认，再为 roadmap items 中每个子 feature 完成 cs-feat-design/checklist 和 cs-feat-design-review，经过用户确认后输出一条可直接粘贴的 /goal 指令，由 goal 会话循环逐个 feature 执行 cs-feat-impl、cs-code-review、cs-feat-qa 和 cs-feat-accept，直到整个 roadmap 验收完成。触发：用户说“做完整个 roadmap”、“把这个大需求拆完并自动推进”、“生成 goal 指令跑完整个 CodeStable roadmap”、“像 supergoal 一样规划并执行这些 features”、“一次性跑完 roadmap 里的所有 feature”等。
---

# cs-roadmap-impl-goal

## 启动必读

开始任何判断或动作前，先读取 `.codestable/attention.md`；缺失则视为骨架不完整，提示先补齐或运行 `cs-onboard`，不要回退到外部 AI 入口文件。

---

## 目标

把一个大需求变成可审阅、可恢复、可自动推进的 CodeStable roadmap 执行包：

1. 先按 `cs-roadmap` 规范澄清需求并创建 / 更新一份 roadmap，运行 `cs-roadmap-review` 并处理到通过。
2. 用户确认 roadmap 后，为 roadmap items 里的每个子 feature 运行 `cs-feat-design`，生成 design + checklist，运行 `cs-feat-design-review` 并处理到通过。
3. 用户确认所有 feature design 后，输出一条可直接粘贴的 `/goal` 指令。
4. `/goal` 会话按顺序循环执行每个 feature：`cs-feat-impl` → `cs-code-review` → 必要时 review-fix → `cs-feat-qa` → 必要时 qa-fix 后重跑 review/QA → `cs-feat-accept` → 更新状态 → 下一个 feature。
5. 全部 feature 验收后，做整个 roadmap 的最终审计；只有审计通过才打印完成标记。

注意：不要把长任务正文塞进 `/goal` 参数。长协议和 feature 执行规格写入 roadmap 自己的目录，`/goal` 只引用这些文件和终止标记。

---

## 目录约定

**复用 `cs-roadmap` 的目录，不创建独立顶层目录。**

在现有 roadmap 目录下增加 goal 执行文件：

```text
.codestable/roadmap/{slug}/
├── {slug}-roadmap.md
├── {slug}-items.yaml
├── {slug}-roadmap-review.md
├── goal-plan.md          # 本次 goal 执行总览：假设 / 风险 / feature 顺序 / 验证命令
├── goal-state.yaml       # goal 会话实时状态
├── goal-protocol.md      # 从本技能 references/protocol.md 复制并按 slug 落地
├── goal-audit.md         # goal 会话结束前生成的最终 roadmap 审计报告
└── goal-features/
    └── {feature-slug}.md # 每个 feature 的执行规格，指向 design/checklist
```

普通 feature 仍放在标准目录：

```text
.codestable/features/{YYYY-MM-DD}-{feature-slug}/
├── {feature-slug}-design.md
├── {feature-slug}-checklist.yaml
├── {feature-slug}-design-review.md
├── {feature-slug}-review.md       # goal 执行时生成
├── {feature-slug}-qa.md           # goal 执行时生成
└── {feature-slug}-acceptance.md   # goal 执行时生成
```

---

## 两次确认门禁

本技能必须按两次确认推进，不能跳过。

### 第一次确认：roadmap

先完成 `cs-roadmap` 的 new / update 流程，并通过人审前 review gate：

- 澄清大需求目标、范围、明确不做、成功标准。
- 读取 `.codestable/attention.md`、相关 requirements / architecture / compound / history features。
- 写 `{slug}-roadmap.md` 和 `{slug}-items.yaml`。
- 自查模块拆分、接口契约、依赖 DAG、最小闭环、safety net / polish / harden、验证入口、交付物、知识回写候选。
- 运行 `cs-roadmap-review`，如果有 blocking / blocked，先修订或等待 reviewer；不要把未通过 review gate 的 roadmap 给用户确认。
- 把完整 roadmap + items.yaml + `{slug}-roadmap-review.md` 给用户 review。

只有用户明确确认 roadmap 后，才进入所有 feature design 阶段。

### 第二次确认：所有 feature design

对 roadmap items 里的每个 planned 子 feature，按依赖顺序逐个完成 `cs-feat-design` 的候选设计阶段：

- 创建 feature 目录。
- 写 `{feature-slug}-design.md`，frontmatter 带 `roadmap` / `roadmap_item`。
- 写 `{feature-slug}-checklist.yaml`。
- 运行 `cs-feat-design-review`；有 blocking / blocked 时先修订或等待 reviewer，不进入用户二次确认。
- 按现有 `cs-feat-design` 约定，把 items.yaml 对应条目更新为 `in-progress` 并填写 `feature` 字段。
- design 必须包含：基线预检、必跑验证命令、交付物、验收场景证据类型、清洁度规则、可独立验证 steps。

这里把 `cs-feat-design` 普通模式里的单 feature 用户整体 review 推迟到本技能统一处理：每份 design 先保持 `draft`，不要逐个改 `approved`。全部 feature design 都写完且 design-review 都 passed 后，一次性给用户 review。用户可能反复修改任意一个 design；每次修改后同步更新 checklist，并对实质变化重跑 `cs-feat-design-review`。只有用户明确确认所有 design 后，才输出 `/goal`。

用户确认所有 design 后，先把每份 `{feature-slug}-design.md` 的 frontmatter `status` 从 `draft` 改为 `approved`，再生成 goal 执行包。`cs-feat-impl` 和 `cs-feat-accept` 都要求 design 已 approved；不要把 draft design 交给 goal 会话。

---

## 生成 goal 执行包

在 `.codestable/roadmap/{slug}/` 内写：

### `goal-plan.md`

包含：

- roadmap 路径和 items.yaml 路径
- feature 执行顺序
- 每个 feature 的一句话交付物
- 每个 feature 的性质：functional / non-functional / mixed
- roadmap 级核心验收路径：必须真实运行的用户 / API / CLI / 后端 / e2e / smoke 场景；没有则写 none，并说明为什么这是纯非功能性 roadmap
- 关键假设
- Top 3 风险与缓解
- 必跑验证命令集合
- 最终聚合测试命令集合：roadmap 完成前必须重跑的 build / typecheck / lint / unit / integration / e2e / smoke；纯非功能性 roadmap 可用静态 / 一致性 / schema / 文档校验替代，但要写理由
- 预检策略
- 验证工具缺失时的恢复策略：只能补测试依赖、锁文件或既有 runner 配置，不能新增同名 shim 或伪造验证结果
- 最终审计会核验的交付物类型

### `goal-state.yaml`

生成前必须先探测 git 基线：

1. 运行 `git rev-parse --is-inside-work-tree`。
2. 返回 `true` 时，运行 `git rev-parse HEAD`，把得到的 SHA 写入 `baseline_ref`。
3. 返回非 git 仓库时，`baseline_ref: no-git`。
4. 在 git 仓库内但无法取得 HEAD 时，先停止并修复基线（例如还没有任何提交），不要写 `no-git` 伪装成非 git 仓库。

格式：

```yaml
roadmap: "{slug}"
status: ready-to-dispatch
baseline_ref: "{git rev-parse HEAD 或 no-git}"
current_feature_index: 0
features:
  - slug: "{feature-slug}"
    roadmap_item: "{feature-slug}"
    feature_dir: ".codestable/features/YYYY-MM-DD-{feature-slug}"
    design: ".codestable/features/YYYY-MM-DD-{feature-slug}/{feature-slug}-design.md"
    checklist: ".codestable/features/YYYY-MM-DD-{feature-slug}/{feature-slug}-checklist.yaml"
    review: ".codestable/features/YYYY-MM-DD-{feature-slug}/{feature-slug}-review.md"
    qa: ".codestable/features/YYYY-MM-DD-{feature-slug}/{feature-slug}-qa.md"
    acceptance: ".codestable/features/YYYY-MM-DD-{feature-slug}/{feature-slug}-acceptance.md"
    status: pending
```

`current_feature_index` 是 **0-based**，指向 `features` 数组中下一个要处理的元素；第一个 feature 必须是 `0`，每个 feature accepted 后加 1。展示给用户的 `Feature: N/总数` 仍使用 1-based。

### `goal-protocol.md`

从 `references/protocol.md` 复制到 roadmap 目录，并把 `{roadmap-slug}` / `{roadmap-path}` / `{roadmap-file}` / `{items-file}` 替换为本次实际值。不要替换 `<feature-slug>` 这类运行时占位；它们必须保留给 goal 会话在每个 feature 边界填写。

### `goal-features/{feature-slug}.md`

每个 feature 一份，包含：

- 对应 roadmap item
- design / checklist / design-review / review / QA / acceptance 路径
- 依赖项
- feature 性质：functional / non-functional / mixed
- 核心运行路径：功能性 feature 必填；非功能性 feature 写 none + 替代证据
- 必跑命令
- 验收证据
- 交付物
- 清洁度规则
- 失败恢复边界

---

## 自查

输出 `/goal` 前必须自查并修正：

1. roadmap items 是否 DAG，无循环依赖。
2. 每个 item 是否已有 design + checklist。
3. roadmap review 是否存在且 `status: passed`，没有 unresolved blocking finding。
4. 每个 item 是否已有 design-review 且 `status: passed`，没有 unresolved blocking finding。
5. 每份 design 是否已 `status: approved`，且 frontmatter 的 `roadmap` / `roadmap_item` 与 items.yaml 一致。
6. 每个 checklist step 是否可独立验证，且初始 `steps.status` 为 `pending`、`checks.status` 为 `pending`。
7. 每个 feature 是否有必跑命令 / 基线风险 / 交付物 / 清洁度规则。
8. 每个 goal-feature spec 是否写明 design-review / review / QA / acceptance 产物路径，以及 review blocking / QA failed 的返回路径。
9. `goal-state.yaml` 是否能断点恢复，且 `current_feature_index` 使用 0-based 语义。
10. `goal-plan.md` 是否写明 roadmap 级核心验收路径、最终聚合测试命令和非功能性替代证据策略。
11. 用户是否已明确确认 roadmap 和所有 feature design。
12. `goal-protocol.md` 是否没有把 roadmap slug 误替换进 feature 标记；`Feature:` 行必须使用 `<feature-slug>` 或真实当前 feature slug。
13. 验证命令如果依赖外部测试工具，goal-plan / goal-feature spec 是否说明真实 runner 或依赖安装方式；不能通过新增 `pytest.py`、`jest`、`go` 等同名 shim 绕过。
14. 最终审计是否能从仓库事实核验每个交付物，并会落盘到 `{roadmap-path}/goal-audit.md`。

---

## 输出给用户的 goal 指令

确认通过后，打印一条 fenced `/goal`，然后停止：

```text
/goal "执行 CodeStable roadmap 目录 .codestable/roadmap/{slug} 下的 goal 执行包。先读取 goal-protocol.md、goal-state.yaml、goal-plan.md；这是已由用户确认 roadmap 和全部 feature design 后的 goal 模式，按 goal-protocol.md 的 gate 接管规则执行。按 goal-state.yaml 的 features 顺序循环处理每个 feature：读取 goal-features/{feature-slug}.md、对应 design 和 checklist，完成 cs-feat-impl，再完成 cs-code-review；如果 review 有 blocking findings，按 review-fix 修复后重跑 cs-code-review；review passed 后完成 cs-feat-qa；如果 QA failed / blocked，按 qa-fix 修复后重跑 cs-code-review 和 cs-feat-qa；QA passed 后完成 cs-feat-accept，并更新 goal-state.yaml 与 roadmap items。每个 feature 验证通过后打印 CS_ROADMAP_GOAL_FEATURE_DONE。所有 feature 完成后，按 goal-protocol.md 做最终 roadmap 审计。只有当 CS_ROADMAP_GOAL_COMPLETE 出现在 transcript 中，且所有 feature 都已 review passed、QA passed 且 accept、最终审计通过、没有 CS_ROADMAP_GOAL_HANDOFF，本 goal 才算完成。"
```

只输出指令，不替用户执行；slash command 只能由用户粘贴触发。

---

## 完成判据

本技能阶段完成于：用户拿到可直接粘贴的 `/goal` 指令。

真正的 roadmap 完成由 goal 会话负责，必须满足：

- 所有 goal-state features 状态为 `accepted`
- roadmap items 全部 `done` 或带理由 `dropped`
- 每个 feature 有 review 报告，且无 unresolved blocking findings
- 每个 feature 有 QA 报告，且无 unresolved failed / blocked items
- 每个 feature 有 acceptance 报告
- `{roadmap-path}/goal-audit.md` 存在，记录最终聚合测试、roadmap 级核心验收路径、跳过项、re-verified / trust-prior 和结论
- architecture / requirement / roadmap 回写完成
- 最终审计通过
- 已做 learning reflection：筛出 pitfall / knowledge 候选，并建议用户确认后再运行 `cs-learn`
- 已提示用户可运行 `cs-docs-neat`，同步 `.codestable/`、README/docs、`CLAUDE.md` / `AGENTS.md` 和 agent 记忆
- transcript 打印 `CS_ROADMAP_GOAL_COMPLETE`

注意：goal 会话只自动做学习点反思和候选筛选，不自动写 `.codestable/compound/`。长期知识库归档必须由用户确认后触发 `cs-learn`，按它自己的查重、提炼、review、归档流程执行。

---

## 资源

写 `goal-protocol.md` 时读取 `references/protocol.md`。
