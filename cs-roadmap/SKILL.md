---
name: cs-roadmap
description: 把"大到塞不进单个 feature"的需求做成完整事前规划：概设 + 接口契约 + 子 feature 拆解清单，放在 `codestable/roadmap/{slug}/`。两种模式 new / update。触发：用户说"我想要一个 X 系统"、"帮我把这块需求拆一下"、"开一份 roadmap"，或 feature-design 阶段发现需求太大。
---

# cs-roadmap

`codestable/roadmap/` 是项目的"规划层"——每个子目录承载一块大需求，主文档由三块构成：

1. **概设**：这块大需求要怎么搭、拆成哪几个模块 / 组件、各自职责是什么
2. **架构层详设**：模块之间的接口契约、共享数据结构、跨 feature 的协议
3. **子 feature 拆解**：把上面的方案分解成一串带依赖关系的子 feature 种子，feature 流程一次消费一条

三块**一起**作为这块大需求所有子 feature 的共同约束——每条子 feature 进 `cs-feat-design` 时，roadmap 第 2 块定下的接口契约就是它的**硬约束输入**（不能违反、要改先回 roadmap update）。

**为什么 roadmap 承载架构方案，而不是放进 `architecture/`**：`cs-arch` 守"只记现状不记计划"的纯度。一块大需求的前瞻性架构方案属于"还没落地、可能还会变"的事前规划，放进 architecture 会污染那份系统地图。等 roadmap 里某条子 feature 真正落地，对应的接口由 `cs-feat-accept` 提炼回 `architecture/`——roadmap 里的方案就完成了它的过渡使命，roadmap 自身收尾归档。

**为什么单独一层**：requirements 和 architecture 记录"系统现在长什么样"（现状档案，默认只在 feature-acceptance 时跟着代码同步更新）。"接下来打算做 A、然后做 B、A 完了才能做 C"这种规划信息，以及"为这块大需求专门定的模块拆分和接口"这种事前方案，塞进那两者会把"是什么"和"打算怎么做"混起来——discussion 里查不到系统真实能力，计划改一下又得回头改两份现状文档。roadmap 独立目录，改起来不牵连现状档案。

**为什么是文件夹不是单文件**：大需求拆解过程里会产生草稿、调研笔记、方案对比、白板照片转述这类材料，塞进一份 md 会变得很乱、又舍不得删。给每个 roadmap 一个子目录，主文档负责对外口径，旁边 `drafts/` 随便堆。

> 共享路径与命名约定看 `codestable/reference/shared-conventions.md`。主文档和 items 清单的完整模板看同目录 `reference.md`。

---

## 适用场景

- 用户描述了一个"一眼看出做不完"的大需求（"加个权限系统"、"做一套通知中心"、"接入 SSO")，塞进单个 feature 不合适
- 从 `cs-brainstorm` 判为 case 3 之后移交过来，本技能接着做拆解（brainstorm 只做分诊，不做拆解）
- 已有 roadmap 需要加新子 feature、改依赖关系、调整顺序、标废弃
- feature-design 阶段发现本次要做的事实际是多个 feature 的集合，需要先退回来拆

不适用：

- 单个 feature 能装下的需求 → 直接 `cs-feat`
- 用户要描述一个能力"是什么、边界在哪" → `cs-req`
- 用户要描述系统"结构怎么搭" → `cs-arch`
- 用户要拍板一条长期规约 / 选型 → `cs-decide`

---

## 模式分流

启动时二选一——AI 根据用户说的话自动判断：

| 用户说什么 | 模式 |
|---|---|
| "帮我拆一下 X 需求"、"开一份 X 的 roadmap"、"我想要一个 X 系统" | `new` |
| "往 {已有 roadmap} 里加一个子 feature"、"重排 {roadmap} 的顺序"、"把 {某条} 标 drop" | `update` |

判断不出来就问用户一句，不要硬猜。

---

## 单目标规则

每次只动一份 roadmap。用户一次扔出两个"我想要 X 和 Y"，先选一个做，另一个下次。理由同 requirements / architecture——一次吐多份 AI 稿用户 review 不过来。

---

## 目录结构

```
codestable/roadmap/{slug}/
├── {slug}-roadmap.md       # 主文档：背景 / 范围 / 模块拆分（概设）/ 接口契约（架构层详设）
│                           #         / 子 feature 清单 / 排期思路
├── {slug}-items.yaml       # 机器可读清单（feature-design 读、feature-acceptance 回写）
└── drafts/                 # 可选，调研 / 讨论 / 草稿
```

