# CodeStable 实体

CodeStable 的实体都落在项目的 `.cs/` 里。它们不是 Agent 的私有状态，而是人和 AI 都能读、能改、能追溯的工作产物。

实体按工作流顺序分四类：

- **启动和讨论**：先读事实，再把没想清楚的想法整理到 talks。
- **事项**：记录这次要做什么，做完就关闭。
- **requirements**：记录当前需求、约束、领域词汇和设计取舍。
- **wiki**：自动建设系统理解 wiki 和 requirements 候选库。
- **辅助资料**：让检索、复用和自动化更省力。

实体模板放在 `cs` 技能包内的 `templates/entities/`，作为体系模板的唯一来源。`cs-onboard` 只创建必要的启动骨架：`facts.md` 和 `.cs/requirements/index.md`；其他实体正文由对应技能在需要时创建。

## 启动和讨论

### facts.md

启动必读事实。只放少量当前最容易忘、最影响判断的稳定事实。

facts 不是知识库。能沉淀成长期知识的，放进 `notes/` 或 `requirements/`。需要手动记录时，用 `cs-note` 判断：一两行启动必读事实写 facts；需要背景、证据或步骤的写 notes。

当 `cs-maketools` 跑通一个流程后，facts 只追加一行指向对应 notes 的引用，让后续 AI 知道先读哪篇流程笔记。

读取 facts 不需要每个技能都重新来一遍。当前对话或执行上下文里没读过就读；已经读过且没有修改迹象，就复用已知事实。

模板：`templates/entities/facts.md`

### talks/

讨论整理。它承接还没进入 epics / issues 的模糊想法，保存问题、术语、约束、分歧和下一步。

talks 是临时承接区，不是最终归档。聊完后先把讨论整理进去；再由 `cs-plan` 判断：过大就进入 epics 规划并产生 issues，足够小就直接进入 issues。稳定结论只在事项关闭后进入 `requirements/`。

talks 按日期分片存放：`.cs/talks/YYYY/MM/DD/{slug}.md`。文件名只放 slug；查找时递归搜索 `.cs/talks/`。

模板：`templates/entities/talk.md`

## 事项

### epics/

过大的讨论产物进入 epics 规划。单个 epic 负责大方向、关键取舍、拆分方式和子 issue 的依赖关系。

epic 不替 issue 承担细节复杂度。真正落地仍然拆到 issues；每个 issue 都应该能独立验证和关闭。

epic 按创建日期分片存放：`.cs/epics/YYYY/MM/DD/{slug}.md`。文件名只放 slug；查找时递归搜索 `.cs/epics/`。

模板：`templates/entities/epics.md`

### issues/

一组可关闭的变更。单个 issue 可以是 bug、feature、小重构、chore，本质都是同一种东西：有目标、有范围、有实现设计、可选测试设计、有验证方式、有执行记录，做完就关闭。

issues 存在于本地 `.cs/issues/`。它是 CodeStable 当前的默认事项实体。

issue 按创建日期分片存放：`.cs/issues/YYYY/MM/DD/{status}-{slug}.md`。新建时使用 `open-{slug}.md`，关闭时由 `cs-close` 改成 `closed-{slug}.md`；frontmatter 的 `status` 要和文件名前缀一致。查找时递归搜索 `.cs/issues/`。

行为投诉由 `cs-complain` 整理成 bug issue。它固定预期、实际、复现和证据，再建立反馈回路、诊断根因、修复验证并回写同一个 issue。

issue 的实现设计由 `cs-design` 面向单个 issue 写回。它只服务该事项，不单独形成 designs 实体。

issue 的测试设计由 `cs-test` 按需写回。它是可插拔关卡，不要求每个 issue 都有。

issue 的代码执行由 `cs-do` 推进，并把实际改动、验证结果和设计偏差写回执行记录。

