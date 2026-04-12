---
name: easysdd-decisions
description: 决策归档子工作流——将已拍板的技术选型、架构决定、约束和规约记录为可检索文档。触发场景："记录决定"、"归档技术选型"、"ADR"、"记录这条约束"、"把规约写下来"，或 feature-design/issue-analyze 后做出重要选择时主动推送。
---

# easysdd-decisions

**决策归档子工作流** —— 把项目中已经拍板的技术选型、架构决定、长期约束和编码规约记录成可检索的永久性文档。

> "六个月后，没人记得为什么当初选了 X。有了决策文档，下次改动之前至少能先读懂背景。"

---

## 一、为什么需要决策归档

项目里有两类知识容易丢失：

1. **踩过的坑**（由 easysdd-compound 坑点轨道负责）
2. **有意做出的选择**（本工作流负责）

第二类更隐蔽——它不会触发报错，没人会注意到它消失了，但它的消失会产生严重后果：

- 新人（或六个月后的自己）不知道约束的来龙去脉，在"已经决定过的问题"上重复耗时讨论
- AI 在没有决策上下文的情况下给出"合理但与项目规约冲突"的方案
- 当约束需要修改时，找不到当初的理由，无法评估修改的影响范围

easysdd-decisions 的职责就是让每一条重要的"已经决定了"都有完整的存档：**是什么、为什么、考虑过什么替代方案、后果是什么**。

---

## 二、涉及的路径

本技能在正文里用自然语言术语引用路径（**决策归档目录**），具体目录位置的**权威定义**见主技能 `easysdd` 第二节"目录安排"。本节只说清楚文档命名规则。

**文件命名**：`YYYY-MM-DD-{slug}.md`（日期取**归档当天**，slug 为英文小写 + 连字符）。

---

## 三、四种决策类型

每条决策文档归属以下四类之一，在 YAML frontmatter 的 `category` 字段标注：

| 类型 | 适用情境 | 示例 |
|---|---|---|
| `tech-stack` | 技术/库/框架的选型 | "使用 Vite 而非 Webpack"、"状态管理用 Pinia" |
| `architecture` | 系统结构、模块划分、数据流方向 | "前后端完全分离"、"事件总线只在顶层使用" |
| `constraint` | 硬约束——某些事情**不允许**做 | "不引入 jQuery"、"所有 API 调用必须通过统一的 http 模块" |
| `convention` | 软规约——某些事情**统一这样做** | "组件命名用 PascalCase"、"副作用集中在 composables/" |

**类型的区别实践意义**：

- 查"我们用什么工具"→ `tech-stack`
- 查"系统是怎么组织的"→ `architecture`
- 查"这里为什么不能改"→ `constraint`
- 查"统一的做法是什么"→ `convention`

---

## 四、文档格式

### YAML frontmatter

```yaml
---
category: tech-stack | architecture | constraint | convention
date: YYYY-MM-DD
slug: {英文描述，连字符分隔}
status: active | superseded | deprecated
superseded-by: {被哪条决策取代，仅 status=superseded 时填写}
area: {受影响的领域，如 frontend / backend / testing / tooling / database / all}
tags: []
---
```

**status 字段语义**：

- `active`：当前有效，必须遵守
- `superseded`：已被新决策取代（填 `superseded-by` 指向新文档的 slug）
- `deprecated`：不再适用（如项目已经整体迁移，原约束自然失效）

### 正文结构

```markdown
## 背景

在什么情境下、面对什么问题或选择，需要做这个决定。

## 决定

一句话说清楚拍板的结论。（这节要短、明确、没有歧义）

## 理由

为什么选这个方案？列出最关键的 1-3 条理由，不要写成论文。

## 考虑过的替代方案

| 方案 | 为什么没选 |
|---|---|
| 方案 A | 原因 |
| 方案 B | 原因 |

（如果当时没有认真评估替代方案，明说"未做系统评估"，不要编造）

## 后果

这个决定意味着什么？什么事情变简单了，什么事情变复杂了，什么是现在必须遵守的。

## 相关文档

（可选）关联的架构文档、feature 方案、issue 分析等。
```

**宁缺毋滥原则**：用户说"没什么"的节省略，不用空话填充。`考虑过的替代方案` 和 `相关文档` 都是可选的。

