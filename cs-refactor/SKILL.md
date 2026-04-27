---
name: cs-refactor
description: 代码优化的子流程入口，处理"行为不变、结构变"的工作（结构 / 性能 / 可读性），按 scan → design → apply 分步执行每步人工放行。触发：用户说"优化一下 / 重构 / 重写 / 拆一下 / 性能不行 / 代码太长"且不夹带行为改动。不处理新需求 / bug / 跨模块架构重划。
---

# cs-refactor

AI 自己重构有两个稳定失败模式：一是不知道模块真实需求和约束，改出来的东西功能不等价；二是一次吞掉的范围超过上下文承载，改到后面忘了前面的约束。这流程在"想优化"和"动手改"之间塞了扫描清单 + 方法库，让 AI 只接自己能稳定做对的活。

```
scan（扫优化点清单）→ design（和用户定做哪几条 + 顺序）→ apply（逐条执行，每步人工放行）
```

**核心纪律**：行为等价是底线。一旦会改外部可观察行为 → 不走 refactor，走 feature（需求变）或 issue（bug 修）。

---

## Fastforward 模式（小重构）

单函数 / 单组件 / 1-3 处优化 / 有测试可自证 / 不需要目视——走完整三阶段太重。触发 `cs-refactor-ff`：直接识别、一次对齐、原地改、跑测试自证，不产 scan / design / checklist。

触发："小重构"、"快速重构"、"简单优化下 XX 函数"、"直接改"、"别那么多步骤"。

**别走** ff：改动跨 > 1 文件 / 预计动点 > 3 处 / 需要目视验证 / 改公开接口（要 Parallel Change）/ 没有测试覆盖 / 跨模块。遇到劝用户走标准流程。ff 开干后发现变复杂切回完整流程从 scan 开始。

---

## 文件放哪儿

```
codestable/refactors/{YYYY-MM-DD}-{slug}/
├── {slug}-scan.md              ← 阶段 1 优化点清单
├── {slug}-refactor-design.md   ← 阶段 2 执行方案
├── {slug}-checklist.yaml       ← 阶段 2 生成，阶段 3 推进
└── {slug}-apply-notes.md       ← 阶段 3 执行记录
```

目录命名同 feature / issue。slug 短到一眼看出改的是什么（`user-form-split`、`export-perf`）。

为什么单独开目录不混进 features：refactor 产物是"代码当前状态扫描 + 执行记录"时效性强；feature 产物是"为什么这样设计"时效性弱。归档逻辑不一样。

---

## 三个阶段

| 阶段 | 产出 | 谁主导 |
|---|---|---|
| 1 scan | scan.md | AI 扫 + 前置检查，用户勾选 |
| 2 design | refactor-design.md + checklist.yaml | AI 起草，用户整体 review |
| 3 apply | 代码改动 + apply-notes.md | AI 执行，每步人工放行 |

阶段间有 checkpoint：scan 不勾选不进 design；design 不放行不动代码；apply 里 HUMAN 验证项不点头不推进下一步。

---

## 阶段 1：scan

### 先跑前置检查（7 条），命中就停

动笔扫之前先跑一遍。命中任何一条 → **中止 scan，给路由建议**，不要硬凑。7 条检查和输出格式见 `reference/refusal-routing.md`。

零条合法输出——扫完真的没发现值得做的就老实说不要凑。

### 扫描范围锁定

进 scan 前确认：**这次扫哪些文件**。默认：

- 用户点名了具体文件 / 组件 → 就扫那些
- "这个页面" → 入口组件 + 直接 import 的内部模块，不追公共依赖
- "这个模块" → 模块目录下的文件，不追出模块边界
- 范围 > 15 文件或 > 3000 行 → 触发第 6 条前置检查请用户先缩范围

范围里要包含测试文件（用来判断第 2 条前置检查的测试覆盖）。

### 扫的时候看什么

按方法库四层当模板找：

- **L1 行为等价迁移**：函数被很多处调用但接口/实现要改 → Parallel Change；整块老逻辑要被新实现替换 → Strangler Fig
- **L2 代码级重构**：超长函数（> 50 行 / 圈复杂度 > 10）、重复条件片段、神秘临时变量、多层嵌套 if-else
- **L3 结构拆分**：组件 > 300 行 / 文件承担多件事 / 容器与展示混在一起 / 相同逻辑多组件各写一份（前端）；Controller 直接调 DB / Service 缺失 / Repository 被绕开（后端）
- **L4 性能**：重复计算（可 memo）/ N+1 查询 / 列表无虚拟化或分页 / 事件监听无清理 / 大对象深响应（Vue）

完整方法库在 `reference/methods.md`，扫描时全量加载作匹配表。

### 产出格式

`{slug}-scan.md` 两部分：

1. **顶部总览**（一段）：扫描范围 / 发现条数 / 按分类分布 / 按风险分布 / 建议先做哪几条 / 慎做哪几条
2. **清单条目**（一条一块）：字段顺序和硬约束见 `reference/scan-checklist-format.md`

整份交给用户，**用户勾选 ✓ / ✗**（✗ 写理由）后进阶段 2。**不要替用户勾选**。

---

## 阶段 2：design

