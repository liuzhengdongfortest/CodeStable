---
name: easysdd-compound
description: 知识沉淀子工作流——将 feature/issue 工作后的坑点与经验提炼为可检索文档（pitfall 或 knowledge 轨道）。触发场景："沉淀知识"、"document learnings"、"归档一下"、"把这次经验记下来"，或 feature-acceptance/issue-fix 结束后主动推送。
---

# easysdd-compound

**知识沉淀子工作流** —— 将工程实践中积累的学习点提炼为可检索、可复用的文档资产。

> "第一次解决一个问题需要研究。记录下来，下次遇到只需几分钟。"

---

## 一、为什么需要知识沉淀

easysdd 通过 spec 让每次功能开发有存档，但 spec 记录的是"做了什么"，而不是"踩过什么坑"和"发现了什么更好的做法"。没有沉淀的团队总在重复解决同一个问题。

easysdd-compound 在每次非 trivial 的工程实践后补一张"学习卡"：

1. **坑点轨道**（Pitfall）：记录遇到的问题、根因、解法，防止重蹈
2. **知识轨道**（Knowledge）：记录发现的最佳实践、工作流改进、可复用模式

两者都写入知识沉淀目录（路径见 SKILL.md 第二节"目录安排"），格式统一，可被未来的 AI 和人类检索。

---

## 二、触发时机

以下任一条件满足，触发本工作流：

| 情境 | 说明 |
|---|---|
| 完成一个 feature 工作流 | `easysdd-feature-acceptance` 验收通过后，主动问"要记录这次的学习点吗？" |
| 完成一个 issue 工作流 | `easysdd-issue-fix` 修复验证后，主动问"要把这个坑记录下来吗？" |
| 用户主动触发 | 用户说"记录一下"、"沉淀知识"、"compound"、"document learnings" 等 |
| 解决了一次性难题 | 不在 feature/issue 工作流内，但花了大量时间才解决的工程问题 |

**主动推荐原则**：推荐时语气轻松，一句话即可。用户说"不用了"立刻跳过，不再提。

---

## 三、两条轨道

### 坑点轨道（Pitfall Track）

适用于：调试过的 BUG、绕过的配置陷阱、环境问题、集成失败……一切"本来应该好但没好"的经历。

**YAML frontmatter 字段**：

```yaml
---
track: pitfall
date: YYYY-MM-DD
slug: {英文描述，连字符分隔}
component: {受影响的模块/层}
severity: low | medium | high
tags: []
---
```

**正文结构**：

1. **问题**：一句话描述现象
2. **症状**：报错信息、异常行为的具体表现
3. **没用的做法**：尝试过但失败的路径（防止别人重蹈）
4. **解法**：最终生效的方案
5. **为什么有效**：根因解释，不只是"改了 X"
6. **预防**：下次如何在更早阶段发现或避免

### 知识轨道（Knowledge Track）

适用于：发现的最佳实践、工作流改进、架构洞见、可复用的设计模式……一切"以后应该默认这样做"的学习。

**YAML frontmatter 字段**：

```yaml
---
track: knowledge
date: YYYY-MM-DD
slug: {英文描述，连字符分隔}
component: {适用的模块/领域}
tags: []
---
```

**正文结构**：

1. **背景**：在什么情境下发现这条知识
2. **指导原则**：核心建议，简洁直接
3. **为什么重要**：不遵守会有什么后果
4. **何时适用**：前提条件，以及不适用的反例
5. **示例**：代码片段、配置样例，或 before/after 对比

---

## 四、工作流阶段

### Phase 1：识别来源（自动）

从当前对话上下文提取：

- **来源类型**：feature 工作流 / issue 工作流 / 独立问题
- **关联产物**：feature 目录路径 / issue 目录路径（如有，供文档"来源"字段引用）
- **粗分轨道**：坑点 or 知识（判断依据："修了什么坏了的东西" = 坑点；"发现了什么更好做法" = 知识；两者都有则分两条写）

如果来源不明确，问用户**一个问题**澄清，不要猜。

### Phase 2：提炼要点（和用户对话）

一次一个问题，不要给用户一张大表格让他填。顺序：

**坑点轨道**：
1. "你最开始观察到的现象是什么？"
2. "哪些解法试过但没用？"（鼓励写，即使觉得"没什么"）
3. "最终是怎么发现真正原因的？"
4. "下次可以更早发现吗？怎么发现？"

**知识轨道**：
1. "你发现的这个模式，在什么情境下最有价值？"
2. "不这样做会出什么问题？"
3. "有没有不适用的反例？"

**规则**：用户对某个问题说"没什么"或"跳过"，就跳过。文档宁可少一节也不用空话填充。

### Phase 3：确认内容（AI 起草，用户 review）

- AI 起草完整的 learning 文档（含 YAML frontmatter + 所有正文节）
- 一次性展示给用户 review
- 用户确认后写入文件；有修改则按用户意见调整再写

### Phase 4：归档

- 文件命名：`YYYY-MM-DD-{slug}.md`（日期取**归档当天**，不是问题发生当天）
- 写完后报告完整文件路径
- 写完后用搜索脚本查重叠（见下文"搜索工具"），如有重叠文档，在新文档末尾加一节"相关文档"列出来

### Phase 5：可发现性检查

写完后检查：`AGENTS.md` 或 `CLAUDE.md` 里是否有指引 AI 查阅知识沉淀目录的说明。如果没有，**提示用户是否要加一行**，不自作主张改文件——只提示，由用户决定。

---

## 五、产物示例

### 坑点文档示例

