---
name: easysdd-tricks
description: 技巧库子工作流——将可复用的编程模式、库用法、技术技巧整理为可检索文档。触发场景："记录一个技巧"、"这个用法值得记"、"tricks"、"记录库用法"。feature-design 或 issue-analyze 阶段发现值得沉淀的技巧时主动推送。
---

# easysdd-tricks

**技巧库子工作流** —— 将编程模式、库用法、技术技巧整理为面向问题的处方性文档，供 feature-design 和 issue-analyze 阶段按需检索复用。

> "碰到同一个问题第二次，应该只花五分钟——前提是第一次做完留下了记录。"

---

## 一、为什么需要技巧库

easysdd 的其他知识类工作流有各自的侧重：

- **easysdd-compound** 记录"这次工程实践踩了什么坑、学到了什么"——事件驱动、回顾性
- **easysdd-decisions** 记录"我们决定了什么、为什么"——规范性、一次性拍板

两者都不负责回答"**要做 X，应该怎么做？**"

easysdd-tricks 填这个空白：它是面向问题的**处方性参考库**，核心问题是"遇到这类问题时，经过验证的做法是什么"。不需要触发事件，任何时候发现值得沉淀的模式或用法，都可以直接写入。

典型内容：

- 某个设计模式在这个项目里的标准写法
- 某个库/框架的核心 API 用法 + 已知坑
- 某类操作（调试、部署、数据处理……）的命令配方

---

## 二、涉及的路径

本技能在正文里用自然语言术语引用路径（**技巧库目录**），具体目录位置的**权威定义**见主技能 `easysdd` 第二节"目录安排"。本节只说文档命名规则。

**文件命名**：`YYYY-MM-DD-{slug}.md`（日期取**归档当天**，slug 为英文小写 + 连字符）。

---

## 三、三种文档类型

每条技巧文档归属以下三类之一，在 YAML frontmatter 的 `type` 字段标注：

| 类型 | 适用情境 | 示例 |
|---|---|---|
| `pattern` | 设计模式、架构模式、编程惯用法 | "用 Repository 模式隔离数据访问层"、"用 Builder 模式构造复杂配置对象" |
| `library` | 某个库/框架的用法、配置方式、常见坑 | "Prisma 事务的正确写法"、"Pinia store 的 action 错误处理" |
| `technique` | 具体操作技巧、工具用法、命令配方 | "用 jq 从 JSON 里提取嵌套字段"、"git bisect 定位引入 BUG 的提交" |

**类型的区别实践意义**：

- 查"代码该怎么组织"→ `pattern`
- 查"这个库/框架的某个 API 怎么用"→ `library`
- 查"这类操作怎么做"→ `technique`

分不清楚时先选最接近的，`type` 不影响搜索的可用性。

---

## 四、文档格式

### YAML frontmatter

```yaml
---
type: pattern | library | technique
date: YYYY-MM-DD
slug: {英文描述，连字符分隔}
topic: {一句话描述这条技巧解决什么问题}
language: {可选，编程语言，如 typescript / python / bash}
framework: {可选，框架或库名，如 vue / prisma / react}
tags: []
status: active | superseded
superseded-by: {被哪条技巧取代，仅 status=superseded 时填写}
---
```

**必填字段**：`type`、`date`、`slug`、`topic`、`tags`、`status`。`language` 和 `framework` 按需加，有助于按技术栈过滤。

**status 字段语义**：

- `active`：当前推荐使用
- `superseded`：已有更好的替代方案（填 `superseded-by` 指向新文档的 slug，原文保留不删）

### 正文结构

