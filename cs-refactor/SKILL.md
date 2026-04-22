---
name: cs-refactor
description: 做代码优化时进入这套子流程——处理"行为不变、结构变"的工作（结构 / 性能 / 可读性），把单模块内部的优化从"AI 胡乱重构"改成"先扫出清单、和用户逐条确认、按方法库分步执行、每步人工放行"。触发场景：用户说"优化一下 / 重构 / 重写 / 拆一下 / 性能不行 / 代码太长"这类，且不夹带行为改动。不处理新需求（走 feature）、不处理 bug（走 issue）、不处理跨模块架构重划（走 architecture + decisions）。
---

# cs-refactor

AI 自己重构代码有两个稳定的失败模式：一是不知道模块的真实需求和约束，改出来的东西功能不等价；二是一次吞掉的范围超过上下文承载，改到后面忘了前面的约束。这条流程在"想优化"和"动手改"之间塞了一份扫描清单 + 方法库，让 AI 只接自己能稳定做对的活，剩下的老实停下来让路。

整套流程：

```
scan（扫出优化点清单）→ design（和用户定做哪几条、按什么顺序）→ apply（逐条执行，每步人工放行）
```

**核心纪律**：行为等价是底线。一旦这次动作会改变外部可观察行为，不走 refactor，走 feature（需求变）或 issue（bug 修）。

---

## Fastforward 模式（小重构走这里）

改动明显很小——单函数、单组件、1-3 处优化、有测试可自证、不需要 HUMAN 目视——走完整三阶段太重。触发 `cs-refactor-ff`：AI 直接识别、一次对齐、原地改、跑测试自证，不产出 scan / design / checklist。

触发信号：用户说"小重构"、"快速重构"、"简单优化下 XX 函数"、"直接改"、"别那么多步骤"。

什么时候**别**走 fastforward：
- 改动跨 > 1 个文件
- 预计动点超过 3 处
- 需要目视验证（前端效果、性能感知）
- 改到公开接口（要走 Parallel Change）
- 没有测试覆盖
- 跨模块

遇到这些就劝用户走标准流程。fastforward 开干后发现变复杂，切回完整流程从 scan 开始。

---

## 文件放哪儿

refactor 产物聚在 `codestable/refactors/` 下，每次独立目录：

```
codestable/
└── refactors/
    └── {YYYY-MM-DD}-{slug}/
        ├── {slug}-scan.md              ← 阶段 1 产出的优化点清单
        ├── {slug}-refactor-design.md   ← 阶段 2 的执行方案（选哪几条、顺序、验证）
        ├── {slug}-checklist.yaml       ← 阶段 2 生成，阶段 3 推进
        └── {slug}-apply-notes.md       ← 阶段 3 的执行记录（每步做了什么、验证结果、偏离）
```

目录命名和 feature / issue 一致：`YYYY-MM-DD-{英文 slug}`，日期是首次创建当天、定了不动；slug 用小写字母数字连字符，短到能一眼看出改的是什么（`user-form-split`、`export-perf` 这种）。

为什么单独开目录而不是混进 features/：refactor 产物是"代码当前状态的扫描 + 执行记录"，时效性强，价值随时间衰减；feature 产物是"这个能力为什么这样设计"，时效性弱。归档逻辑不一样，混一起后面找不到。

---

## 三个阶段

| 阶段 | 子流程 | 产出 | 谁主导 |
|---|---|---|---|
| 1 scan | 扫出优化点清单 | {slug}-scan.md | AI 扫代码 + 做前置检查，用户勾选 |
| 2 design | 定执行方案 | {slug}-refactor-design.md + {slug}-checklist.yaml | AI 起草，用户整体 review |
| 3 apply | 逐条执行 | 代码改动 + {slug}-apply-notes.md | AI 执行，每步人工放行 |

阶段之间有 checkpoint。scan 的清单用户不勾选不进 design；design 用户不放行不动代码；apply 里标了 HUMAN 验证的条目人不点头不推进下一步。

---

## 阶段 1：scan（扫出优化点清单）

### 先跑前置检查（7 条），命中就停

动笔扫之前先跑一遍前置检查。命中任何一条就**中止 scan，给出路由建议**，不要硬凑清单。7 条检查和输出格式见同目录 `reference/refusal-routing.md`。

零条合法输出——扫完真的没发现值得做的就老实说，不要凑。

### 扫描范围锁定

进 scan 前先和用户确认一件事：**这次扫哪些文件**。默认规则：