- `{slug}` 小写字母、数字、连字符，和大需求的 slug 一致（如 `permission-system`、`notification-center`）
- 平铺，每个大需求一个子目录，不嵌套 epic / sub-epic
- `drafts/` 按需建，里面内容只服务起草过程，AI 不强制归档

---

## 工作流

### Phase 1：锁定目标

- 模式（`new` / `update`）
- 目标（new：新 slug + 一句话大需求描述；update：已有 roadmap 路径）
- 本次覆盖范围（整份起草 / 只加几条 / 只重排顺序）

**slug 收敛**：new 模式下用户给的"权限系统"、"加个通知功能"，先敲定一个英文 slug。命名风格参考现有 requirements 和 architecture doc 的 slug 习惯。

### Phase 2：读取材料

共同必读：

- `AGENTS.md`
- 用户提供的素材（口述、产品想法、白板转述、相关 issue）
- `codestable/roadmap/` 下其他 roadmap（防止和已有大需求重复或冲突）
- `codestable/requirements/` 相关 req doc（这块能力的需求写下来没？写了的话拆解要对齐）
- `codestable/architecture/` 相关 doc（系统现在长什么样，影响拆解顺序）

按情况读：

- 相关的 compound 沉淀（decision / explore / learning）：
  ```bash
  python codestable/tools/search-yaml.py --dir codestable/compound --query "{大需求关键词}"
  ```
- 已有 feature 方案里和这块相关的（可能已经有人做了一部分）

**update 模式额外必读**：当前 roadmap 主文档全文 + items.yaml 当前状态 + 已启动 / 已完成的子 feature 的 design 和 acceptance 报告。

### Phase 3：拆解与起草

按 `reference.md` 的"主文档结构"和"items.yaml 格式"写出**完整初稿**，不分批吐半成品。

拆解的判断纪律：

0. **先做架构方案再拆 feature**——不要直接跳到"分成几个任务"。顺序是：先想清楚这块大需求拆成哪几个模块（概设，写进主文档第 3 节）→ 再想清楚模块之间通过什么接口 / 数据结构 / 协议交互（架构层详设，写进第 4 节）→ 最后才把方案分解成子 feature（第 5 节）。**架构方案不清楚就硬拆 feature，结果是每个 feature 各自重新发明轮子、接口对不齐**
1. **接口契约要写到 feature 可以拿来当硬约束的程度**——不是"两边商量"，而是函数签名 / 数据结构 / 协议字段 / 错误码这一级。讲不到这一级就回去想清楚再写。如果本大需求确实没有跨模块接口（比如纯前端样式调整），就在第 4 节明确写"无跨模块接口"
2. **每条子 feature 要能当作一次独立 feature 流程跑完**——能单独写 design、单独实现、单独验收。跑不下来说明颗粒度不对，继续拆或合并
3. **依赖图要是 DAG**——A 依赖 B 就写清楚，别写循环依赖
4. **依赖关系要有具体理由**——"B 依赖 A，因为 A 提供 XX 表结构" 而不是 "B 依赖 A，因为 A 先做"
5. **先列一条最小闭环**——整个大需求里，哪条子 feature 做完后能端到端跑通最窄的一条路径？标成第一条。后续都在这条基础上叠
6. **明确不做的边界**——用户脑子里的"权限系统"可能包括审计日志 / 数据脱敏，如果本 roadmap 不打算覆盖就写进"明确不做"
7. **不替用户决定优先级**——子 feature 之间的先后顺序除了技术依赖之外，还有产品优先级。技术依赖之外的排序要让用户拍板，不要 AI 自作主张

### Phase 4：自查清单

用户 review 前自己先跑一遍，汇报处理结果：

1. **模块拆分讲清了吗**？每个模块的职责能一句话说出来，模块边界讲得清吗？
2. **接口契约写到可执行程度了吗**？函数签名 / 数据结构 / 协议字段 / 错误码这一级，feature-design 看完不需要再回来问就能直接照着实现？写不到这一级是没想清楚的信号
3. **每条子 feature 的 slug 是不是规范**？（英文小写连字符，不和已有 feature 目录冲突 → grep `codestable/features/` 确认）
4. **每条描述是不是一句话能讲清楚**？讲不清就是拆得还不够或者 scope 太模糊
5. **依赖关系是不是 DAG**？有没有谁指向自己、或 A→B→A 的回环
6. **最小闭环是不是真的最小**？第一条做完能独立给用户演示点什么？做不到就还不够小
7. **"明确不做"有没有写**？没写的话就说"没有明确不做"，不要空着
8. **和已有 requirement / architecture 有没有矛盾**？有的话在主文档里写"和 req-X 冲突待用户决定"，不要偷偷选一边
9. **update 专项**：本次新加 / 改的条目是否都有对应的素材依据？凭空"再加一条让看起来更完整"是漂移的开端
10. **update 专项**：改了接口契约的话，已经 in-progress / done 的子 feature 受影响了吗？影响到的列在"观察项"，提示用户是否需要起 issue / 二次 design