### 输入

- 用户勾选过的 `{slug}-scan.md`
- 方法库（每条勾选项必须映射到方法号 M-Ln-NN）

### 做的事

1. **排顺序**——勾选条目有依赖的排前（L1 的 Parallel Change 通常先跑，L2 的提取跟在后面）。独立的按"低风险 + AI 可自证"优先，HUMAN 验证项排后批量处理
2. **每条补执行细节**：方法号 / 步骤 / 前置条件 / 退出信号 / 验证责任方（AI / HUMAN）/ 回滚策略
3. **识别前置依赖**——测试覆盖不够的条目前置"补刻画测试"；改公开接口的前置"搜调用方"
4. **整体 review**：整稿交用户，放行后 `status: approved`
5. **抽 checklist**：steps 对应执行顺序，checks 对应每步退出信号

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
- 从 scan 勾选了哪几条（编号）
- 明确不做的（被 ✗ 的）和理由
- 预估总工作量 / 总风险档位

## 2. 前置依赖
- 测试覆盖补齐（如需）
- 调用方搜索（如需）
- 其他一次性准备

## 3. 执行顺序
按步骤列，每步一块：
- 步骤 N：{一句话动作}
- 引用方法：M-Ln-NN {方法名}
- 具体操作：{照方法库步骤落到本项目具体文件 / 函数}
- 退出信号：{AI 跑什么测试 / HUMAN 看什么页面}
- 验证责任：AI 自证 ｜ HUMAN
- 回滚：{出问题怎么还原，通常 git revert 某步}

## 4. 风险与看点
- 高风险步骤汇总
- 容易出错的点（跨步骤数据流变化等）
```

---

## 阶段 3：apply

### 推进规则

1. **一步一做不批量**——严格按 checklist 顺序，当前步不完成不开下一步
2. **每步完成走验证**：
   - AI 自证：跑指定测试 / 类型检查 / lint / grep 无残留旧引用。通过了记 apply-notes 继续
   - HUMAN 验证：**停下来**汇报"第 N 步已完成，请在 {具体页面 / 操作} 目视确认，确认后我继续"。用户不明确说"继续"就不推进
3. **偏离当场记**——执行中发现方案没考虑的情况（如有个调用方在动态 import 里），**停下来汇报不发挥**。和用户对齐后追加到 apply-notes，必要时回阶段 2 改 design
4. **行为等价自检**——每步结束额外问"这一步有没有可能改了外部可观察行为？" 有怀疑就退回当步

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

- 跑全量测试 + 类型检查 + lint
- 最后一次请用户整体目视确认（前端：打开主要页面点一圈）
- 确认通过后收尾 commit，message 引用 refactor 目录

---

## 退出条件

- [ ] scan 前置检查跑过，命中的已路由，没命中的才进 scan
- [ ] `{slug}-scan.md` 用户已勾选（✓/✗）
- [ ] design 每条勾选项映射到方法号
- [ ] design 用户整体 review 通过 `status: approved`
- [ ] checklist.yaml 已生成且通过 `validate-yaml.py`
- [ ] apply 每步都有验证记录（AI 自证贴日志，HUMAN 贴用户确认语录）
- [ ] 全量测试 / 类型检查 / lint 通过
- [ ] 用户最后一次目视确认通过

---

## 容易踩的坑

- **AI 硬凑清单**——前置检查明显命中却找理由绕过，扫出一堆"代码可以更优雅"无量化问题的条目
- **夹带行为改动**——在重构中间"顺便修了 bug / 优化提示文案"——拆成独立 issue 或 feature
- **跨步骤合并动作**——一次提交做 2-3 步，失去"单步回滚"能力
- **把口味项列进清单**——命名偏好 / 引号 / 箭头函数 vs function——走 decisions
- **扫大模块直接动手**——> 15 文件 / > 3000 行不拆就进 scan，产出没法决策的长清单
- **HUMAN 验证项自己跳过**——前端效果 AI 看不到，不能用"类型检查过了"替代人工目视
- **覆盖率不够硬上**——没测试的模块直接改，"行为等价"只是口头承诺

---

## 与相邻工作流的边界

- **feature**：加新能力 / 改需求。refactor 里冒出"顺便实现 X"停下拆出去
- **issue**：修 bug / 行为错了。refactor 里发现的 bug 记成新 issue 不偷偷修
- **decisions**：全项目长期约束（"以后都用 composable"、"禁用 mixin"）。refactor 可引用已有 decision 但不产出 decision
- **architecture**：跨模块边界重划 / 分层调整。单次 refactor 不跨模块；跨模块要拆成"更新架构 + 记决策 + N 个模块级 refactor"
- **tricks / learning**：refactor 中发现的手法 → tricks；踩的坑 → learning

---

## 相关文档

- `cs-refactor-ff/SKILL.md` — 小重构超轻量通道
- `reference/scan-checklist-format.md` — scan 清单条目字段 / 顺序 / 硬约束
- `reference/refusal-routing.md` — scan 前置检查 7 条 + 路由表
- `reference/methods.md` — 方法库（L1-L4 四层分类）
- `codestable/reference/shared-conventions.md` — 跨工作流共享口径