- 用户点名了具体文件/组件 → 就扫那些
- 用户说"这个页面" → 扫该页面入口组件 + 它直接 import 的内部模块，不追公共依赖
- 用户说"这个模块" → 扫该模块目录下的文件，不追出模块边界
- 范围 > 15 文件或 > 3000 行 → 触发第 6 条前置检查，请用户先缩范围

范围里要包含测试文件（用来判断第 2 条前置检查的测试覆盖情况）。

### 扫的时候看什么

按方法库的四层分类当模板在代码里找：

- **L1 行为等价迁移信号**：某个函数被很多处调用，但接口/实现要改 → 候选 Parallel Change；某整块老逻辑要被新实现替换 → 候选 Strangler Fig
- **L2 代码级重构信号**：超长函数（> 50 行 / 圈复杂度 > 10）、重复的条件片段、神秘临时变量、多层嵌套 if-else
- **L3 结构拆分信号**：组件 > 300 行、一个文件承担多件事、容器/展示混在一起、相同逻辑在多个组件里各写一份（前端）；Controller 里直接调 DB、Service 层缺失、Repository 被绕开（后端）
- **L4 性能信号**：重复计算（可 memo）、N+1 查询、列表无虚拟化/分页、事件监听无清理、大对象深响应（Vue）

方法库完整清单在同目录 `reference/methods.md`，扫描时要全量加载作为匹配表。

### 产出格式

`{slug}-scan.md` 由两部分组成：

1. **顶部总览**（一段）：扫描范围 / 发现条数 / 按分类分布 / 按风险分布 / 建议先做哪几条 / 建议慎做哪几条
2. **清单条目**（一条一块 markdown）：字段顺序和硬约束见同目录 `reference/scan-checklist-format.md`

扫完把 `{slug}-scan.md` 整份交给用户看，用户勾选要做的条目（打 ✓）、标注疑问或否决（打 ✗ 并写理由），再进阶段 2。**不要自己替用户勾选**。

---

## 阶段 2：design（定执行方案）

### 输入

- 用户勾选过的 `{slug}-scan.md`（✓ 的条目是本次要做的，✗ 的归档留痕）
- 方法库 `reference/methods.md`（每条勾选项必须映射到一个方法号 M-Ln-NN）

### 做的事

1. **排顺序**。勾选条目之间有依赖的排在前面（如 L1 的 Parallel Change 往往要先跑，L2 的提取跟在后面）。独立的按"低风险 + AI 可自证"优先，HUMAN 验证项排后面批量处理。
2. **每条补执行细节**：引用的方法号、具体步骤、前置条件、退出信号、验证责任方（AI / HUMAN）、回滚策略（出问题怎么还原）。
3. **识别前置依赖**：测试覆盖不够的条目要前置一个"补刻画测试"的步骤；改动涉及公开接口的要前置一个"搜调用方"的步骤。
4. **整体 review**：把 `{slug}-refactor-design.md` 整稿交给用户，用户放行后改 frontmatter 的 `status` 为 `approved`。
5. **抽 checklist**：从 design 抽出 `{slug}-checklist.yaml`，steps 对应执行顺序，checks 对应每步的退出信号。

### design 文件结构

```markdown
---
doc_type: refactor-design
refactor: {YYYY-MM-DD}-{slug}
status: draft | approved
scope: {扫描范围一句话}
summary: {本次要做的几条是什么，一句话}
---

# {slug} refactor design

## 1. 本次范围
- 从 scan 里勾选了哪几条（编号列出）
- 明确不做的条目（被 ✗ 的）和理由
- 预估总工作量 / 总风险档位

## 2. 前置依赖
- 测试覆盖补齐动作（如果需要）
- 调用方搜索动作（如果需要）
- 其他一次性准备

## 3. 执行顺序
按步骤列，每步一块：
- 步骤 N：{一句话动作}
- 引用方法：M-Ln-NN {方法名}
- 具体操作：{照方法库的步骤落到本项目的具体文件/函数}
- 退出信号：{AI 跑什么测试 / HUMAN 看什么页面}
- 验证责任：AI 自证 ｜ HUMAN
- 回滚：{出问题怎么还原，通常是 git revert 某步}

## 4. 风险与看点
- 高风险步骤汇总（本次 design 里风险=高的步骤单独拎出来提醒）
- 容易出错的点（比如跨步骤的数据流变化）
```

---

## 阶段 3：apply（逐条执行）

### 推进规则