### Phase 5：用户 review

把主文档 + items.yaml 完整贴给用户，提示 review。用户提意见就改，反复直到用户明确"这份可以了"。

### Phase 6：落盘

- `new` 模式：
  - 建 `codestable/roadmap/{slug}/` 目录
  - 写入 `{slug}-roadmap.md`，frontmatter `status: active`、`created` / `last_reviewed` 填当天
  - 写入 `{slug}-items.yaml`，每条 `status: planned`、`feature: null`
  - 用 `validate-yaml.py --file {slug}-items.yaml --yaml-only` 校验
- `update` 模式：
  - 改主文档，`last_reviewed` 更新为当天；结构性改动在文末 `变更日志` 加一条
  - 改 items.yaml 对应条目，用户标 drop 的条目不删，`status: dropped` 留存（理由一同保留）
  - 重新校验 yaml

**不需要改 requirements / architecture**——roadmap 是规划层，那两层只描述现状。如果拆解过程发现 req 或架构描述确实过时了（比如用户说"先把现在的 X 模块改成 Y 才能接着做"），在主文档"观察项"节记一句交给用户，不要顺手改那两层的文档。

---

## 和 feature 流程的衔接

### feature 从 roadmap 起头

当用户说"开始做 roadmap 里的 {子 feature slug}"时：

1. `cs-feat-design`（或 fastforward / brainstorm）起 feature 目录
2. design frontmatter 带两个字段：`roadmap: {roadmap-slug}` + `roadmap_item: {子 feature slug}`
3. design 流程同时把 `codestable/roadmap/{roadmap-slug}/{roadmap-slug}-items.yaml` 对应条目 `status` 改为 `in-progress`、`feature` 填为 feature 目录名（`YYYY-MM-DD-{slug}`）

这一步的职责在 feature-design 技能里，不在本技能里。

### feature-design 必须把 roadmap 接口契约作为硬约束

`cs-feat-design` 在读 roadmap 时，**必须把对应模块在 roadmap 主文档第 4 节"接口契约"里定的部分作为本 feature 的硬约束输入**——不是"参考一下可以改"，而是 feature 不能违反、要改先回 roadmap update。这是为什么 roadmap 要在拆 feature 之前先把架构方案定下来：让多条 feature 在并行 / 串行实现时，对外接口能对齐。

如果 feature-design 阶段发现 roadmap 里定的接口契约不合理 / 漏了 / 描述不准，**正确做法是回 `cs-roadmap update` 改了再继续**，而不是在 feature 里偷偷绕开。绕开会导致下一条同模块 feature 接到的还是老契约，二次冲突。

### acceptance 自动回写

`cs-feat-accept` 走到收尾时，如果 design frontmatter 有 `roadmap` 字段，就去 `codestable/roadmap/{roadmap-slug}/{roadmap-slug}-items.yaml` 把对应 `roadmap_item` 的 `status` 改为 `done`。同时在主文档的子 feature 清单里把对应行的勾选状态同步。

这一步的职责在 feature-acceptance 技能里，不在本技能里。roadmap 文档本身是项目产物，任何 skill 都可以按 items.yaml 的 schema 读写——**这不算 skill 间耦合**，和各 skill 都读写 `codestable/features/` 是一回事。

### roadmap 本身的生命周期

- 所有 items 都 `done` / `dropped` 后，主文档 frontmatter `status` 改为 `completed`，目录不删，留作历史档案
- roadmap 停摆（长期无进展）：`status: paused`，主文档加一句理由

---

## 硬性边界

