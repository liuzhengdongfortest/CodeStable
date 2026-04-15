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
| 完成一个 feature 工作流 | `easysdd-feature-acceptance` 按 `easysdd/reference/shared-conventions.md` 的收尾推荐主动问"要记录这次的学习点吗？" |
| 完成一个 issue 工作流 | `easysdd-issue-fix` 按 `easysdd/reference/shared-conventions.md` 的收尾推荐主动问"要把这个坑记录下来吗？" |
| 用户主动触发 | 用户说"记录一下"、"沉淀知识"、"compound"、"document learnings" 等 |
| 解决了一次性难题 | 不在 feature/issue 工作流内，但花了大量时间才解决的工程问题 |

**主动推荐原则**：推荐时语气轻松，一句话即可。用户说"不用了"立刻跳过，不再提。

---

## 三、两条轨道

### 坑点轨道（Pitfall Track）

适用于：调试过的 BUG、绕过的配置陷阱、环境问题、集成失败……一切"本来应该好但没好"的经历。

### 知识轨道（Knowledge Track）

适用于：发现的最佳实践、工作流改进、架构洞见、可复用的设计模式……一切"以后应该默认这样做"的学习。

两条轨道的 frontmatter、正文模板和完整示例已拆到 `easysdd-compound/reference.md`。本技能只保留判断与流程规则：坑点轨道写"本来应该好但没好"，知识轨道写"以后默认这样做"。

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

完整示例已拆到 `easysdd-compound/reference.md`。本技能正文不再嵌入长示例。

---

## 六、搜索工具

> 完整语法和示例见 `easysdd/reference/tools.md`。本节只列 compound 特有的典型查询。

```bash
# 按轨道筛选坑点
python easysdd/tools/search-yaml.py --dir easysdd/learnings --filter track=pitfall --filter severity=high

# 按组件查相关学习点
python easysdd/tools/search-yaml.py --dir easysdd/learnings --filter component~={组件名}

# 归档后查重叠
python easysdd/tools/search-yaml.py --dir easysdd/learnings --filter tags~={主要 tag} --json
```

---

## 七、与其他 easysdd 工作流的关系（含搜索工具集成）

| 关系 | 说明 |
|---|---|
| `easysdd-feature-acceptance` 结束 → 推荐 compound | 验收通过后按 `easysdd/reference/shared-conventions.md` 的收尾推荐主动提议记录 feature 中的学习点 |
| `easysdd-issue-fix` 结束 → 推荐 compound | 修复完成后按 `easysdd/reference/shared-conventions.md` 的收尾推荐主动提议把坑记录成 pitfall doc |
| `easysdd-feature-design` 读 learnings | 方案设计时主动 Grep 知识沉淀目录，查有无相关坑点或模式，避免重踩 |
| `easysdd-issue-analyze` 读 learnings | 根因分析时先搜知识沉淀目录，看是否已有相同问题的历史记录 |
| `architecture/` vs `learnings/` | `architecture/` 是项目级架构权威（长期稳定）；`learnings/` 是经验沉淀（累积式，只增不删）。两者不混 |

**关于 `easysdd-feature-design` 和 `easysdd-issue-analyze` 读 learnings**：这两个工作流的对应子技能**不需要显式调用** easysdd-compound，直接 Grep 知识沉淀目录读文件即可。easysdd-compound 只负责写，不负责读。

---

## 八、守护规则

> 归档类工作流共享守护规则（只增不删、宁缺毋滥、不替用户写、可发现性、归档后查重叠）见根技能 `easysdd` 第五节约束 10。以下为本技能特有规则：

1. **不混入 spec**。learning 文档不是 spec，不放进 `features/` 或 `issues/`；spec 文档也不放进知识沉淀目录
