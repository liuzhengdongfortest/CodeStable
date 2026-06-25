# CodeStable 技能目录

| 分组 | 技能 | 用途 |
|---|---|---|
| 根入口 | `cs` | 统一入口，介绍体系并把开放式诉求路由到正确的 `cs-*` 子技能 |
| 接入 | `cs-onboard` | 把 CodeStable 接入到一个新仓库或已有零散文档的仓库 |
| 需求与架构 | `cs-req` | 整理和沉淀原始需求文档 |
| 需求与架构 | `cs-arch` | 起草或更新 `codestable/architecture/` 下的架构文档 |
| 路线图 | `cs-roadmap` | 为大需求做事前规划：概设、接口契约、子 feature 拆解 |
| 路线图 | `cs-roadmap-review` | roadmap 人工确认前的独立规划审查 gate |
| 路线图 | `cs-roadmap-impl-goal` | 把已确认 roadmap 编排成可直接运行的 goal，逐个 feature 执行 impl / review / QA / accept |
| 讨论入口 | `cs-brainstorm` | 想法模糊时分诊：直接 design、进入 feature brainstorm，或移交 roadmap |
| 特性流程 | `cs-feat` | 新特性子流程入口 |
| 特性流程 | `cs-feat-design` | 起草 `{slug}-design.md` 作为后续唯一输入 |
| 特性流程 | `cs-feat-design-review` | feature design 人工确认前的独立方案审查 gate |
| 特性流程 | `cs-feat-impl` | 按 design 的推进顺序写代码 |
| 特性流程 | `cs-code-review` | 实现完成后的只读代码审查 gate |
| 特性流程 | `cs-feat-qa` | 代码审查通过后的本地 QA 验证 gate |
| 特性流程 | `cs-feat-accept` | 对照 design 核对实现并完成验收闭环 |
| 特性流程 | `cs-feat-ff` | 超轻量通道：不写 design、不分阶段，直接实现 |
| 问题流程 | `cs-issue` | 问题修复子流程入口 |
| 问题流程 | `cs-issue-report` | 把问题落成可复现、可追溯的 report |
| 问题流程 | `cs-issue-analyze` | 找根因、评估修复风险、给方案 |
| 问题流程 | `cs-issue-fix` | 定点修复、验证并写 fix-note |
| 重构流程 | `cs-refactor` | beta 重构主流程 |
| 重构流程 | `cs-refactor-ff` | beta 轻量重构通道 |
| 知识沉淀 | `cs-learn` | 把踩过的坑或好做法沉淀成 learning 文档 |
| 知识沉淀 | `cs-trick` | 把可复用模式或库用法整理成处方性参考 |
| 知识沉淀 | `cs-decide` | 把已拍板的技术选型、架构决定、长期约束记成永久文档 |
| 知识沉淀 | `cs-note` | 把一两行启动必读的项目注意事项追加到 `.codestable/attention.md` |
| 探索与文档 | `cs-explore` | 定向代码探索，把“提问 → 读代码 → 得结论”沉淀成证据 |
| 探索与文档 | `cs-audit` | 主动审计代码中的 bug 隐患、安全、性能、可维护性和架构偏离 |
| 探索与文档 | `cs-guide` | 编写对外开发者指南 |
| 探索与文档 | `cs-libdoc` | 为库的公开表面生成参考文档 |
| 探索与文档 | `cs-docs-neat` | 阶段收尾时同步 `.codestable/`、README/docs、`CLAUDE.md` / `AGENTS.md` 和 agent 记忆 |