---

## 五、工作流阶段

### Phase 1：识别决策（和用户对话）

用**一个问题**确认关键信息，不要给用户一张大表格：

1. "这个决定是关于什么的？（技术选型 / 架构结构 / 约束 / 规约）" → 确定 `category`
2. "这个决定是已经拍板了，还是还在讨论中？" → **本工作流只归档已拍板的决定**，讨论中的决定不归档（建议用户讨论完再来）
3. 如果用户描述不够清楚，问"当时为什么选这个而不选别的？"

### Phase 2：提炼要点（一次一个问题）

按以下顺序问，用户可以随时说"没什么"跳过某个问题：

1. "当时面对的背景或问题是什么？"
2. "决定的结论是什么？"（如果用户已经说清楚了就跳过）
3. "为什么选这个？最重要的理由是什么？"
4. "有没有考虑过其他方案？为什么没选？"（鼓励写，哪怕只是直觉）
5. "这个决定对后续工作有什么影响或约束？"

**规则**：用户对某个问题说"没什么"或"跳过"，就跳过。

### Phase 3：确认内容（AI 起草，用户 review）

- AI 根据对话起草完整文档（含 YAML frontmatter + 所有正文节）
- 一次性展示给用户 review，**不要逐节展示逐节问**
- 用户确认后写入文件；有修改则按用户意见调整再写

### Phase 4：归档

- 文件写入决策归档目录，命名 `YYYY-MM-DD-{slug}.md`
- 写完后报告完整文件路径
- 用搜索工具查是否有语义重叠的已有决策（见第六节），如有，在新文档末尾 `相关文档` 节列出来，并提示用户"这里有一条类似的决策，请确认两者是否需要合并或其中一条 supersede 另一条"

### Phase 5：相关工作流更新提示

写完后检查以下两项，有则提示用户（不自作主张改文件）：

1. `easysdd/architecture/DESIGN.md` 的"关键架构决定"节是否应该引用这条决策——如果是 `architecture` 或 `tech-stack` 类型，通常应该
2. `AGENTS.md` 的"禁止事项"或"代码规范"节是否应该追加这条约束——如果是 `constraint` 或 `convention` 类型，通常应该

---

## 六、搜索工具

`tools/search-yaml.py` 是 easysdd 提供的通用 YAML frontmatter 搜索工具（路径见主技能 `easysdd` 第二节"目录安排"）。AI 在以下场景应优先使用它。

**filter 语法**（可重复，AND 逻辑）：

- `key=value` — 字段精确匹配（大小写不敏感）
- `key~=value` — 字符串字段子串匹配；列表字段元素包含匹配

```bash
# 按类型
python tools/search-yaml.py --dir easysdd/decisions --filter category=tech-stack

# 按领域
python tools/search-yaml.py --dir easysdd/decisions --filter area=frontend

# 只看当前有效的决策
python tools/search-yaml.py --dir easysdd/decisions --filter status=active

# 按 tag（元素包含匹配）
python tools/search-yaml.py --dir easysdd/decisions --filter tags~=vite

# 全文搜索
python tools/search-yaml.py --dir easysdd/decisions --query "状态管理"

# 列出所有约束类决策
python tools/search-yaml.py --dir easysdd/decisions --filter category=constraint --filter status=active

# 完整正文输出
python tools/search-yaml.py --dir easysdd/decisions --filter category=architecture --full

# JSON 输出（适合 AI 解析）
python tools/search-yaml.py --dir easysdd/decisions --filter area=backend --json
```

**在哪个阶段用**：

| 场景 | 命令建议 |
|---|---|
| Phase 4 归档后查重叠 | `python tools/search-yaml.py --dir easysdd/decisions --query "{关键词}" --json` |
| `easysdd-feature-design` 开始前 | `python tools/search-yaml.py --dir easysdd/decisions --filter status=active --filter area={相关领域}` |
| `easysdd-issue-analyze` 根因分析前 | `python tools/search-yaml.py --dir easysdd/decisions --filter status=active --full` |
| 新人了解项目规约 | `python tools/search-yaml.py --dir easysdd/decisions --filter status=active` |

---

## 七、与其他 easysdd 工作流的关系