```markdown
## 适用场景

什么情况下会遇到这个问题、有这个需求。一到两句话，让读者判断"这条记录是否和我的情况相关"。

## 做法

经过验证的具体做法。pattern 类写核心结构；library 类写最关键的 API 和配置；technique 类写步骤/命令。

## 为什么有效

原理解释。让读者理解"为什么这样做"，而不是盲目复制粘贴。

## 示例

代码片段、命令序列或 before/after 对比。（强烈推荐，跳过时说明原因）

## 何时不适用

（可选）边界条件或反例——这个技巧在哪些情况下不该用。

## 已知坑

（可选，library 类重点填）使用这个技巧时容易踩的陷阱，以及如何避免。

## 相关文档

（可选）关联的 decisions、learnings、feature 方案，或外部参考链接。
```

**宁缺毋滥原则**：`何时不适用`、`已知坑`、`相关文档` 都是可选节。用户说"没什么"就省略，不用空话填充。

---

## 五、工作流阶段

### Phase 1：识别类型（和用户对话）

用**最多两个问题**确认核心信息：

1. "这是关于模式/结构、某个库/框架的用法，还是操作技巧/命令？" → 确定 `type`
2. "一句话说：遇到什么情况时会用到它？" → 确定 `topic`

如果用户描述已经足够清楚，跳过问题直接进 Phase 2。

### Phase 2：代码调查（必做，不可跳过）

技巧是通过代码体现的——**用户不贴代码不等于不需要看代码**。AI 必须主动调查代码仓，找到技巧的实际落点。

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
   - 如果代码仓里完全找不到相关代码（纯经验性技巧、外部工具用法），在 Phase 3 起草时说明"本技巧暂无项目内代码实例"

**规则**：
- 用户附带了文件 → 仍然要搜一遍代码仓，确认有没有其他使用点或关联代码
- 搜索结果为空 → 可以继续（有些技巧确实是"将来要用"的），但必须在文档里注明
- 找到的代码和用户描述矛盾 → 主动和用户确认，不要闷头写

### Phase 3：提炼要点（一次一个问题）

按以下顺序问，用户可以随时说"没什么"跳过。**结合 Phase 2 找到的代码**来提问和补充——不要问用户已经在代码里能看到的东西：

1. "标准做法是什么？"（或"核心 API / 步骤是什么？"）——如果代码调查已经看到了实现，直接展示理解并请用户确认
2. "为什么这样做有效？有什么原理吗？"
3. "有什么反例——什么情况下不该用它？"（可选）
4. "有没有踩过坑，或者有什么要注意的？"（可选，library 类重点问）
5. "有代码片段或命令示例吗？"（如果 Phase 2 已找到实际代码，可跳过此问，直接用真实代码作为示例基础）

**规则**：用户对某个问题说"没什么"或"跳过"，就跳过。文档宁缺节也不用空话填充。

### Phase 4：确认内容（AI 起草，用户 review）

- AI 根据对话 + **Phase 2 代码调查结果**起草完整文档（含 YAML frontmatter + 所有正文节）
- 示例代码优先使用 Phase 2 找到的真实项目代码（可精简），而非凭空编写
- 一次性展示给用户 review，**不要逐节展示逐节问**
- 用户确认后写入文件；有修改则按用户意见调整再写

### Phase 5：归档

- 文件写入技巧库目录，命名 `YYYY-MM-DD-{slug}.md`
- 写完后报告完整文件路径
- 用搜索工具查是否有语义重叠的已有技巧（见第六节）。如有，在新文档末尾 `相关文档` 节列出来，并提示用户"这里有一条类似的记录，请确认是否需要合并，或者其中一条 supersede 另一条"

### Phase 6：关联推荐

写完后检查以下两项，有则**提示用户**（不自作主张改文件）：

1. 这条技巧是否应该在 `AGENTS.md` 或 `CLAUDE.md` 里加一行"遇到 X 情况，可检索技巧库"——让 AI 未来能主动检索到它
2. 如果技巧涉及某个 library 的坑，easysdd-compound 是否也应该记一条 pitfall——两者角度不同，可并存

---

## 六、搜索工具

`tools/search-yaml.py` 是 easysdd 提供的通用 YAML frontmatter 搜索工具（路径见主技能 `easysdd` 第二节"目录安排"）。AI 在以下场景应优先使用它。

