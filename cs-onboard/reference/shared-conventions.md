# CodeStable 共享口径

本文件由 `cs-onboard` 复制到项目的 `codestable/reference/shared-conventions.md`。所有 CodeStable 子技能在运行时用**项目相对路径** `codestable/reference/shared-conventions.md` 引用本文件——这是跨子技能共享但不适合堆在单个技能里的规范的唯一权威版本。

skill 本身不共享文件系统（每个 skill 是独立安装单元），所以共享口径不能放在某个 skill 内部被别的 skill 引用。放在"工作项目"里，对所有 skill 都可达。

---

## 0. 目录结构与路径命名

onboarding 完成后，项目里应当存在如下骨架（`cs-onboard` 负责搭建）：

```
codestable/
├── requirements/          需求中心目录（"为什么要有这个能力"，只记现状）
│   └── {slug}.md          一个能力一份，扁平（由 cs-req 产出）
├── architecture/          架构中心目录（"用什么结构实现"，只记现状）
│   ├── DESIGN.md          架构总入口（索引 + 关键架构决定）
│   └── {slug}.md          子系统 / 模块架构 doc（由 cs-arch 产出）
├── roadmap/               规划层目录（"接下来打算怎么走"，独立于现状档案）
│   └── {slug}/            一个大需求一个子目录（由 cs-roadmap 产出）
│       ├── {slug}-roadmap.md      主文档（背景 / 拆解 / 排期思路）
│       ├── {slug}-items.yaml      机器可读的子 feature 清单，acceptance 回写状态
│       └── drafts/                可选，草稿 / 调研 / 讨论
├── features/              feature spec 聚合根
│   └── YYYY-MM-DD-{slug}/  每个 feature 一个目录
│       ├── {slug}-brainstorm.md  （可选，由 cs-brainstorm 判为 case 2 时产出）
│       ├── {slug}-design.md
│       ├── {slug}-checklist.yaml
│       └── {slug}-acceptance.md
├── issues/                issue spec 聚合根
│   └── YYYY-MM-DD-{slug}/  每个 issue 一个目录
│       ├── {slug}-report.md
│       ├── {slug}-analysis.md    （根因不显然时才有）
│       └── {slug}-fix-note.md
├── refactors/             refactor spec 聚合根
│   └── YYYY-MM-DD-{slug}/  每次 refactor 一个目录
│       ├── {slug}-scan.md
│       ├── {slug}-refactor-design.md
│       ├── {slug}-checklist.yaml
│       └── {slug}-apply-notes.md
├── compound/              沉淀类文档统一目录
│   └── YYYY-MM-DD-{doc_type}-{slug}.md
│                          doc_type ∈ {learning, trick, decision, explore}
├── tools/                 跨工作流共享脚本（由 onboarding 从技能包释放）
└── reference/             共享参考文档（由 onboarding 从技能包释放，即本文件所在目录）
```

### 命名规则

- 需求文档：`codestable/requirements/{slug}.md`（长效能力清单，不带日期前缀，扁平不分组）
- roadmap 目录：`codestable/roadmap/{slug}/`（一个大需求一个子目录，不带日期前缀，平铺不嵌套）
- feature 目录：`codestable/features/YYYY-MM-DD-{slug}/`，日期用创建当天
- issue 目录：`codestable/issues/YYYY-MM-DD-{slug}/`，日期用报告当天
- refactor 目录：`codestable/refactors/YYYY-MM-DD-{slug}/`，日期用首次扫描当天
- 沉淀类文档：`codestable/compound/YYYY-MM-DD-{doc_type}-{slug}.md`，日期用**归档当天**（不是问题发生当天）
- 架构文档：`codestable/architecture/{type}-{slug}.md`（长效地图，不带日期前缀）；总入口始终叫 `DESIGN.md`
- `AGENTS.md` 在项目根目录，**不在 `codestable/` 里**

### 架构 doc 的分组规则（同类聚合）

`codestable/architecture/` 下的 doc 用文件名**第一段**（首个连字符之前）作为类型标记：`ui-chat.md` 和 `ui-events.md` 同属 `ui` 类，`api-routing.md` 自成 `api` 类。所以**所有架构 doc 命名必须遵循 `{type}-{slug}.md`**——只有一份且预计长期独占的，也要带个合理的 type 段（如 `cli-entry.md` 而非 `entry.md`），否则未来同类出现时统计不到、聚合不了。

