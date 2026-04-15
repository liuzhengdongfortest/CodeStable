---
name: easysdd-feature-design
description: Feature 工作流阶段一：起草方案 doc（三层结构+测试设计+架构关系）。触发场景："开始设计方案"、"design doc"、"准备实现 XX"。先收集代码/文档证据，再按三层模板一次性生成完整初稿（含 YAML frontmatter），用户整体 review 拍板后作为实现与验收的唯一输入。
---

# easysdd-feature-design

## 涉及的路径

> 共享路径与命名约定以根技能 `easysdd` 第二节为准。本节只补充本阶段特有信息：到本阶段，feature 目录通常已由 brainstorm 阶段创建好；若不存在则在本阶段创建。

## 你的职责

为这个功能起草一份方案 doc。要求是：先做证据化阅读与检索，再按三层模板一次性生成完整初稿（含 YAML frontmatter），最后组织用户整体 review 并迭代到拍板。

**核心原则：方案 doc 是给人扫的，不是给人读的。** 读者应该 5 分钟内抓到要点，需要细节时有地方查。

---

## 一、全局规则（先看这个）

1. **5 分钟可扫完**：方案 doc 的读者目标是快速抓要点。如果一个节超过 1 屏，就该砍或拆。
2. **术语先锁死**：所有新增术语必须做 grep 防撞车（代码 + 架构中心目录 + 所有 feature 的方案 doc）。
3. **示例优先于定义**：接口行为先用具体示例说明（API 用输入→输出，组件用 Props→渲染结果 / Events 示例），复杂时再补正式类型定义。
4. **推进按功能可见度**：先最小闭环，再叠细节；不是按代码文件顺序推进。
5. **新逻辑优先独立文件**：添加新功能时，新增的内聚逻辑单元默认创建独立文件，而不是往已有文件里追加。改动计划里每个新增逻辑单元必须标注"新建文件"或"追加到已有文件（理由）"。
6. **只保留高价值约束**：禁止重复表述同一条规则，避免噪音。一条信息只出现在它最自然的位置。
7. **流程与模板分离**：先按流程执行，再按模板写文档；不要边写边切换流程控制逻辑。

---

## 二、流程（什么时候做什么）

### 1) 触发与前置检查

启动时先完成以下检查，未通过不进入起草：

1. **需求输入是否清晰**。确认至少有用户目标、核心行为、成功标准和明确不做。
   - 缺失则先补齐；若用户自己也说不清，先走 brainstorm 阶段。
2. **是否已有同名方案 doc**。检查方案 doc 是否已存在，有重名先确认是接着改还是新建。
3. **读前置资料**。在动笔前先读：
   - `AGENTS.md`
   - 架构总入口（项目级架构权威）
   - 架构索引（项目级架构 doc 索引）
   - 与用户需求相关的既有代码和架构中心目录下的子系统架构 doc
4. **归档检索（按需）**——是否值得搜、优先搜哪些目录，以根技能 `easysdd` 第五节约束 7 为准；本阶段至少优先考虑以下目录：
   - 技巧库目录：`python easysdd/tools/search-yaml.py --dir easysdd/tricks --filter status=active --query "{feature 关键词}"`
   - 探索归档目录：`python easysdd/tools/search-yaml.py --dir easysdd/explores --query "{feature 关键词}"`
   - 知识沉淀目录：`python easysdd/tools/search-yaml.py --dir easysdd/learnings --query "{feature 关键词}"`
   - 决策归档目录：`python easysdd/tools/search-yaml.py --dir easysdd/decisions --filter status=active --query "{feature 关键词}"`
   - 已有 feature 方案：`python easysdd/tools/search-yaml.py --dir easysdd/features --filter doc_type=feature-design --query "{feature 关键词}"`

命中后优先复用，并在方案 doc 记录引用来源。

5. **断点恢复**。如果 `design.md` 已存在且有部分节内容：
   - `status=draft` 且各节基本完整 → 上次写完了还没 review，跳到整体 review 步骤
   - 部分节缺失 → 汇报"上次方案写到第 X 节，我补齐剩余节后统一给你 review"，只补缺失节，不重写已完成节

### 2) 着陆区评估

前置检查中已读过目标代码，在动笔起草前做一次快速评估：**新功能要落地的文件/模块能不能干净地接住这次改动？**

评估维度：目标文件行数、职责数量、与新功能的耦合方式。涉及前端时还需看：组件树层级是否过深、状态归属是否清晰（本地 state / props 传递 / 全局 store）。

按严重程度分流：