**filter 语法**（可重复，AND 逻辑）：

- `key=value` — 字段精确匹配（大小写不敏感）
- `key~=value` — 字符串字段子串匹配；列表字段元素包含匹配

```bash
# 按类型
python tools/search-yaml.py --dir easysdd/tricks --filter type=pattern

# 按框架（子串匹配）
python tools/search-yaml.py --dir easysdd/tricks --filter framework~=prisma

# 按编程语言
python tools/search-yaml.py --dir easysdd/tricks --filter language=typescript

# 只看当前有效的技巧
python tools/search-yaml.py --dir easysdd/tricks --filter status=active

# 按 tag（列表元素包含匹配）
python tools/search-yaml.py --dir easysdd/tricks --filter tags~=transaction

# 全文搜索
python tools/search-yaml.py --dir easysdd/tricks --query "错误处理"

# 列出所有 library 类技巧
python tools/search-yaml.py --dir easysdd/tricks --filter type=library --filter status=active

# 完整正文输出
python tools/search-yaml.py --dir easysdd/tricks --filter type=pattern --full

# JSON 输出（适合 AI 解析）
python tools/search-yaml.py --dir easysdd/tricks --filter framework~=vue --json
```

**在哪个阶段用**：

| 场景 | 命令建议 |
|---|---|
| `easysdd-feature-design` 开始前 | `python tools/search-yaml.py --dir easysdd/tricks --filter status=active --filter tags~={相关技术}` |
| `easysdd-issue-analyze` 开始前 | `python tools/search-yaml.py --dir easysdd/tricks --filter type=library --filter framework~={相关库} --full` |
| Phase 5 归档后查重叠 | `python tools/search-yaml.py --dir easysdd/tricks --query "{关键词}" --json` |
| 按技术栈快速浏览 | `python tools/search-yaml.py --dir easysdd/tricks --filter language={语言} --filter status=active` |

---

## 七、与其他 easysdd 工作流的关系

| 关系 | 说明 |
|---|---|
| `easysdd-feature-design` → 读 tricks | 方案设计开始前，搜索技巧库，看有无相关模式或库用法可直接参考，避免重新发明轮子 |
| `easysdd-issue-analyze` → 读 tricks | 根因分析开始前，搜索技巧库，特别关注 `type=library` 文档——根因有时是库的已知误用 |
| `easysdd-tricks` vs `easysdd-compound` | compound 是"这次工作结束后，回顾学到了什么"（事件锚定、回顾性）；tricks 是"要做这类事，这是正确做法"（问题锚定、处方性）。同一次工程实践可以同时产出两类文档，互不替代 |
| `easysdd-tricks` vs `easysdd-decisions` | tricks 是可复用操作技巧（how to do X）；decisions 是一次性规范决定（we decided X must/must not happen）。同一个技术选择可以在 decisions 里存"为什么选"，在 tricks 里存"怎么正确用" |
| `easysdd-compound` 的 library 坑 → 可并存 tricks | compound 记录"踩了这个坑"（pitfall）；tricks 记录"正确用法是这样"（library）。两者角度互补，可同时存在，在各自的 `相关文档` 节互相引用 |

**关于 `easysdd-feature-design` 和 `easysdd-issue-analyze` 读 tricks**：这两个工作流的对应子技能**不需要显式调用** easysdd-tricks，直接用搜索工具读技巧库目录即可。easysdd-tricks 只负责写入，不负责被动读取。

---

## 八、产物示例

### pattern 示例

```markdown
---
type: pattern
date: 2026-04-11
slug: repository-pattern-data-access
topic: 用 Repository 模式把数据访问逻辑和业务逻辑分开，方便单测和未来替换 ORM
language: typescript
tags: [repository, orm, testability, architecture]
status: active
---

## 适用场景

业务层代码直接调用 ORM（如 Prisma），导致单测需要 mock 整个 DB 客户端，且切换 ORM 时改动范围太大。

## 做法

为每个聚合根创建一个 Repository 类，暴露业务语义的方法（`findByEmail`、`save`、`delete`），
内部封装 ORM 调用。业务层只依赖 Repository 接口，不直接导入 ORM。

```typescript
// user.repository.ts
export interface UserRepository {
  findByEmail(email: string): Promise<User | null>;
  save(user: User): Promise<User>;
}

