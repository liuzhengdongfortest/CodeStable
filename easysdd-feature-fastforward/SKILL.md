---
name: easysdd-feature-fastforward
description: Feature 快速通道——需求清晰、范围小时，写一份紧凑 design.md（含 YAML frontmatter）后直接进实现。触发场景："快速模式"、"fastforward"、"别那么多步骤"、"直接开干"。不适合跨子系统或需要术语梳理的复杂功能。
---

# easysdd-feature-fastforward

**feature 系列的快速通道**——需求清晰且范围小时，压缩掉完整 design 细化流程，只产出一份紧凑的 `design.md`，一次用户确认后直接进实现。

---

## 一、适用场景

满足以下**全部条件**才走 fastforward：

1. **需求清晰**：用户能说出"做什么、为谁、怎么算成功"，不需要发散讨论
2. **范围明确**：改动集中在少数文件或模块，不需要梳理多个子系统的对接点
3. **复杂度低**：没有复杂的状态机、并发逻辑、术语撞车风险或架构变更
4. **用户主动选择**：用户明确说"快速模式"、"fastforward"、"快点搞"、"别那么多步骤直接做"、"直接开干"等

**不适合 fastforward 的情况**（遇到就告知用户走完整 feature 工作流）：

- 涉及多个子系统的数据流向变更
- 需要引入新术语或有概念撞车风险
- 推进步骤超过 4 步
- 用户自己说不清楚边界
- 改动可能影响现有核心架构

---

## 二、涉及的路径

> 路径约定见根技能 `easysdd` 第二节（组织规则 11）。`{feature}` 格式：`YYYY-MM-DD-{英文 slug}`。

---

## 三、你的职责

用户交代需求后，**快速阅读相关代码**（必须看涉及的主要文件，不需要通读全部架构文档），然后一次性产出紧凑的 `design.md`（含 YAML frontmatter），让用户整体确认，确认后给出实现指引。

---

## 四、启动检查

1. **确认适用性**：按第一节条件判断是否适合 fastforward；不适合就主动说出原因，建议走完整流程
2. **查重**：检查 `easysdd/features/` 下是否已有同名 feature 目录——有的话先问用户是继续还是新建
3. **读代码**：Glob + Read 快速浏览用户描述中涉及的主要文件；必要时 Grep 关键词确认改动范围

不读相关代码就产出 design.md 是反模式——哪怕 fastforward 也要看主要文件。

---

## 五、design.md 结构

fastforward 的 `design.md` 比完整方案 doc 精简，但**必须包含 YAML frontmatter + 以下 4 节，一次性产出**，不分批。

### YAML frontmatter

开头必须写统一 frontmatter，便于 `search-yaml.py` 在 `features/` 下检索。必填字段:

- `doc_type`: 固定写 `feature-design`
- `feature`: 当前 feature 目录名
- `status`: 初稿写 `draft`，用户确认后改成 `approved`；被替代时写 `superseded`
- `summary`: 一句话描述本功能目标
- `tags`: 可检索标签列表，至少 2 个

推荐模板:

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

### 第 1 节：设计方案

关键设计决策，写清楚：

- 改动的主要文件和位置（代码指针：文件路径 + 函数/类型名）
- 新增的类型/接口（如有，用 TypeScript / Rust 伪代码）
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

**这是 fastforward 和普通方案 doc 的关键差异**——不变量和验收标准在这里就写好，不留占位。验收报告（`acceptance.md`）将直接从这里抽取验收点。

每条验收点必须是**可操作的步骤 + 期待结果**，不接受"功能正常运行"这种不可验证的描述。

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

简化版推进顺序，**不超过 4 步**。每步要有退出信号（怎么算这步做完）。超过 4 步意味着不适合 fastforward，需要告知用户切换到完整流程。

```markdown
## 3. 推进步骤

1. **步骤名**：改动描述 → 退出信号
2. **步骤名**：...
```

---

## 六、确认与 checklist.yaml

产出 `design.md` 后，向用户发出一次整体确认提示：

> "fastforward design.md 已就绪，请整体 review 后确认：
> - 需求摘要是否准确？明确不做的部分有没有遗漏？
> - 改动点有没有遗漏的文件或函数？
> - 验收标准能不能覆盖你期望的场景？
>
> 确认后直接进入实现阶段。"

用户可以提修改意见，修订后再次确认；用户明确说"可以了"即视为放行，并把 frontmatter 的 `status` 更新为 `approved`。

**确认后，立即从 design.md 提取行动清单，落盘为同目录下的 `checklist.yaml`**（格式见 easysdd-feature-design 技能的"checklist.yaml 格式"小节）。提取规则：

- `steps`：从第 3 节"推进步骤"逐步提取
- `checks`：从第 0 节"明确不做"项 + 第 2 节"验收标准"各条提取

落盘后用 `validate-yaml.py --file {checklist.yaml 路径} --yaml-only` 校验语法。

---

## 七、退出条件

- [ ] 第 0 节含"明确不做"（至少 1-2 条）
- [ ] YAML frontmatter 存在，且 `doc_type` / `feature` / `status` / `summary` / `tags` 填写完整
- [ ] 第 1 节每个改动点都有代码指针（文件路径 + 函数/类型名）
- [ ] 第 2 节包含功能验收 + 至少一条异常或回归检查，且每条可验证
- [ ] 第 3 节推进步骤 ≤ 4 步，每步有退出信号
- [ ] 用户明确确认
- [ ] 用户确认后，frontmatter 的 `status` 已更新为 `approved`
- [ ] `checklist.yaml` 已从 design.md 提取生成，且通过 `validate-yaml.py` 校验

**文件路径**：方案 doc 和 checklist.yaml（feature 目录不存在则创建；两者聚合在同一 feature 目录，目录位置见主技能 `easysdd` 第二节"目录安排"）

---

## 八、退出后

告诉用户："design.md 已确认，行动清单 `checklist.yaml` 已生成，直接进入实现阶段。可以触发 `easysdd-feature-implement` 技能。"

不要自己顺手开始写代码——用户确认是硬约束。

---

## 九、反模式（看到就停）

- ❌ 需求不清楚还硬走 fastforward——先问清楚，或建议走完整流程
- ❌ 不读相关代码就产出 design.md
- ❌ 第 2 节验收标准写"功能正常"、"表现符合预期"这种不可操作的描述
- ❌ 第 3 节超过 4 步还不提示切换到完整流程
- ❌ 产出后不经用户确认就开始实现
- ❌ 把 fastforward 当成"敷衍了事的借口"——紧凑不等于粗糙，代码指针和验收标准一条都不能省