**触发条件**：某个 type 在 `codestable/architecture/` 根目录下达到或超过 **6 份**文档时（即新加第 6 份的那一次操作），把这一类全部收进同名子目录。

**收入子目录后的命名**：去掉 type 前缀。`ui-chat.md` → `ui/chat.md`、`ui-open-files-tree.md` → `ui/open-files-tree.md`。子目录里不再带 `ui-` 前缀。

**只升不降**：文档因删除回到 ≤5 份也不折回平铺，避免反复改一堆引用。

**触发时谁负责**：`cs-arch` 的 `new` / `update` 模式在 Phase 6 落盘前主动检查；命中阈值时这次操作要把"本次新加 / 改的这份 + 已有同类全部"一起搬迁，并同步改 `DESIGN.md` 里所有相关链接（搬迁本身要在 Phase 5 一并给用户 review，不偷偷做）。`check` 模式不主动搬迁，但读 `architecture/` 时若发现某 type 已 ≥6 仍平铺，在报告末尾列为观察项交给用户。

### 要改目录结构

改 `cs-onboard/reference/shared-conventions.md` 这个模板，新项目 onboarding 时会带上新版本。已有项目需要手动同步 `codestable/reference/shared-conventions.md`。

---

## 1. 共享元数据口径

### feature spec

- `{slug}-brainstorm.md` / `{slug}-design.md` / `{slug}-acceptance.md` 共用 `doc_type`、`feature`、`status`、`summary`、`tags` 这组核心字段
- 子技能只补充本阶段特有字段，不重复改写这组字段的含义
- `status` 取值各阶段不同：brainstorm = `confirmed`（落盘即确认，无 draft）；design = `draft` / `approved`；acceptance 见对应技能

### issue spec

- `{slug}-report.md` / `{slug}-analysis.md` / `{slug}-fix-note.md` 共用 `doc_type`、`issue`、`status`、`tags` 这组核心字段
- `severity`、`root_cause_type`、`path` 等属于阶段特有字段，由对应阶段按需补充

### 归档类文档

- `learning` / `trick` / `decision` / `explore` 四个子技能的产物**统一写入 `codestable/compound/` 目录**
- 每个文档必须在 frontmatter 顶部带 `doc_type` 字段（`learning` / `trick` / `decision` / `explore`），作为跨子技能的归属判定
- 文件名统一用 `YYYY-MM-DD-{doc_type}-{slug}.md`——日期打头、`doc_type` 段在中间，`ls` 按名字排序就按归档日期排好；要按类型筛就 grep 中间那段
- 各子技能在 `doc_type` 之外保留自己的专属 frontmatter（learning 的 `track`、trick 的 `type`、decision 的 `category`、explore 的 `type`）
- 各子技能只认自己的 `doc_type` 和文件名里的类型段（`YYYY-MM-DD-{doc_type}-...` 中间那段），不读不写别的子技能的文档
- `status` 一类通用字段的语义必须和本文件保持一致，不另起一套口径
- 子技能里如果需要解释状态，只保留该工作流特有的状态流，不重新定义通用语义

### 面向外部读者的文档

- `guidedoc` / `libdoc` 的 frontmatter 由各自子技能定义
- 如无特殊说明：`draft` = 待 review，`current` = 当前有效，`outdated` = 代码已变更待同步

### 写作约束

- 子技能提到字段时，优先写"本技能额外字段"或"本阶段状态变化"
- 不要把整套通用字段定义在多个技能里重复展开

---

## 2. {slug}-checklist.yaml 生命周期

- `{slug}-checklist.yaml` 是 feature 工作流的唯一执行清单
- 由 `cs-feat-design` 在 `{slug}-design.md` 确认通过后一次生成
- `cs-feat-ff` **不生成** checklist（也不写 design doc / acceptance），它是跳过 spec 流程、直接让 AI 写代码的超轻量通道，只做动手前的知识检索引导

### design 的职责

- 只负责从方案里提取 `steps` 和 `checks`
- 不预先把任何条目标成完成

### implement 的职责

- 只更新 `steps[].status`
- 状态流：`pending` → `done`
- 不改写 `checks` 的所有权和来源

### acceptance 的职责

- 只更新 `checks[].status`
- 状态流：`pending` → `passed` / `failed`
- 不回头重写 `steps`

### 写作约束

- 子技能描述 `{slug}-checklist.yaml` 时，只补充本阶段具体要读/写哪一部分
- 不重新定义整份文件的生命周期

---

## 2.5 roadmap ↔ feature 衔接协议

