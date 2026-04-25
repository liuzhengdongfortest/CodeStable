---
name: cs-trick
description: 把可复用的编程模式 / 库用法 / 技术技巧整理成处方性参考库，三种类型 pattern / library / technique。触发：用户说"记录一个技巧"、"这个用法值得记"、"tricks"、"记录库用法"，或 design / analyze 阶段发现值得沉淀的技巧时推送。
---

# cs-trick

cs-trick 是面向问题的**处方性参考库**，回答一个问题：**要做 X，经过验证的正确做法是什么？**不需要触发事件，任何时候发现值得沉淀的模式或用法都可以直接写。

典型内容：

- 某个设计模式在这个项目里的标准写法
- 某个库 / 框架的核心 API 用法 + 已知坑
- 某类操作（调试、部署、数据处理……）的命令配方

> 共享路径与命名约定看 `codestable/reference/shared-conventions.md`。本技能的产物写入 `codestable/compound/`，文件命名 `YYYY-MM-DD-trick-{slug}.md`，frontmatter 带 `doc_type: trick`。

---

## 三种文档类型

每条技巧文档归属下面三类之一，在 frontmatter 的 `type` 字段标注：

| 类型 | 适用情境 | 示例 |
|---|---|---|
| `pattern` | 设计模式、架构模式、编程惯用法 | "用 Repository 模式隔离数据访问层"、"用 Builder 模式构造复杂配置对象" |
| `library` | 某个库 / 框架的用法、配置方式、常见坑 | "Prisma 事务的正确写法"、"Pinia store 的 action 错误处理" |
| `technique` | 具体操作技巧、工具用法、命令配方 | "用 jq 从 JSON 里提取嵌套字段"、"git bisect 定位引入 bug 的提交" |

类型在查询时各有用途：

- 查"代码该怎么组织"→ `pattern`
- 查"这个库 / 框架的某个 API 怎么用"→ `library`
- 查"这类操作怎么做"→ `technique`

分不清楚就选最接近的，`type` 不影响搜索的可用性。

---

## 文档格式

技巧文档的 frontmatter、正文模板和长示例已拆到同目录 `reference.md`。本技能只保留判断与流程规则：

- `type` 只允许 `pattern` / `library` / `technique`
- 示例优先用项目里的真实代码或命令
- `何时不适用`、`已知坑`、`相关文档` 是可选节，用户说"没什么"就省略

---

## 工作流阶段

### Phase 1：识别类型（和用户对话）

用**最多两个问题**确认核心信息：

1. "这是关于模式 / 结构、某个库 / 框架的用法，还是操作技巧 / 命令？" → 确定 `type`
2. "一句话说：遇到什么情况时会用到它？" → 确定 `topic`

用户描述已经够清楚就跳过问题直接进 Phase 1.5。

### Phase 1.5：查重叠与意图分流（必做）

按 `codestable/reference/shared-conventions.md` §6 第 5 / 6 条执行：

- 用户话里含"改 / 更新 / 修订 / 补充 / 某条 trick"或明确指向某份旧文档 → 直接走**更新已有条目**路径，不进新建流程；搜索只是确认定位到哪一条
- 否则用下面"搜索工具"里的 `--query` 查一遍 `topic`，命中语义相近的旧文档时把候选列给用户，让用户选：更新 / supersede / 确实不同主题后再走 Phase 2

**更新已有条目的流程**：直接读取旧文档 → 和用户对齐要改哪几节 → 跳过 Phase 2 完整代码调查（但被改的节涉及的代码要重读确认未失效） → 起草 diff 给用户 review → 写回原文件，补 `updated: YYYY-MM-DD`。

### Phase 2：代码调查（必做，不可跳过）

技巧是通过代码体现的——**用户不贴代码不等于不需要看代码**。AI 必须主动调查代码仓，找到技巧的实际落点。

为什么必做？没看代码就写出的"技巧"会停留在抽象层面，下次有人按这条技巧找代码会找不到对应的真实例子，反而失去信心。

1. **根据 topic 和 type 搜索代码仓**：
   - Grep 关键词（函数名、类名、库导入、模式特征）
   - 搜索相关文件（按文件名、目录结构、import 路径）
   - 必要时用语义搜索补充

