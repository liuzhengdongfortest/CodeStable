---
name: easysdd-feature-fastforward
description: feature 流程的快速通道——需求清晰、范围又小时压缩掉完整 design 流程，写一份紧凑的 {slug}-design.md 经用户一次确认后直接进实现。压缩的是发散和分阶段 review，不是质量标准——代码指针、验收标准这些一条都不能省。触发场景：用户说"快速模式"、"fastforward"、"别那么多步骤"、"直接开干"。不适合跨子系统、需要梳理新术语、或推进步骤超过 4 步的复杂功能——这些情况要主动告诉用户回完整流程。
---

# easysdd-feature-fastforward

并不是每个功能都值得走完整的 brainstorm → design → implement → acceptance 四步流程。需求一句话能说清、改动就在两三个文件里、没什么术语撞车风险——这种功能硬走完整流程会让用户觉得"AI 在加戏"。fastforward 就是为这种情况留的快速通道。

但**压缩的是流程，不是质量**——代码指针、验收标准、明确不做这些一条都不能省。fastforward 不是"敷衍版的 design"，而是"省掉了发散讨论和分阶段 review 的 design"。

---

## 什么时候走 fastforward

下面几条**全部满足**才走：

1. **需求清晰**——用户能说出"做什么、为谁、怎么算成功"，不需要发散讨论
2. **范围明确**——改动集中在少数文件或模块，不需要梳理多个子系统的对接点
3. **复杂度低**——没有复杂状态机、并发逻辑、术语撞车风险或架构变更
4. **用户主动选**——用户明说"快速模式"、"fastforward"、"快点搞"、"别那么多步骤"、"直接开干"等

下面这些情况遇到就主动告诉用户回完整 feature 流程：

- 涉及多个子系统的数据流向变更
- 需要引入新术语，或有概念撞车风险
- 推进步骤超过 4 步
- 用户自己说不清楚边界
- 改动可能影响现有核心架构

为什么这几条划得这么死？fastforward 跳过的不是仪式而是"用户在多个 checkpoint 上跟你对齐方案的机会"。范围一大、概念一新，跳过这些 checkpoint 意味着实现完用户才发现你理解的不是同一回事——这时候返工的成本比走完整流程贵得多。

---

## 涉及的路径

> 共享路径与命名约定看 `easysdd/reference/shared-conventions.md` 第 0 节。本节只补充 fastforward 特有信息。

---

## 你做的事

用户交代需求后，**快速读相关代码**（必须看涉及的主要文件，不需要通读全部架构文档），然后一次性产出紧凑的 `{slug}-design.md`（含 YAML frontmatter），让用户整体确认，确认后给出实现指引。

---

## 启动检查

1. **确认适用性**——按上面那几条判断是不是适合 fastforward。不适合就主动告诉用户原因，建议走完整流程
2. **查重**——检查 `easysdd/features/` 下是不是已经有同名 feature 目录。有的话先问是继续还是新建
3. **读代码**——Glob + Read 快速浏览用户描述里涉及的主要文件；必要时 Grep 关键词确认改动范围

不读相关代码就直接产出 `{slug}-design.md` 是反模式——fastforward 也要看主要文件。原因是没读代码写出来的方案大概率跟实际项目结构对不上，省下这一步会让后面整阶段全跑偏。

---

## {slug}-design.md 结构

fastforward 的 `{slug}-design.md` 比标准方案精简，但**必须包含 YAML frontmatter + 下面 4 节，一次性产出**，不分批。

### YAML frontmatter

开头必须写统一 frontmatter，便于 `search-yaml.py` 在 `features/` 下检索。必填字段：

- `doc_type`：固定写 `feature-design`
- `feature`：当前 feature 目录名
- `status`：初稿写 `draft`，用户确认后改成 `approved`；被替代时写 `superseded`
- `summary`：一句话描述本功能目标
- `tags`：可检索标签列表，至少 2 个

模板：

```markdown
---
doc_type: feature-design
feature: 2026-04-12-export-csv
status: draft
summary: 为订单列表增加 CSV 导出能力
tags: [export, csv, orders]
---
```

### 第 0 节：需求摘要

用 2-4 句话说清楚：做什么、为谁、什么算成功、明确不做什么。

```markdown
## 0. 需求摘要

- **做什么**：...
- **为谁**：...
- **成功标准**：...
- **明确不做**：...（至少 1-2 条）
```

"明确不做"不是凑数——这一节最重要的就是它。后面验收要靠它划出范围边界，没写就等于范围开放。

### 第 1 节：设计方案

关键设计决策，写清楚：

