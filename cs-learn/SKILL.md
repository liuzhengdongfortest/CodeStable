---
name: cs-learn
description: 把这次工作里踩过的坑或发现的好做法沉淀成可检索的 learning 文档，下次同类事来了 AI 和人都能查到。两条轨道：坑点轨道（pitfall）记录"本来应该好但没好"的经历——bug、配置陷阱、环境问题、集成失败；知识轨道（knowledge）记录"以后默认这样做"的发现——最佳实践、工作流改进、可复用模式。触发场景：feature-acceptance 或 issue-fix 收尾时主动推送询问，或用户说"沉淀知识"、"learning"、"document learnings"、"把这次经验记下来"。spec 记的是做了什么，learning 记的是踩了什么 / 学了什么——两者互补不替代。
---

# cs-learn

每次做 feature 或修 issue 都会留下 spec 文件——`{slug}-design.md` / `{slug}-fix-note.md` 这些。但 spec 记录的是"做了什么"和"怎么做的"，**不会记录"踩了什么坑"和"发现了什么更好的做法"**。

没有沉淀的团队总在重复解决同一个问题。第一次解决一个问题需要研究，记下来后下次几分钟就够。cs-learn 就是给每次非 trivial 的工程实践补一张"学习卡"。

两条轨道：

- **坑点轨道**（pitfall）：记录遇到的问题、根因、解法，防止下次再掉进同一个坑
- **知识轨道**（knowledge）：记录发现的最佳实践、工作流改进、可复用模式

两者都写入沉淀目录 `codestable/compound/`（与其他沉淀子技能共享一个目录，分类规则看 `codestable/reference/shared-conventions.md` 第 1 节"归档类文档"），格式统一，可被未来的 AI 和人类检索。本技能产出的文档在 frontmatter 里带 `doc_type: learning`，文件名形如 `YYYY-MM-DD-learning-{slug}.md`（日期打头、类型段固定为 `learning`），这是本技能在共享目录里的身份标识。

---

## 什么时候触发

下面任一条件满足就触发：

| 情境 | 说明 |
|---|---|
| 完成一个 feature 工作流 | `cs-feat-accept` 按 `codestable/reference/shared-conventions.md` 主动问"要记录这次的学习点吗？" |
| 完成一个 issue 工作流 | `cs-issue-fix` 按 `codestable/reference/shared-conventions.md` 主动问"要把这个坑记录下来吗？" |
| 用户主动触发 | "记录一下"、"沉淀知识"、"learning"、"document learnings" 等 |
| 解决了一次性难题 | 不在 feature / issue 工作流内，但花了大量时间才解决的工程问题 |

主动推荐时一句话即可，语气轻松。用户说"不用了"立刻跳过，不再提——重复推可能让用户觉得 AI 在加戏。

---

## 两条轨道各写什么

**坑点轨道**适用于：调试过的 bug、绕过的配置陷阱、环境问题、集成失败……一切"本来应该好但没好"的经历。

**知识轨道**适用于：发现的最佳实践、工作流改进、架构洞见、可复用的设计模式……一切"以后应该默认这样做"的学习。

两条轨道的 frontmatter、正文模板和完整示例已拆到同目录 `reference.md`。本技能正文只保留判断与流程规则。

---

## 工作流阶段

### Phase 1：识别来源（自动）

从当前对话上下文提取：

- **来源类型**：feature 工作流 / issue 工作流 / 独立问题
- **关联产物**：feature 目录路径 / issue 目录路径（如有，供文档"来源"字段引用）
- **粗分轨道**：坑点 or 知识。判断依据——"修了什么坏了的东西" = 坑点；"发现了什么更好做法" = 知识。两者都有就分两条写。

来源不明确就问用户**一个问题**澄清，不要猜。

### Phase 1.5：查重叠与意图分流（必做）

按 `codestable/reference/shared-conventions.md` §6 第 5 / 6 条执行：

- 用户话里含"改 / 更新 / 补充 / 某条 learning"或明确指向某份旧文档 → 直接走**更新已有条目**路径
- 否则用下面"搜索工具"里 `--filter tags~=` 或 `--query` 查一遍本次主题 / 组件，命中相近旧文档时把候选列给用户，让用户选：更新 / supersede / 确实不同主题

**更新路径**：读旧文档 → 和用户对齐要改哪几节（常见是补充新踩的坑、补上当时"没找到原因"的根因） → 起草 diff → 写回原文件，补 `updated: YYYY-MM-DD`，不新建文件。

### Phase 2：提炼要点（和用户对话）

一次一个问题，不要给用户一张大表格让他填。

**坑点轨道**问：

1. "你最开始观察到的现象是什么？"
2. "哪些解法试过但没用？"（鼓励写，即使觉得"没什么"——失败的尝试是后人最宝贵的信息，知道哪条路不通能省下大量时间）
3. "最终是怎么发现真正原因的？"
4. "下次可以更早发现吗？怎么发现？"

**知识轨道**问：

1. "你发现的这个模式，在什么情境下最有价值？"
2. "不这样做会出什么问题？"
3. "有没有不适用的反例？"

用户对某个问题说"没什么"或"跳过"就跳过——文档宁可少一节也不用空话填充。

### Phase 3：确认内容（AI 起草，用户 review）

- AI 起草完整的 learning 文档（含 YAML frontmatter + 所有正文节）
- 一次性展示给用户 review
- 用户确认后写入文件；有修改就按用户意见调整再写

### Phase 4：归档

- 新建路径：写入 `codestable/compound/`，文件命名 `YYYY-MM-DD-learning-{slug}.md`（日期取**归档当天**，不是问题发生当天），frontmatter 顶部带 `doc_type: learning`（见 `reference.md`）
- 更新路径：写回 Phase 1.5 定位到的原文件，frontmatter 补 `updated: YYYY-MM-DD`
- supersede 路径：按 `shared-conventions.md` §6 第 5 条处理新旧两份文件
- 写完后报告完整文件路径

### Phase 5：可发现性检查

写完后检查 `AGENTS.md` 或 `CLAUDE.md` 里有没有指引 AI 查阅 `codestable/compound/` 沉淀目录的说明。**没有就提示用户是否要加一行**——别自作主张改文件，只提示，由用户决定。理由是 AGENTS.md 这种入口文件改动影响整个团队对 AI 的指引方式，用户该拍板。

---

## 搜索工具

> 完整语法和示例见 `codestable/reference/tools.md`。本节只列 learning 特有的典型查询。

```bash
# 按轨道筛选坑点
python codestable/tools/search-yaml.py --dir codestable/compound --filter doc_type=learning --filter track=pitfall --filter severity=high

# 按组件查相关学习点
python codestable/tools/search-yaml.py --dir codestable/compound --filter doc_type=learning --filter component~={组件名}

# 归档后查重叠
python codestable/tools/search-yaml.py --dir codestable/compound --filter doc_type=learning --filter tags~={主要 tag} --json
```

---

## 守护规则

> 归档类工作流共享守护规则（只增不删、宁缺毋滥、不替用户写、可发现性、归档后查重叠）见 `codestable/reference/shared-conventions.md` 第 6 节。本技能特有规则：

1. **不混入 spec**——learning 文档不是 spec，不放进 `features/` 或 `issues/`；spec 文档也不放进 `codestable/compound/`
2. **只认自己的 doc_type**——只读写 `doc_type: learning` 的文档，不感知 `compound/` 目录里其他 doc_type 的文档