2. **读取关键文件**：
   - 找到技巧实际使用或实现的代码位置，读取上下文
   - `library` 类：找到库的 import 语句和调用处
   - `pattern` 类：找到模式的结构性代码（接口定义、类继承、组合关系）
   - `technique` 类：找到操作步骤对应的脚本或配置

3. **产出**：
   - 记下找到的文件路径和关键代码片段，作为后续起草的事实基础
   - 代码仓里完全找不到相关代码（纯经验性技巧、外部工具用法）就在 Phase 3 起草时说明"本技巧暂无项目内代码实例"

补充几条情况处理：

- 用户附带了文件 → 仍然要搜一遍代码仓，确认有没有其他使用点或关联代码
- 搜索结果为空 → 可以继续（有些技巧确实是"将来要用"的），但必须在文档里注明
- 找到的代码和用户描述矛盾 → 主动跟用户确认，别闷头写

### Phase 3：提炼要点（一次一个问题）

按下面顺序问，用户可以随时说"没什么"跳过。**结合 Phase 2 找到的代码**来提问和补充——不要问用户已经能在代码里看到的东西：

1. "标准做法是什么？"（或"核心 API / 步骤是什么？"）——代码调查已经看到实现的，直接展示理解请用户确认
2. "为什么这样做有效？有什么原理吗？"
3. "有什么反例——什么情况下不该用它？"（可选）
4. "有没有踩过坑，或者有什么要注意的？"（可选，library 类重点问）
5. "有代码片段或命令示例吗？"（Phase 2 已找到实际代码就跳过此问，直接用真实代码作为示例基础）

用户对某个问题说"没什么"或"跳过"就跳过，文档宁缺节也不用空话填充。

### Phase 4：确认内容（AI 起草，用户 review）

- AI 根据对话 + **Phase 2 代码调查结果**起草完整文档（含 YAML frontmatter + 所有正文节）
- 示例代码优先用 Phase 2 找到的真实项目代码（可精简），别凭空编写
- 一次性展示给用户 review，**别逐节展示逐节问**
- 用户确认后写入文件；有修改就按用户意见调整再写

### Phase 5：归档

- 新建路径：文件写入 `codestable/compound/`，命名 `YYYY-MM-DD-trick-{slug}.md`，frontmatter 顶部带 `doc_type: trick`（见 `reference.md`）
- 更新路径：写回 Phase 1.5 定位到的原文件，frontmatter 补 `updated: YYYY-MM-DD`
- supersede 路径：按 `shared-conventions.md` §6 第 5 条处理新旧两份文件
- 写完后报告完整文件路径

### Phase 6：可发现性检查

写完后检查 `AGENTS.md` 或 `CLAUDE.md` 里是否有指引 AI 查阅 `codestable/compound/` 沉淀目录的说明。**没有就提示用户是否要加一行**——别自作主张改文件，只提示，由用户决定。

---

## 搜索工具

> 完整语法和示例见 `codestable/reference/tools.md`。本节只列 tricks 特有的典型查询。

```bash
# 按类型 + 框架筛选
python codestable/tools/search-yaml.py --dir codestable/compound --filter doc_type=trick --filter type=library --filter framework~={库名}

# 按技术栈浏览
python codestable/tools/search-yaml.py --dir codestable/compound --filter doc_type=trick --filter language=typescript --filter status=active

# 归档后查重叠
python codestable/tools/search-yaml.py --dir codestable/compound --filter doc_type=trick --query "{关键词}" --json
```

---

## 守护规则

> 归档类工作流共享守护规则（只增不删、宁缺毋滥、不替用户写、可发现性、归档后查重叠）见 `codestable/reference/shared-conventions.md` 第 6 节。本技能特有或细化规则：

1. **只归档已验证的做法**——"也许应该这样做"不归档；文档内容必须是用户或 AI 确认过有效的
2. **必须调查代码仓**——用户没贴代码不等于不需要看，Phase 2 代码调查不可跳过。示例代码优先用项目真实代码，不凭空编写
3. **不替用户写原理**——用户说不清楚"为什么有效"的写"原理待补充"，不要 AI 编造听起来合理的解释
4. **示例优先于描述**——能用代码说清楚的就用代码，不要只有文字描述
5. **只认自己的 doc_type**——只读写 `doc_type: trick` 的文档，不感知 `compound/` 目录里其他 `doc_type` 的文档