- 改动的主要文件和位置（代码指针：文件路径 + 函数 / 类型名）
- 新增的类型 / 接口（如有，用 TypeScript / Rust 伪代码）
- 关键边界情况的处理方式

```markdown
## 1. 设计方案

### 改动点

| 文件 | 改动内容 |
|---|---|
| `path/to/file.ts` | 描述具体改动 |

### 新增类型（如有）

​```typescript
// 伪代码，字段名和类型写全
​```

### 边界情况

- 情况 A：处理方式
- 情况 B：处理方式
```

### 第 2 节：验收标准

**这是 fastforward 和标准方案 doc 的关键差异**——验收标准在这里就要写好，不留占位。`{slug}-acceptance.md` 会直接从这里抽验收点，留占位等于后面验收无据可依。

每条验收点必须是**可操作的步骤 + 期待结果**，不接受"功能正常运行"这种不可验证的描述。原因很简单：不可验证的标准等于没标准。

```markdown
## 2. 验收标准

### 功能验收

- [ ] （操作步骤）→（期待结果）
- [ ] ...

### 异常与边界

- [ ] 边界情况 X 发生时，表现为 Y
- [ ] ...

### 回归检查

- [ ] 已有功能 X 不受影响（具体说明怎么验）
```

### 第 3 节：推进步骤

简化版推进顺序，**不超过 4 步**。每步要有退出信号（怎么算这步做完）。

为什么卡 4 步？超过 4 步意味着这件事已经不"简单"了——继续走 fastforward 只会让 implement 阶段失去节奏。遇到这种情况告知用户切到完整流程。

```markdown
## 3. 推进步骤

1. **步骤名**：改动描述 → 退出信号
2. **步骤名**：...
```

---

## 用户确认与 {slug}-checklist.yaml

产出 `{slug}-design.md` 后向用户发一次整体确认提示：

> "fastforward {slug}-design.md 已就绪，请整体 review 后确认：
> - 需求摘要是否准确？明确不做的部分有没有遗漏？
> - 改动点有没有遗漏的文件或函数？
> - 验收标准能不能覆盖你期望的场景？
>
> 确认后直接进入实现阶段。"

用户可以提修改意见，修订后再次确认。用户明确说"可以了"就视为放行，把 frontmatter 的 `status` 改成 `approved`。

**确认后立即从 `{slug}-design.md` 抽行动清单，落到同目录 `{slug}-checklist.yaml`**。清单格式和生命周期看 `easysdd/reference/shared-conventions.md`，本阶段只负责初始生成。提取规则：

- `steps`：从第 3 节"推进步骤"逐步抽
- `checks`：从第 0 节"明确不做"项 + 第 2 节"验收标准"各条抽

落盘后用 `validate-yaml.py --file {slug-checklist.yaml 路径} --yaml-only` 校验语法。

---

## 退出条件

- [ ] 第 0 节含"明确不做"（至少 1-2 条）
- [ ] YAML frontmatter 存在，`doc_type` / `feature` / `status` / `summary` / `tags` 都填了
- [ ] 第 1 节每个改动点都有代码指针（文件路径 + 函数 / 类型名）
- [ ] 第 2 节包含功能验收 + 至少一条异常或回归检查，每条可验证
- [ ] 第 3 节推进步骤 ≤ 4 步，每步有退出信号
- [ ] 用户明确确认
- [ ] 用户确认后，frontmatter 的 `status` 已改成 `approved`
- [ ] `{slug}-checklist.yaml` 已从 `{slug}-design.md` 抽出生成，且通过 `validate-yaml.py` 校验

文件路径：方案 doc 和 `{slug}-checklist.yaml` 都在同一 feature 目录下；feature 目录不存在就在这一步建。位置看 `easysdd/reference/shared-conventions.md` 第 0 节。

---

## 退出后

告诉用户："{slug}-design.md 已确认，行动清单 `{slug}-checklist.yaml` 已生成，直接进入实现阶段。可以触发 `easysdd-feature-implement` 技能。"

别自己顺手开始写代码——用户确认是硬约束，理由跟标准流程一样：跨阶段无停顿地往下跑会让用户来不及把关。

---

## 容易踩的坑

- 需求不清楚还硬走 fastforward——先问清楚或建议走完整流程
- 不读相关代码就产出 `{slug}-design.md`
- 第 2 节验收标准写"功能正常"、"表现符合预期"这种不可操作的描述
- 第 3 节超过 4 步还不提示切完整流程
- 产出后没经用户确认就开始实现
- 把 fastforward 当成"敷衍了事的借口"——紧凑不等于粗糙，代码指针和验收标准一条都不能省
