---
name: cs-learn
description: 把踩过的坑或好做法沉淀成可检索的 learning 文档，两条轨道 pitfall（坑）/ knowledge（默认做法）。触发：用户说"沉淀知识"、"learning"、"把这次经验记下来"，或 acceptance / fix 收尾时推送。
---

# cs-learn

每次做 feature 或修 issue 都会留下 spec 文件。但 spec 记录的是"做了什么"和"怎么做的"，**不会记录"踩了什么坑"和"发现了什么更好的做法"**。没有沉淀的团队总在重复解决同一个问题。

两条轨道：

- **坑点轨道**（pitfall）：记录问题 / 根因 / 解法，防止下次再掉进同一个坑
- **知识轨道**（knowledge）：记录最佳实践 / 工作流改进 / 可复用模式

两者都写入 `codestable/compound/`（共享目录见 `shared-conventions.md` 第 1 节"归档类文档"）。本技能产出 frontmatter 带 `doc_type: learning`，命名 `YYYY-MM-DD-learning-{slug}.md`。

---

## 什么时候触发

| 情境 | 说明 |
|---|---|
| 完成 feature 工作流 | `cs-feat-accept` 主动问"要记录这次的学习点吗？" |
| 完成 issue 工作流 | `cs-issue-fix` 主动问"要把这个坑记录下来吗？" |
| 用户主动 | "记录一下"、"沉淀知识"、"learning"等 |
| 解决了一次性难题 | 不在 feature / issue 内但花了大量时间才解决的工程问题 |

主动推荐一句话即可，用户说"不用了"立刻跳过——重复推可能让用户觉得 AI 在加戏。

---

## 两条轨道各写什么

**坑点**：调试过的 bug / 绕过的配置陷阱 / 环境问题 / 集成失败……一切"本来应该好但没好"的经历。

**知识**：发现的最佳实践 / 工作流改进 / 架构洞见 / 可复用设计模式……一切"以后应该默认这样做"的学习。

frontmatter / 正文模板 / 完整示例见同目录 `reference.md`。

---

## 工作流阶段

### Phase 1：识别来源（自动）

从对话上下文提取：

- **来源类型**：feature 工作流 / issue 工作流 / 独立问题
- **关联产物**：feature 目录 / issue 目录路径（如有）
- **粗分轨道**：坑点 or 知识。"修了什么坏了的东西" = 坑点；"发现了什么更好做法" = 知识。两者都有就分两条

来源不明确问用户**一个问题**澄清不要猜。

### Phase 1.5：查重叠与意图分流（必做）

按 `shared-conventions.md` §6 第 5/6 条：

- 含"改 / 更新 / 补充 / 某条 learning"或指向某份旧文档 → 直接走**更新已有**
- 否则用搜索工具按 `--filter tags~=` 或 `--query` 查一遍，命中相近旧文档时把候选列给用户

**更新路径**：读旧文档 → 和用户对齐要改哪几节（常见是补新踩的坑、补当时"没找到原因"的根因）→ 起草 diff → 写回原文件 + `updated: YYYY-MM-DD`，不新建。

### Phase 2：提炼要点（一次一个问题）

**坑点轨道**问：

1. "你最开始观察到的现象是什么？"
2. "哪些解法试过但没用？"（鼓励写，失败的尝试是后人最宝贵的信息——知道哪条路不通能省下大量时间）
3. "最终怎么发现真正原因的？"
4. "下次可以更早发现吗？怎么发现？"

**知识轨道**问：

1. "你发现的这个模式，在什么情境下最有价值？"
2. "不这样做会出什么问题？"
3. "有没有不适用的反例？"

用户对某问题说"没什么"或"跳过"就跳过——宁可少一节也不用空话填充。

### Phase 3：起草 + 用户 review

AI 一次性起草完整文档（YAML frontmatter + 所有正文节）。一次性展示给用户。

### Phase 4：归档

- 新建：写入 `compound/YYYY-MM-DD-learning-{slug}.md`（日期取**归档当天**），frontmatter 带 `doc_type: learning`
- 更新：写回 Phase 1.5 定位的原文件 + `updated: YYYY-MM-DD`
- supersede：按 `shared-conventions.md` §6 第 5 条处理

### Phase 5：可发现性检查

写完检查 `AGENTS.md` / `CLAUDE.md` 有没有指引 AI 查阅 `codestable/compound/`。**没有就提示用户加一行**——不自作主张改文件。AGENTS.md 这种入口文件改动影响整个团队对 AI 的指引方式，用户该拍板。

---

## 搜索工具

> 完整语法见 `codestable/reference/tools.md`。

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

> 归档类共享规则见 `shared-conventions.md` 第 6 节。本技能特有：

1. **不混入 spec**——learning 不放进 `features/` 或 `issues/`；spec 也不放进 `compound/`
2. **只认自己的 doc_type**——只读写 `doc_type: learning`