1. **一步一做，不批量**。严格按 checklist 顺序，当前步不完成不开下一步。
2. **每步完成后走验证**：
   - AI 自证项：跑指定测试 / 类型检查 / lint / grep 无残留旧引用。通过了记在 apply-notes 里，继续下一步。
   - HUMAN 验证项：**停下来**，汇报"第 N 步已完成，请在 {具体页面 / 操作步骤} 下目视确认，确认后我继续"。用户不明确说"继续"就不推进。
3. **偏离当场记**：执行中发现方案里没考虑到的情况（比如有个调用方在动态 import 里），**停下来汇报，不要自己发挥**。和用户对齐后把偏离点追加到 apply-notes，必要时回阶段 2 改 design。
4. **行为等价自检**：每步结束额外问自己——"这一步有没有可能改了外部可观察行为？"。有怀疑就退回当步，不带到下一步。

### apply-notes 格式

```markdown
---
doc_type: refactor-apply-notes
refactor: {YYYY-MM-DD}-{slug}
---

# {slug} apply notes

## 步骤 1: {动作}
- 完成时间: {date}
- 改动文件: {file list}
- 验证结果: {测试输出 / HUMAN 确认语录}
- 偏离: {无 / 具体描述}

## 步骤 2: ...
```

### 全部完成后

- 跑一遍全量测试 + 类型检查 + lint
- 最后一次请用户整体目视确认（尤其是前端：打开主要页面点一圈）
- 确认通过后收尾 commit，commit message 引用 refactor 目录

---

## 退出条件

- [ ] scan 前置检查跑过，命中的已按路由引导用户，没命中的才进 scan
- [ ] `{slug}-scan.md` 用户已勾选（✓/✗），未勾选的不进 design
- [ ] `{slug}-refactor-design.md` 每条勾选项都映射到了方法库的方法号
- [ ] design 用户整体 review 通过，status=approved
- [ ] `{slug}-checklist.yaml` 已生成且通过 validate-yaml.py
- [ ] apply 阶段每步都有验证记录（AI 自证的贴日志，HUMAN 的贴用户确认语录）
- [ ] 全量测试 / 类型检查 / lint 通过
- [ ] 用户最后一次目视确认通过

---

## 容易踩的坑

- **AI 硬凑清单**：前置检查明显命中却找理由绕过，扫出一堆 "代码可以更优雅" 这种无量化问题的条目——应直接停下给路由建议
- **夹带行为改动**：在重构中间"顺便修了一个 bug / 优化了一下提示文案"——应停下，拆成独立 issue 或 feature
- **跨步骤合并动作**：为了快，一次提交里做了 2-3 步——失去"出问题单步回滚"的能力
- **把口味项列进清单**：命名偏好、引号、箭头函数 vs function——这些走 decisions，不走 refactor
- **扫一个大模块就直接动手**：> 15 文件 / > 3000 行的范围不拆就进 scan，产出一份没法决策的长清单
- **HUMAN 验证项自己跳过**：前端效果 AI 看不到，不能用 "类型检查过了" 替代人工目视
- **覆盖率不够硬上**：没测试的模块直接改，所谓"行为等价"只是口头承诺

---

## 与相邻工作流的边界

- **feature**：加新能力 / 改需求 → feature。refactor 里一旦冒出"顺便实现 X"，停下拆出去。
- **issue**：修 bug / 行为错了 → issue。refactor 里发现的 bug 记成新 issue，不在本次 PR 里偷偷修。
- **decisions**：全项目长期约束（"以后都用 composable"、"禁用 mixin"）→ decisions。refactor 执行时可以引用已有 decision 作为依据，但不产出 decision。
- **architecture**：跨模块边界重划 / 分层调整 → architecture + decisions。单次 refactor 不跨模块，跨模块的工作要拆成"更新架构文档 + 记决策 + N 个模块级 refactor"。
- **tricks / learning**：refactor 中发现可复用的手法 → tricks；踩的坑 → learning。

---

## 相关文档

- `codestable/reference/system-overview.md` — CodeStable 体系总览
- `cs-refactor-ff/SKILL.md` — 小重构超轻量通道
- `reference/scan-checklist-format.md` — scan 清单条目的字段、顺序、硬约束、反模式样本
- `reference/refusal-routing.md` — scan 前置检查 7 条 + 路由表 + 拒绝输出格式
- `reference/methods.md` — 重构方法库（L1-L4 四层分类，统一字段）
- `codestable/reference/shared-conventions.md` — 跨工作流共享口径
- 项目架构总入口 — scan 前需要翻一下，确认模块边界在哪