| 情况 | 处理方式 |
|---|---|
| 健康，直接加 | 正常推进，不额外处理 |
| 需要微重构（extract file / extract function） | 纳入第 3 节推进顺序作为**第 1 步**，scope 锁死为"只搬不改行为"，退出信号为"搬完后既有功能不变" |
| 需要架构级变更（职责重划分、模块拆合、接口重新设计） | 在第 1 节记录为**前置依赖**，建议拆成独立 feature 先解决；当前 feature 暂缓或标注"等前置完成后再推进" |

评估结论写进方案 doc 第 3 节"改动计划"的开头（见 `easysdd-feature-design/reference.md`）。如果是"健康，直接加"，不需要写——只在有动作时才记录。

### 3) 一次性起草

按下文三层模板一次性生成完整初稿，不要分批让用户先看半成品。初稿的 YAML frontmatter 里 `status` 固定写 `draft`。

### 4) 整体 review

向用户发出一次整体 review 提示。用户可以对任意部分提修改意见，你按意见修订后再次确认，直到用户明确"方案可以了"。用户明确放行后，把 YAML frontmatter 的 `status` 从 `draft` 改成 `approved`。

### 5) 生成 checklist.yaml

方案 doc 确认后，从 design.md 中提取行动清单，落盘为同目录下的 `checklist.yaml`。这份清单的生命周期以 `easysdd/reference/shared-conventions.md` 为准：本阶段负责生成，implement 只推进 `steps`，acceptance 只核对 `checks`。

`design.md` / `checklist.yaml` 的完整模板、frontmatter 示例、节锚点、提取格式见 `easysdd-feature-design/reference.md`。本阶段只保留提取原则：

- `steps`：从第 3 节"推进顺序"逐步提取，每步一条
- `checks`：从以下来源综合提取——
  - 第 1 节"明确不做"的每条 → 范围守护检查项
  - 第 2 节关键接口契约 → 接口一致性检查项
  - 第 3 节测试设计的每条测试约束 → 测试验证检查项

落盘后用 `validate-yaml.py --file {checklist.yaml 路径} --yaml-only` 校验语法。

### 6) 退出

完成退出条件核对后结束本阶段，并引导进入阶段二实现。

---

## 三、模板与格式

`design.md` / `checklist.yaml` 的完整参考已拆到 `easysdd-feature-design/reference.md`，包括：

- YAML frontmatter 示例
- 顶层节锚点要求
- `checklist.yaml` 完整格式与状态语义
- 第 0-4 节各自该写什么

本技能只保留流程约束：按该参考一次性起草完整初稿，不分批吐半成品。

---

## 四、review 提示

整体 review 提示词见 `easysdd-feature-design/reference.md`。本阶段要求仍然不变：只能发一次整体 review，不逐节拆开确认。

---

## 五、退出条件

用户整体 review 通过，且以下全部满足：

- [ ] 做过术语 grep 防撞车并记录结果
- [ ] YAML frontmatter 存在，且 `doc_type` / `feature` / `status` / `summary` / `tags` 填写完整
- [ ] 需求摘要含"不做什么"且后文无扩范围
- [ ] 记录了关键决策与被拒方案
- [ ] 每个关键接口有具体示例（API：输入→输出；组件：Props→渲染 / Events），覆盖正常 + 主要错误路径
- [ ] 示例通过注释标明了来源位置（文件路径 + 函数/组件名）
- [ ] 推进步骤 4-8 步，且每步可独立验证
- [ ] 测试设计按功能点组织，且每个功能点都包含测试约束/验证方式/关键用例骨架
- [ ] 记录了高风险实现约束
- [ ] 用户确认通过后，frontmatter 的 `status` 已更新为 `approved`
- [ ] `checklist.yaml` 已从 design.md 提取生成，且通过 `validate-yaml.py` 校验
- [ ] `checklist.yaml` 的 steps 条目数与第 3 节推进顺序一致

文件路径：方案 doc（若 feature 目录不存在则创建；同一 feature 的 design.md / checklist.yaml / acceptance.md 聚合在同一 feature 目录，目录位置见主技能 `easysdd` 第二节"目录安排"）

---

## 六、反模式（看到就停）

- ❌ 未读 `AGENTS.md` 和相关架构文档就动笔
- ❌ 术语未做防撞车检查
- ❌ 用散文描述接口行为，无具体示例
- ❌ 把契约层写成全字段百科——已有且不变的接口不要重复
- ❌ 强行画图——模块 ≤ 2 个、调用线性时不需要图
- ❌ 推进步骤过细（>8 步）
- ❌ 只给半份文档就让用户先 review
- ❌ 在需求摘要或改动计划里偷偷扩范围

---

## 七、退出后

告诉用户："方案 doc 已就绪（含测试设计），行动清单 `checklist.yaml` 已生成，下一步是阶段二：分步实现。可以触发 easysdd-feature-implement 技能。"