1. **不写单 feature 内部的实现细节**——roadmap 写到"模块边界 / 接口契约 / 共享协议"为止，单个模块内部怎么实现属于 feature-design 的范围。判断标准：写出来的东西**会被多个 feature 共同遵守**就归 roadmap，**只在某个 feature 内部用**就归 feature-design。子 feature 清单里每条一句话描述就够
2. **不改现状档案**——不顺手改 requirements / architecture / 代码 / 已有 feature。发现它们有问题就记为"观察项"交给用户
3. **不替用户拍产品优先级**——技术依赖之外的排序让用户决定
4. **单目标**——一次只动一份 roadmap
5. **不发散**——用户描述范围外的问题记成观察项，不扩大 roadmap 范围
6. **接口契约要么写到可执行级，要么明确写"无跨模块接口"**——不允许"待定 / 后面再说"含糊过去。含糊掉的接口在 feature-design 阶段会被各条 feature 各自补，补出来必然不一致

---

## 退出条件

- [ ] 已锁定单一模式（new / update）和单一目标 roadmap
- [ ] 主文档 frontmatter 完整（`doc_type: roadmap` / `slug` / `status` / `created` / `last_reviewed` / `tags`）
- [ ] 主文档包含：背景 / 范围与明确不做 / **模块拆分（概设）** / **接口契约（架构层详设）** / 子 feature 清单 / 排期思路 / 观察项
- [ ] "模块拆分"节列出本大需求拆成哪几个模块，每个模块职责一句话讲清
- [ ] "接口契约"节写到 feature-design 可以拿来当硬约束输入的级别（函数签名 / 数据结构 / 协议字段 / 错误码），或明确写"无跨模块接口"
- [ ] items.yaml 每条都有 `slug` / `description` / `depends_on` / `status` / `feature`
- [ ] 依赖图是 DAG，无循环
- [ ] 最小闭环条目已明确标记
- [ ] items.yaml 通过 `validate-yaml.py --yaml-only` 校验
- [ ] Phase 4 自查清单逐条跑过，并已汇报处理结果
- [ ] 用户明确 review 通过
- [ ] 没有顺手改 requirements / architecture / 代码 / 已有 feature

---

## 和其他工作流的关系

| 方向 | 关系 |
|---|---|
| `cs-req` 配合 | req 记"为什么要有这个能力"，roadmap 记"打算怎么分步把它做出来"。大需求下可能有多份 req；拆解过程中发现缺 req 就提示用户先触发本技能之前跑 `cs-req` |
| `cs-arch` 配合 | architecture 记"系统现在长什么样"，roadmap 记"接下来想把它变成什么样的若干步"。拆解时要读 architecture 理解现状，但不改它 |
| `cs-feat` 下游 | roadmap 里每条子 feature 都是未来一次 feature 流程的种子；feature 从 roadmap 起头时在 design frontmatter 带 `roadmap` / `roadmap_item` 字段 |
| `cs-feat-accept` 回写方 | acceptance 走完时自动改 items.yaml 对应条目为 `done`，本技能只定义格式不负责回写 |
| `cs-onboard` 创建者 | onboarding 建 `codestable/roadmap/` 空目录 |
| `cs-brainstorm` 上游 | brainstorm 判为 case 3 时把讨论移交给本技能，并带上已聊到的真问题 / 大致范围 / 可能子模块做一句话汇总。本技能不重复做分诊，直接进拆解 |

---

## 常见错误

- **跳过架构方案直接拆任务**——上来就列子 feature 清单，模块怎么切、接口怎么对接没想。结果 feature-design 阶段每条 feature 各自发明轮子，跨模块接口对不齐
- **接口契约写得含糊**——"两边商量" / "待定" / "用一个统一的事件总线"——讲不到字段 / 签名 / 协议级。feature-design 接到这种契约没法当硬约束用
- 把单 feature 内部细节写进 roadmap——比如某个模块内部怎么分文件、用哪个库的哪个函数。这些归 feature-design
- 颗粒度失衡——一条子 feature 大到能装下三个独立功能、另一条小到只是改个配置项。都要重新拆
- 依赖关系靠脑补——"B 依赖 A" 但讲不清为什么依赖，回去想清楚再写
- 替用户排优先级——技术依赖之外的顺序让用户拍板
- 和已有 requirement / architecture 冲突不停下——自己偷偷选一边会掩盖真实分歧
- 一次做多份 roadmap——用户 review 不过来
- 顺手改 requirements 或 architecture——越界，那两层是现状档案，动它们走各自技能
- 把 drop 的条目直接删掉——历史状态丢失，后人看不到"这条为什么被放弃"
- roadmap 跑偏不登记——拆解跑着跑着变成给单条子 feature 写详细方案
- update 改了接口契约不评估存量影响——已经 in-progress / done 的 feature 没人看到契约变了，下次代码合并冲突