// prisma-user.repository.ts
export class PrismaUserRepository implements UserRepository {
  constructor(private readonly db: PrismaClient) {}

  async findByEmail(email: string) {
    return this.db.user.findUnique({ where: { email } });
  }

  async save(user: User) {
    return this.db.user.upsert({ ... });
  }
}
```

## 为什么有效

业务层对 ORM 的依赖变成对接口的依赖，单测时只需提供接口的 mock 实现，
不需要真实数据库。切换 ORM 只需换 Repository 实现，业务代码不动。

## 示例

单测里：`new UserService(new InMemoryUserRepository())` 即可，无需 mock Prisma。

## 何时不适用

只有一两个查询、且明确不会写单测的小脚本——引入 Repository 层是过度设计。

## 已知坑

Repository 方法命名容易滑向"数据库动词"（`findAll`、`updateWhere`）而非业务语义
（`findActiveSubscribers`）。保持方法名对业务有意义，不要把 SQL where 子句直接翻译成方法名。


### library 示例

```markdown
---
type: library
date: 2026-04-11
slug: prisma-interactive-transaction
topic: Prisma 交互式事务的正确写法，避免死锁和事务超时
language: typescript
framework: prisma
tags: [prisma, transaction, database]
status: active
---

## 适用场景

需要在一个事务里执行多个互相依赖的数据库操作，任何一步失败则全部回滚。

## 做法

使用 `prisma.$transaction(async (tx) => { ... })` 交互式事务，
在回调内用 `tx` 而不是 `prisma` 执行所有操作。

```typescript
const result = await prisma.$transaction(async (tx) => {
  const order = await tx.order.create({ data: orderData });
  await tx.inventory.update({
    where: { productId: orderData.productId },
    data: { stock: { decrement: orderData.quantity } },
  });
  return order;
});
```

## 为什么有效

交互式事务在整个回调执行期间持有数据库事务，回调抛出异常时自动回滚。
用 `tx` 替代 `prisma` 确保所有操作在同一事务上下文里。

## 示例

见"做法"节代码片段。

## 已知坑

1. 事务超时默认 5 秒——在事务内做外部 HTTP 请求会导致超时。外部调用必须移到事务外。
2. 在事务内调用另一个使用 `prisma`（非 `tx`）的函数，该调用不在事务内，容易造成数据不一致。
   解决：把 `tx` 作为参数传进子函数。
3. 嵌套事务不支持——在 `$transaction` 回调内再次调用 `$transaction` 会报错。
```

---

## 九、守护规则

1. **只归档已验证的做法**。"也许应该这样做"不归档；文档内容必须是用户或 AI 确认过有效的
2. **必须调查代码仓**。用户没贴代码不等于不需要看——Phase 2 代码调查不可跳过。示例代码优先用项目真实代码，不凭空编写
3. **status=superseded 不等于删除**。被更好方案取代的技巧保留原文，加 `superseded-by` 字段，正文顶部加一行"**[已取代]** 见 {新文档 slug}"
3. **不替用户写原理**。用户说不清楚"为什么有效"的，写"原理待补充"，不要 AI 编造听起来合理的解释
4. **示例优先于描述**。能用代码说清楚的就用代码，不要只有文字描述
5. **不和 compound / decisions 重叠**。如果内容是"踩了什么坑"→ compound；如果内容是"我们规定必须/不能做 X"→ decisions；tricks 只存"怎么做"
7. **可发现性是交付的一部分**。写完但没人能搜到等于没写；Phase 6 的关联推荐检查不可跳过