```markdown
---
track: pitfall
date: 2026-04-11
slug: prisma-migrate-shadow-db-permission
component: database
severity: high
tags: [prisma, migration, postgresql]
---

## 问题
Prisma migrate dev 在 CI 环境中因 shadow database 权限报错失败。

## 症状
`Error: P3014 Prisma Migrate could not create the shadow database...`

## 没用的做法
- 手动创建同名 shadow database：仍然报权限不足
- 降低数据库用户的密码策略：和权限问题无关

## 解法
在 `DATABASE_URL` 对应的 PostgreSQL 用户上授予 `CREATEDB` 权限：
`ALTER USER app_user CREATEDB;`

## 为什么有效
Prisma migrate dev 需要动态创建 shadow database 来安全地计算 migration diff，缺少 CREATEDB 权限就无法完成这步。

## 预防
在 CI 环境配置文档中添加 PostgreSQL 用户权限清单，把 CREATEDB 列为 migrate 环境的必要权限。
```

### 知识文档示例

```markdown
---
track: knowledge
date: 2026-04-11
slug: freeze-invariants-before-iterating-llm-prompts
component: ai-integration
tags: [llm, prompting, workflow]
---

## 背景
在直接修改 LLM prompt 之前没有先冻结预期行为，导致迭代过程中无法判断改动是进步还是退步。

## 指导原则
修改 LLM prompt 前，先用不变量列表（或 golden-set 测试用例）固定"正确行为的边界"，再动 prompt。

## 为什么重要
没有基准的 prompt 迭代是随机游走：改了 A 不知道有没有破坏 B。

## 何时适用
任何对 LLM prompt 做超过 2 处修改的场景。单词级别的拼写修正不需要。

## 示例
**Before**：直接改 system prompt，手动看输出感觉是否"好一些"。

**After**：先写 5 条不变量（"当用户问 X 时，输出必须包含 Y"），跑通后再改 prompt，每次改完重跑。
```

---

## 六、搜索工具

`tools/search-yaml.py` 是 easysdd 提供的通用 YAML frontmatter 搜索工具（路径见 SKILL.md 第二节"目录安排"）。AI 在以下场景应优先使用它，而不是手动 Grep。

**filter 语法**（可重复，AND 逻辑）：
- `key=value` — 字段精确匹配（大小写不敏感）
- `key~=value` — 字符串字段子串匹配；列表字段元素包含匹配

```bash
# 按轨道
python tools/search-yaml.py --dir easysdd/learnings --filter track=pitfall

# 按 tag（元素包含匹配）
python tools/search-yaml.py --dir easysdd/learnings --filter tags~=prisma

# 组合过滤（AND）
python tools/search-yaml.py --dir easysdd/learnings --filter track=pitfall --filter severity=high

# 组件子串匹配
python tools/search-yaml.py --dir easysdd/learnings --filter component~=database

# 全文搜索
python tools/search-yaml.py --dir easysdd/learnings --query "shadow database"

# 完整正文输出
python tools/search-yaml.py --dir easysdd/learnings --filter track=knowledge --full

# JSON 输出（适合 AI 解析）
python tools/search-yaml.py --dir easysdd/learnings --filter tags~=llm --json
```

**在哪个阶段用**：

| 场景 | 命令建议 |
|---|---|
| Phase 4 归档后查重叠 | `python tools/search-yaml.py --dir easysdd/learnings --filter tags~={主要 tag} --json` |
| `easysdd-feature-design` 开始前查坑点 | `python tools/search-yaml.py --dir easysdd/learnings --filter track=pitfall --filter component~={相关组件}` |
| `easysdd-issue-analyze` 根因分析前查历史 | `python tools/search-yaml.py --dir easysdd/learnings --query "{关键词}" --filter track=pitfall` |
| 列出所有 high-severity 坑点 | `python tools/search-yaml.py --dir easysdd/learnings --filter track=pitfall --filter severity=high` |

脚本无需安装额外依赖（PyYAML 可选，有则用，无则内建 fallback parser）。从项目根目录运行。

---

## 七、与其他 easysdd 工作流的关系（含搜索工具集成）

| 关系 | 说明 |
|---|---|
| `easysdd-feature-acceptance` 结束 → 推荐 compound | 验收通过后主动提议记录 feature 中的学习点 |
| `easysdd-issue-fix` 结束 → 推荐 compound | 修复完成后主动提议把坑记录成 pitfall doc |
| `easysdd-feature-design` 读 learnings | 方案设计时主动 Grep 知识沉淀目录，查有无相关坑点或模式，避免重踩 |
| `easysdd-issue-analyze` 读 learnings | 根因分析时先搜知识沉淀目录，看是否已有相同问题的历史记录 |
| `architecture/` vs `learnings/` | `architecture/` 是项目级架构权威（长期稳定）；`learnings/` 是经验沉淀（累积式，只增不删）。两者不混 |

**关于 `easysdd-feature-design` 和 `easysdd-issue-analyze` 读 learnings**：这两个工作流的对应子技能**不需要显式调用** easysdd-compound，直接 Grep 知识沉淀目录读文件即可。easysdd-compound 只负责写，不负责读。

---

## 八、守护规则

1. **不替用户写**。要点由用户说出，AI 整理成格式——不允许 AI 凭空捏造细节去填满模板
2. **宁缺毋滥**。用户说"没什么"的节就留空或省略，空话比没有更糟
3. **文档只增不删**。知识沉淀目录是累积性知识库；过时的文档加"已过时"标注，不删除
4. **不混入 spec**。learning 文档不是 spec，不放进 `features/` 或 `issues/`；spec 文档也不放进知识沉淀目录
5. **可发现性是交付的一部分**。写完文档但没人能找到等于没写；Phase 5 的检查不可跳过