`codestable/roadmap/{slug}/{slug}-items.yaml` 是"规划层"和"feature 执行层"之间的唯一接口。三个技能共同读写它——**不算跨 skill 耦合**，是 skill 都读写项目共享产物，和都读写 `codestable/features/` 同理。

### items.yaml 的状态机

```
planned  → in-progress  （cs-feat-design 启动 feature 时改）
in-progress → done      （cs-feat-accept 验收完成时改）
planned  → dropped      （cs-roadmap update 模式，用户决定不做时改）
```

`done` 和 `dropped` 是终态。需要回退重做的要新加一条 slug 略改的条目，不要改终态。

### cs-roadmap 的职责

- 生成和维护 `{slug}-roadmap.md` 主文档和 `{slug}-items.yaml` 的结构
- 把 `planned` 条目改 `dropped`（用户决定放弃时）
- 不改 `in-progress` / `done` 状态——那两类跃迁由 feature 技能负责

### cs-feat-design 的职责

从 roadmap 条目起头 feature 时：

1. 在 `{slug}-design.md` frontmatter 加两个字段：`roadmap: {roadmap-slug}` + `roadmap_item: {子 feature slug}`
2. 打开 `codestable/roadmap/{roadmap-slug}/{roadmap-slug}-items.yaml`，把对应条目 `status` 改为 `in-progress`、`feature` 填为 feature 目录名（`YYYY-MM-DD-{slug}`）
3. 校验 yaml 语法

直接起 feature（不从 roadmap 来）时两个字段留空或省略，不触发任何 roadmap 写操作。

### cs-feat-accept 的职责

验收流程走到收尾时：

1. 读 `{slug}-design.md` frontmatter 的 `roadmap` / `roadmap_item` 字段
2. 字段为空 → 跳过 roadmap 回写
3. 字段有值 → 打开 `codestable/roadmap/{roadmap}/{roadmap}-items.yaml`，把 `roadmap_item` 对应条目 `status` 改为 `done`
4. 同步主文档 `{roadmap}-roadmap.md` 子 feature 清单里对应行的显示状态（保持两份一致）
5. 校验 yaml 语法

回写是**实际写文件的动作**，不是自评"应该不需要改"。验收报告里要明确记录回写结果。

### 最小闭环标记

items.yaml 每份里只有一条 `minimal_loop: true`，标记"这条做完后系统能端到端跑通最窄路径"。feature-design 启动 `minimal_loop: true` 条目时优先级最高——它是整个大需求能不能落地的早期信号。

---

## 3. 阶段收尾推荐

### feature-acceptance

收尾时按顺序判断是否要推荐：

1. `cs-learn`：沉淀经验
2. `cs-decide`：记录长期约束/选型
3. `cs-guide`：更新开发者/用户指南
4. `cs-libdoc`：更新公开 API 参考
5. `scoped-commit`

### issue-fix

收尾时按顺序判断是否要推荐：

1. `cs-learn`：记录坑点
2. `cs-decide`：如修复暴露出长期约束
3. `scoped-commit`

### 推荐动作的统一规则

- 一律一句话提示
- 用户说"不用"立刻跳过
- 推荐不是强制，不得把用户拖入新的工作流
- 上游技能负责主动提示，下游技能负责承接执行
- 不要出现下游说"应该由上游推荐"、上游却没有动作的漂移

---

## 4. 收尾提交（scoped-commit）

feature-acceptance 和 issue-fix 走完后要把本次产物提交为一个 commit。规则：

- **提交范围**：本次工作改到的代码 + 相关 spec 文档 + 本次实际更新过的架构 doc + 本次实际更新过的 roadmap items.yaml / 主文档
- **不该进这个 commit**：和本次工作无关的顺手修改；属于"下次另起一个 feature / issue"的扩大范围
- **提交前确认**：用户没明确同意就不要 `git commit`
- **commit message**：一句话说清楚"这次做了什么"，不要把 spec 目录路径贴进 message

子技能只描述本阶段的特有提交范围（比如 acceptance 要带架构 doc），通用规则看这里。

---

## 5. 归档检索规则

feature-design / issue-analyze / issue-fix 在动手前要到 `codestable/compound/` 里搜已有的沉淀：

- 总是先搜 `architecture/` 和 `compound/` 两个目录
- 在 `compound/` 里用 `doc_type` 字段按需过滤（learning / trick / decision / explore）
- 搜到的结果只作为参考输入，不盲目套用——可能已过期（`status=outdated`）或不适合当前上下文
- 搜到和当前方向冲突的 decision → 必须在方案 / 分析里正面回应"为什么仍然要这么做"或调整方向

