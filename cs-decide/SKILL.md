---
name: cs-decide
description: 把已拍板的技术选型、架构决定、长期约束、编码规约记成永久性决策文档（tech-stack / architecture / constraint / convention 四种）。触发：用户说"记录决定"、"归档技术选型"、"ADR"、"记录这条约束"、"把规约写下来"，或 design / analyze 后做出重要选择。只归档已拍板的，讨论中的不归档。
---

# cs-decide

项目里"有意做出的选择"——技术选型 / 架构决定 / 长期约束 / 编码规约——特别容易丢失。它不会触发报错、没人会注意到它消失，但消失代价很具体：

- 新人（或六个月后的自己）不知道约束的来龙去脉，在"已经决定过的问题"上重复耗时讨论
- AI 没有决策上下文给出"合理但与项目规约冲突"的方案
- 约束需要修改时找不到当初的理由，无法评估修改影响

本工作流让每一条重要的"已经决定了"都有完整存档：**是什么、为什么、考虑过什么替代方案、后果是什么**。

> 共享路径与命名约定看 `codestable/reference/shared-conventions.md`。产物写入 `codestable/compound/`，命名 `YYYY-MM-DD-decision-{slug}.md`，frontmatter 带 `doc_type: decision`。

---

## 四种决策类型

每条归属四类之一（frontmatter 的 `category` 字段标注）：

| 类型 | 适用情境 | 示例 |
|---|---|---|
| `tech-stack` | 技术 / 库 / 框架的选型 | "用 Vite 而非 Webpack"、"状态管理用 Pinia" |
| `architecture` | 系统结构、模块划分、数据流方向 | "前后端完全分离"、"事件总线只在顶层使用" |
| `constraint` | 硬约束——某些事情**不允许**做 | "不引入 jQuery"、"所有 API 调用必须通过统一的 http 模块" |
| `convention` | 软规约——某些事情**统一这样做** | "组件命名用 PascalCase"、"副作用集中在 composables/" |

查询时各有用途：查"用什么工具"→ tech-stack；"系统怎么组织"→ architecture；"这里为什么不能改"→ constraint；"统一做法是什么"→ convention。

---

## 文档格式

frontmatter / 正文模板 / 示例见同目录 `reference.md`。本技能流程约束：

- `category` 只允许 `tech-stack` / `architecture` / `constraint` / `convention`
- `status` 只允许 `active` / `superseded` / `deprecated`
- "考虑过的替代方案"和"相关文档"是可选节，用户说"没什么"就省略

---

## 工作流阶段

### Phase 1：识别决策

用**一个问题**确认关键信息不要给用户大表格：

1. "这个决定关于什么？（技术选型 / 架构 / 约束 / 规约）" → 确定 `category`
2. "已经拍板还是还在讨论？" → **本工作流只归档已拍板的**，讨论中的不归档（建议讨论完再来）。理由：讨论中的方案归档，下次有人查到会以为已定了，反而误导
3. 描述不清楚问"当时为什么选这个而不选别的？"

### Phase 1.5：查重叠与意图分流（必做）

按 `shared-conventions.md` §6 第 5/6 条执行：

- 用户话里含"改 / 更新 / 推翻 / 某条决策 / 某个选型"或明确指向某份旧决策 → 直接走**更新或 supersede**。决策文档特性：**结论本身变更几乎总要 supersede**（旧结论留痕不能原地覆盖）；只补背景 / 替代方案 / 影响描述时走"更新已有条目"
- 否则用下面"搜索工具"按 category + 关键词查一遍，命中相近旧决策时把候选列给用户

**update vs supersede**：结论变了 → supersede；结论没变只补充 → update。拿不准问用户。

### Phase 2：提炼要点（一次一个问题）

用户可随时说"没什么"跳过：

1. "当时面对的背景或问题？"
2. "决定的结论是什么？"（已说清就跳过）
3. "为什么选这个？最重要的理由？"
4. "考虑过其他方案吗？为什么没选？"（鼓励写哪怕只是直觉——后人最想知道"为什么不选 X"）
5. "这个决定对后续工作有什么影响或约束？"

### Phase 3：起草 + 用户 review

AI 根据对话起草完整文档（YAML frontmatter + 所有正文节）。一次性展示给用户 review，**别逐节展示逐节问**——拿到完整版才能判断节之间逻辑是否自洽。

### Phase 4：归档

- 新建：写入 `codestable/compound/YYYY-MM-DD-decision-{slug}.md`，frontmatter 顶部带 `doc_type: decision`
- 更新：写回 Phase 1.5 定位到的原文件，frontmatter 补 `updated: YYYY-MM-DD`
- supersede：按 `shared-conventions.md` §6 第 5 条处理；旧文档 `status: superseded` + `superseded-by`

### Phase 5：相关工作流更新提示

写完检查两项有则提示用户（**不自作主张改文件**）：

1. `architecture/ARCHITECTURE.md` 的"关键架构决定"节是否应引用——`architecture` 或 `tech-stack` 通常应该
2. `AGENTS.md` 的"禁止事项"或"代码规范"节是否应追加——`constraint` 或 `convention` 通常应该

---

## 搜索工具

> 完整语法见 `codestable/reference/tools.md`。

```bash
# 列出所有当前有效的决策
python codestable/tools/search-yaml.py --dir codestable/compound --filter doc_type=decision --filter status=active

# 按类型 + 状态组合
python codestable/tools/search-yaml.py --dir codestable/compound --filter doc_type=decision --filter category=constraint --filter status=active

# 归档后查重叠
python codestable/tools/search-yaml.py --dir codestable/compound --filter doc_type=decision --query "{关键词}" --json
```

---

## 守护规则

> 归档类工作流共享守护规则（只增不删 / 宁缺毋滥 / 不替用户写 / 可发现性 / 归档后查重叠）见 `shared-conventions.md` 第 6 节。本技能特有：

1. **只归档已拍板的决定**——讨论中的方案不归档
2. **status=superseded 不等于删除**——被取代的保留原文 + `superseded-by` + 正文顶部 `**[已取代]** 见 {新文档 slug}`
3. **不替用户写理由**——用户说不出就写"未做系统评估"，不要编造（编造的理由会变成历史"事实"误导后人）
4. **不主动修改 AGENTS.md 和 ARCHITECTURE.md**——Phase 5 只提示，由用户决定
5. **跨技能一致性**——decision 和 AGENTS.md 描述不同时以 decision 为详细版、AGENTS.md 为摘要版，两者应链接不应矛盾
6. **只认自己的 doc_type**——只读写 `doc_type: decision`
