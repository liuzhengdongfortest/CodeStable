---
name: cs-trick
description: 把可复用的编程模式 / 库用法 / 技术技巧整理成处方性参考库，三种类型 pattern / library / technique。触发：用户说"记录一个技巧"、"这个用法值得记"、"tricks"、"记录库用法"，或 design / analyze 阶段发现值得沉淀的技巧时推送。
---

# cs-trick

cs-trick 是面向问题的**处方性参考库**，回答：**要做 X，经过验证的正确做法是什么？** 不需要触发事件，任何时候发现值得沉淀的模式或用法都可以直接写。

典型内容：某个设计模式在这个项目的标准写法 / 某个库的核心 API 用法 + 已知坑 / 某类操作的命令配方。

> 共享路径与命名约定看 `codestable/reference/shared-conventions.md`。产物写入 `codestable/compound/`，命名 `YYYY-MM-DD-trick-{slug}.md`，frontmatter 带 `doc_type: trick`。

---

## 三种类型

frontmatter 的 `type` 字段：

| 类型 | 适用情境 | 示例 |
|---|---|---|
| `pattern` | 设计模式 / 架构模式 / 编程惯用法 | "用 Repository 模式隔离数据访问层"、"用 Builder 构造复杂配置" |
| `library` | 某个库 / 框架的用法 / 配置方式 / 常见坑 | "Prisma 事务的正确写法"、"Pinia store 的 action 错误处理" |
| `technique` | 具体操作技巧 / 工具用法 / 命令配方 | "用 jq 从 JSON 提取嵌套字段"、"git bisect 定位引入 bug 的提交" |

查询用途：查"代码该怎么组织"→ pattern；"库 / 框架某 API 怎么用"→ library；"这类操作怎么做"→ technique。分不清选最接近的，`type` 不影响搜索可用性。

---

## 文档格式

frontmatter / 正文模板 / 长示例见同目录 `reference.md`。流程约束：

- `type` 只允许 `pattern` / `library` / `technique`
- 示例优先用项目真实代码或命令
- "何时不适用 / 已知坑 / 相关文档"是可选节，用户说"没什么"就省略

---

## 工作流阶段

### Phase 1：识别类型

最多两个问题：

1. "这是关于模式 / 结构、某个库 / 框架的用法，还是操作技巧 / 命令？" → 确定 `type`
2. "一句话说：遇到什么情况时会用到它？" → 确定 `topic`

用户描述已清楚就跳过直接进 Phase 1.5。

### Phase 1.5：查重叠与意图分流（必做）

按 `shared-conventions.md` §6 第 5/6 条：

- 含"改 / 更新 / 修订 / 补充 / 某条 trick"或指向某份旧文档 → 直接走**更新已有**，不进新建流程
- 否则用搜索工具 `--query` 查一遍 `topic`，命中相近时把候选列给用户

**更新流程**：读旧文档 → 和用户对齐改哪几节 → 跳过 Phase 2 完整代码调查（被改的节涉及的代码要重读确认未失效）→ 起草 diff 给用户 review → 写回 + `updated: YYYY-MM-DD`。

### Phase 2：代码调查（必做不可跳过）

技巧通过代码体现——**用户不贴代码不等于不需要看代码**。AI 必须主动调查代码仓。

为什么必做：没看代码就写出的"技巧"会停留在抽象层面，下次有人按这条找代码会找不到对应的真实例子，反而失去信心。

1. **根据 topic + type 搜索代码仓**——Grep 关键词（函数名 / 类名 / 库导入 / 模式特征）；搜相关文件；必要时语义搜索补充
2. **读取关键文件**——技巧实际使用 / 实现的代码位置：`library` 类找 import 和调用处；`pattern` 类找结构性代码（接口定义 / 类继承 / 组合）；`technique` 类找操作步骤对应的脚本或配置
3. **产出**——记下文件路径和关键代码片段。完全找不到（纯经验性技巧、外部工具用法）就在 Phase 3 起草时说明"本技巧暂无项目内代码实例"

补充：用户附带文件 → 仍要搜一遍代码仓确认有没有其他使用点；搜索结果为空 → 可继续但必须在文档注明；找到的代码和用户描述矛盾 → 主动跟用户确认。

### Phase 3：提炼要点（一次一个问题）

**结合 Phase 2 找到的代码**提问——不问用户已经能在代码看到的东西：

1. "标准做法是什么？"（已看到实现的直接展示理解请用户确认）
2. "为什么这样做有效？有什么原理？"
3. "什么情况下不该用它？"（可选）
4. "踩过坑或要注意的？"（可选，library 重点问）
5. "代码片段或命令示例？"（已找到实际代码就跳过，直接用真实代码作为示例）

用户说"没什么"或"跳过"就跳过，宁缺节也不用空话填充。

### Phase 4：起草 + 用户 review

AI 一次性起草完整文档（YAML frontmatter + 正文）。示例代码优先用 Phase 2 找到的真实项目代码（可精简），别凭空编写。展示给用户。

### Phase 5：归档

- 新建：写入 `compound/YYYY-MM-DD-trick-{slug}.md`，frontmatter 带 `doc_type: trick`
- 更新：写回 Phase 1.5 定位的原文件 + `updated: YYYY-MM-DD`
- supersede：按 `shared-conventions.md` §6 第 5 条处理

### Phase 6：可发现性检查

写完检查 `AGENTS.md` / `CLAUDE.md` 是否指引 AI 查阅 `codestable/compound/`。**没有就提示用户加一行**——不自作主张改文件。

---

## 搜索工具

> 完整语法见 `codestable/reference/tools.md`。

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

> 归档类共享规则见 `shared-conventions.md` 第 6 节。本技能特有：

1. **只归档已验证的做法**——"也许应该这样做"不归档；必须用户或 AI 确认过有效
2. **必须调查代码仓**——Phase 2 不可跳过。示例代码优先用项目真实代码不凭空编写
3. **不替用户写原理**——用户说不清"为什么有效"就写"原理待补充"，不编造
4. **示例优先于描述**——能用代码说清楚就用代码
5. **只认自己的 doc_type**——只读写 `doc_type: trick`