子技能只补充本阶段的具体查询命令。完整搜索语法看 `codestable/reference/tools.md`。

---

## 6. 归档类子技能共享守护规则

`cs-learn` / `cs-trick` / `cs-decide` / `cs-explore` 四个子技能共享下面这组规则。各子技能的正文只写本技能特有反模式，通用规则看这里：

1. **只增不删**——已归档的文档除非被明确取代（`status=superseded`），否则不删除；理由丢失的成本极高
2. **宁缺毋滥**——用户说不出理由的节直接省略，不要 AI 编造听起来合理的内容
3. **不替用户写实质内容**——AI 负责起草结构和串联语言，实质结论必须来自用户或可追溯的代码证据
4. **可发现性检查**——写完后检查 `AGENTS.md` / `CLAUDE.md` 里有没有指引 AI 查阅 `codestable/compound/`，没有就**提示**用户（不替用户改）
5. **起草前先查重叠，而不是归档后**——动手写之前就用 `search-yaml.py --query` 查语义相近的旧文档。有命中就把候选列给用户，让用户在三条路径里选一条：
   - **更新已有条目**（默认优先）：沿用原文件名和原创建日期，**不新建文件**；修改正文相关节，在 frontmatter 补 `updated: YYYY-MM-DD`（归档当天）；变更超出小修的话在文末加一段"YYYY-MM-DD 更新"简述改了什么
   - **supersede 已有条目**：旧文档保留原文，把 `status` 改成 `superseded`，加 `superseded-by: {新文档文件名}`，正文顶部加一行 `**[已取代]** 见 {新文档 slug}`；然后新建文档，frontmatter 带 `supersedes: {旧文档文件名}`
   - **确实是不同主题**：直接新建，在新文档末尾 `相关文档` 节列出已有那条，说明区别
6. **识别用户意图是"改已有"还是"记新的"**——用户说"改 / 更新 / 修订 / 补充 {某条}"、明确指向某条旧文档、或话题高度重合时，默认走"更新已有条目"路径，不要闷头新建。分不清就问一句，不要猜。

各子技能只认自己的 `doc_type`，不读写别家产物。

---

## 7. 写代码时的反射检查

`cs-feat-impl` 和 `cs-issue-fix` 共用的一组代码质量反射检查。AI 默认会往"大函数 / 大文件 / god class / 处处特殊分支"这些方向漂，这一节的目的是把漂移截在发生的那一刻。

**不是阈值，是触发器**。不是"超过 N 行必须拆"——硬数字会诱发为拆而拆，把自然聚合的代码切碎。这里每一条都是"遇到 X 情况就停下来问自己"的反射动作。

| 触发场景 | 停下来问自己 |
|---|---|
| 要往一个已经很长的文件里追加代码时 | 这文件现在承担了几件事？新加的东西是已有职责的延伸，还是第 N+1 件事？是第 N+1 件就默认新建文件 |
| 要给一个已经很多方法的类加方法时 | 新方法是这个类核心职责的自然扩展，还是把这个类推向"什么都能干"？ |
| 写的函数已经超过一屏时 | 这函数在做几件事？几件事就拆 |
| 要加一个 `if (特殊情况) { 特殊处理 }` 分支时 | 是不是抽象维度选错了？正确的做法可能是把特殊路径和通用路径分成不同的函数 / 策略 / 类，而不是往现有代码里打补丁 |
| 要 copy-paste 一段代码时 | 这段代码能抽成共用的，还是只是碰巧字面相似？能抽就抽 |
| 要给一个函数加第 4+ 个参数时 | 这个函数在做的事情是不是太多了？参数列表是 API 恶化的早期信号 |
| 要新写一个"万能工具类 / helper"时 | 这个东西真的没有归属吗？还是只是因为一时想不起来放哪儿，就先堆在 util 里？ |

### 停下来之后

反射检查**只负责把问题提出来**，结论用户定。如果停下来想清楚后的动作（拆文件 / 新建文件 / 重命名 / 抽共用层）会让这次改动超出 `{slug}-checklist.yaml` 里现有步骤的范围，跟用户对齐再决定——要么纳入当前 feature / fix 的推进计划，要么记成顺手发现留到后续。

不许偷偷拆完继续写，也不许忽略信号硬冲。默认动作是停、问、再继续。