| 关系 | 说明 |
|---|---|
| `easysdd-feature-design` → 读 decisions | 方案设计开始前，搜索决策归档目录，确认方案不违反已有约束，并优先沿用已有技术选型 |
| `easysdd-feature-design` → 写 decisions | 设计阶段做出的重要技术选择（影响超出单个 feature），设计完成后推荐记录进决策归档 |
| `easysdd-issue-analyze` → 读 decisions | 根因分析时，有时"这里为什么这么做"的答案在决策归档里，先搜再分析 |
| `easysdd-feature-acceptance` 结束 → 可选推荐 | 验收完成后，如果这次 feature 引入了新约定或技术，推荐记录一次 |
| `easysdd-compound` vs `easysdd-decisions` | compound 记录的是"发现了什么坑 / 最佳实践"（经验性）；decisions 记录的是"我们决定了什么"（规范性）。有时两者都要写，互不替代 |
| `architecture/DESIGN.md` vs `decisions/` | DESIGN.md 是架构总览（高层次，跨模块，长期稳定）；decisions 是单条决策的完整存档（含理由和替代方案）。DESIGN.md 的"关键架构决定"节应链接到相关的 decisions 文档 |

**关于 `easysdd-feature-design` 读 decisions**：这个工作流的对应子技能**不需要显式调用** easysdd-decisions，直接搜索决策归档目录读文件即可。easysdd-decisions 只负责写入，不负责被动读取。

---

## 八、产物示例

### 技术选型示例

```markdown
---
category: tech-stack
date: 2026-04-11
slug: vite-as-bundler
status: active
area: frontend
tags: [vite, bundler, build-tool]
---

## 背景

项目启动时需要选择前端构建工具。主要候选为 Vite 和 Webpack。

## 决定

使用 Vite 作为开发和生产构建工具。

## 理由

1. 开发模式下基于原生 ESM，冷启动和热更新速度远快于 Webpack（大型项目差距更明显）
2. 配置更简洁，适合当前团队规模
3. 与 Vue 3 生态深度集成，官方支持

## 考虑过的替代方案

| 方案 | 为什么没选 |
|---|---|
| Webpack 5 | 配置复杂度高，开发启动慢，无明显优势 |
| esbuild 直接使用 | 缺乏开发服务器和 HMR 的完整支持，需额外集成工作 |

## 后果

- 所有构建相关配置集中在 `vite.config.ts`，不引入 `webpack.config.js`
- 插件选型优先考虑 Vite 插件生态，Webpack-only 插件不引入
- 如需 SSR，使用 Vite SSR 模式，不引入其他构建层
```

### 约束示例

```markdown
---
category: constraint
date: 2026-04-11
slug: no-direct-fetch-outside-http-module
status: active
area: frontend
tags: [http, fetch, api]
---

## 背景

早期代码里 `fetch` 调用散落在各个组件和 store 里，导致：错误处理不统一、鉴权逻辑需要到处复制、Mock 困难。

## 决定

所有外部 API 调用必须通过 `src/http/` 模块，禁止在组件或 store 里直接调用 `fetch` 或 `axios`。

## 理由

1. 鉴权、错误处理、日志统一在 http 模块做一次，不散落
2. 测试时 Mock 一个入口比 Mock 全局 fetch 干净

## 考虑过的替代方案

未做系统评估。约束来源于对早期散落调用的教训总结。

## 后果

- `src/http/` 是唯一的网络请求出口，新 API 接入先在这里加封装
- Code Review 时，组件里出现 `fetch(` 或 `axios.get(` 直接打回
```

---

## 九、守护规则

1. **只归档已拍板的决定**。讨论中的方案不归档；"也许我们应该用 X"不归档
2. **status=superseded 不等于删除**。被取代的决策保留原文，加 `superseded-by` 字段，正文顶部加一行"**[已取代]** 见 {新文档 slug}"
3. **不替用户写理由**。用户说不出理由的，写"未做系统评估"，不要 AI 编造看起来合理的理由
4. **不主动修改 AGENTS.md 和 DESIGN.md**。Phase 5 只提示，由用户决定是否追加——这两个文件的内容必须项目 owner 拍板
5. **跨技能一致性**：如果某条 decisions 文档与 AGENTS.md 的禁止事项描述不同，以 decisions 文档为详细版，AGENTS.md 为摘要版，两者应链接，不应矛盾
