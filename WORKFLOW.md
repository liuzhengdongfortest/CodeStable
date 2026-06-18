# CodeStable 工作流与运行结构

## 工作流层次

CodeStable 的技能是分层 + 事件驱动的：

```text
cs
└── cs-onboard
    ├── cs-req / cs-arch
    ├── cs-roadmap
    │   └── cs-roadmap-impl
    ├── cs-feat-design -> cs-feat-impl -> cs-feat-accept
    ├── cs-issue-report -> cs-issue-analyze -> cs-issue-fix
    ├── cs-refactor / cs-refactor-ff
    └── cs-learn / cs-trick / cs-decide / cs-explore
```

纵向是层次，不是严格时间顺序。长效档案层会反复刷新，规划层只在大需求时进入。第 3 层是事件入口：新需求走 feature，bug 走 issue，腐化走 refactor。横切层是知识飞轮：任何流程都可以把值得复用的经验沉淀到 compound。

## 运行时结构

`/cs-onboard` 后，项目根下会出现 `codestable/`：

```text
codestable/
├── requirements/
├── architecture/
├── roadmap/
├── features/
├── issues/
├── refactors/
├── compound/
├── tools/
└── reference/
```

关键约束：

- `requirements/` 和 `architecture/` 是长效档案，只记现状。
- `roadmap/` 是规划层，描述大需求接下来怎么走。
- `features/`、`issues/`、`refactors/` 用 `YYYY-MM-DD-{slug}/` 聚合单次流程产物。
- `compound/` 是唯一知识沉淀目录，靠 `doc_type` 区分 learning / trick / decision / explore。
- `reference/` 由 `cs-onboard` 释放共享口径；跨 skill 共享文档必须通过项目内 `codestable/reference/`，不能从一个 skill 直接引用另一个 skill 包内文件。