issue 的关闭由 `cs-close` 完成。关闭时把仍然有效的需求、约束、取舍、坑点、操作经验和工具说明，分别沉淀到 `requirements/`、`notes/`、`facts.md` 或 `tools/`；如果项目是 git 仓库，把相关代码、目标 issue 和 `.cs` 回写一起提交。

issue 不长期描述需求和取舍。关闭后，只有稳定下来的约束、事实和判断才回写到长期实体。

模板：`templates/entities/issue.md`

## requirements

### requirements/

当前需求、约束、领域词汇和设计取舍。它讲代码本身看不出来的东西：为什么要这样、为什么不走另一条路、哪些边界会变化、哪些用户故事必须被守住。

requirements 要写得像人话。优先用说明的姿态描述：背景是什么，系统大致要实现什么功能，用户为什么需要它，现在有哪些已经稳定的规则和取舍。不要只堆字段、标签和抽象名词。

requirements 按“主文档统帅、子文档分治”组织。主文档默认是 `.cs/requirements/index.md`：它负责项目/领域背景、总体目标、统一术语、核心规则、当前结构和子文档索引。子系统、子步骤、题型、用户工作流或复杂领域规则拆成同目录下的独立 requirements 文件；子文档只负责自己的局部细节，并从主文档索引进入。

如果用 CodeStable 打比赛，主文档写比赛背景、目标、评分规则、通用约束和题型索引；动态规划、图论、构造、交互题等分别进入子文档。不要把每次新增的规则随手新建成一堆平级文件，让后来者不知道先读哪篇。

requirements 不记流水账，不替关闭的 issue 保存历史。它只保留当前仍然有效、会影响未来判断和实现的内容。历史、执行过程和一次性判断留在关闭的 issue 里。

模板：主文档用 `templates/entities/requirements.md`；子文档用 `templates/entities/requirements-topic.md`

### wiki/

系统理解 wiki 和 requirements 候选库。它由 `cs-wiki` 自动维护，用新人/外部观察者视角多轮提问、派 subagent 调查、综合成文档。

wiki 不是 requirements。它可以多写、多试探、多记录未知；正式 requirements 只接收经过用户确认或关闭流程沉淀的当前真相。wiki 的价值是把系统方方面面先摸出来，形成可审阅、可迁移的材料。

默认结构：

- `.cs/wiki/index.md`：wiki 首页和系统总览。
- `.cs/wiki/map.md`：主题地图、覆盖度、薄弱区和未知区。
- `.cs/wiki/questions.md`：问题池、已回答、待回答和下一轮候选。
- `.cs/wiki/requirements-drafts.md`：可迁移到 requirements 的候选段落和建议位置。
- `.cs/wiki/topics/{slug}.md`：按数据流、控制流、模块、概念、用户路径或外部依赖组织的主题文档。

模板：`templates/entities/wiki-index.md`、`wiki-topic.md`、`wiki-questions.md`、`wiki-requirements-drafts.md`

## 辅助资料

### notes/

知识笔记。坑点、技巧、调查结论、可复用判断、操作经验，都可以放成纯 markdown，靠全文检索找回来。日常“记下来”统一走 `cs-note`，由它判断写 notes 还是 facts。

`cs-maketools` 走通未知流程后，必须把真实操作步骤、前置条件、成功判断、失败处理和危险边界写成 notes。

notes 不要求结构优雅，重点是下次能搜到。稳定到会影响系统判断的结论，再回写到 `requirements/`。

模板：`templates/entities/notes.md`

### tools/

跨工作流共享的小工具和脚本。比如登录、抓取、批处理这类 AI 反复需要但不该每次重写的东西。

tools 通常来自 `cs-maketools` 的后半段：只有当流程步骤稳定、重复、机械化，且不会绕过必要的人类确认时，才沉淀成工具。

工具需要说明输入、输出、运行方式和危险边界。复杂脚本不要只靠记忆使用。

模板：`templates/entities/tool.md`
