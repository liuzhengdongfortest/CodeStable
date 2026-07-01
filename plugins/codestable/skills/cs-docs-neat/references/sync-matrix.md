# 文档同步影响矩阵

遇到不确定"这次变化要同步哪些文档"时查本表。两个方向都要看：补漏（该加到哪里）和反膨胀（该从哪里删）。

## 先删 / 迁的反模式

| 反模式 | 处理 |
|---|---|
| `CLAUDE.md` / `AGENTS.md` 顶部堆"某日某功能上线" | 删除；历史归 git log / changelog，稳定事实归 docs 或 `.codestable/` |
| agent 入口里复制 architecture / design 的详细机制 | 删除细节，只留规则和文档索引 |
| `.codestable/attention.md` 写成长篇事故复盘 | 提炼成一行硬约束；细节归 learning / runbook |
| 外部 memory 描述项目架构 / API / 工作流 | 毕业到 `.codestable/requirements/CONTEXT.md`、README 或 docs；memory 留指针或删除 |
| 单次调试流水账长期保留 | 留可复用坑点到 learning；其余删除 |
| 已被新版本取代的中间态说明 | 保留最终态；旧文档标 superseded 或删除临时记忆 |
| README 和 docs 命令互相矛盾 | 以代码和实际可运行命令为准统一 |

判断句：下次 agent 写代码时不看这条会犯错吗？会，进 agent 入口或 attention；不会，进 docs / compound / git log，或者删。

## 代码或行为变化 → 文档层

| 变化 | `.codestable/` | `CLAUDE.md` / `AGENTS.md` | README / docs |
|---|---|---|---|
| 新增 API / 路由 | architecture routes；必要时 requirement | 路由速查或测试命令，只写 agent 会用到的 | integration / dev guide，示例和错误码 |
| 新增环境变量 | architecture / decision（如是长期约束） | 本地运行必需变量和禁区 | README setup、operator runbook |
| 新增数据库表 / schema | architecture data model | 迁移/测试注意事项 | dev guide / architecture docs |
| 新功能 / 用户流程 | requirement 当前能力；architecture 现状；roadmap 状态 | 相关命令或目录规则 | user guide / README usage |
| 新长期约束 / 技术选型 | decision；attention 候选 | 必须遵守的规则 | 架构说明或开发者指南 |
| 踩坑 / 调试路径 | learning；必要时 attention 一行 | 会反复影响实现的红线 | runbook troubleshooting |
| 公开 API / CLI / 组件表面变化 | architecture 索引或 libdoc 关联 | 测试/发布注意事项 | libdoc / dev guide |
| 文档结构调整 | reference / system overview 如涉及 CodeStable | 文档索引更新 | README / docs index |

## 外部 memory 毕业规则

| memory 内容 | 处理 |
|---|---|
| 个人偏好、跨项目协作原则 | 可留在外部全局记忆 |
| 项目专属命令 / 红线 | 迁到 `CLAUDE.md` / `AGENTS.md`，必要时同步 `.codestable/attention.md` |
| 项目架构 / API / 业务能力 | 迁到 `.codestable/requirements/CONTEXT.md`、requirements 或 docs |
| 稳定踩坑 | 迁到 `.codestable/compound/` 的 learning |
| 长期规定 | 迁到 decision，并在 agent 入口保留一行执行规则 |
| 事件流水账 | 删除；必要时由 git log / changelog 承担 |

## 跨项目影响

以下情况必须搜索下游项目或相关 docs：

- 上游 API / SDK / 协议变更。
- 共享域名、子域、环境变量、认证方式变化。
- 公共组件或基础设施升级。
- 文档里有"如何接入本项目"的说明。

当前仓库改完不代表同步完成；依赖方的 setup / integration 文档也可能要改。
