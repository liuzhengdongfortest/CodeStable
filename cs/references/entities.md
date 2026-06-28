# CodeStable 实体

CodeStable 的实体都落在项目的 `.cs/` 里。它们不是 Agent 的私有状态，而是人和 AI 都能读、能改、能追溯的工作产物。

实体分三类：

- **变更轴**：记录这次要改什么，做完就关闭。
- **现状轴**：记录系统现在为什么这样，保持当前真相。
- **横切实体**：让下一次工作更省力。

对应模板在 `templates/entities/`。

## 变更轴

### issue / task

一件可关闭的变更。bug、feature、小重构、chore 都是同一种东西：有目标、有范围、有验证方式，做完就关闭。

它可以存在于 GitHub issue，也可以存在于本地 `.cs/issues/`。二选一由 `cs-onboard` 决定，并记录在 `attention.md`。

issue 不长期描述现状。关闭后，只有稳定下来的取舍和事实才回写到 `context/`。

模板：`templates/entities/issue.md`

### epic

大到塞不进单个 issue 的需求容器。epic 负责大方向、关键取舍、拆分方式和子 issue 的依赖关系。

epic 不替 issue 承担细节复杂度。真正落地仍然拆到 issue；每个 issue 都应该能独立验证和关闭。

模板：`templates/entities/epic.md`

## 现状轴

### context/

当前系统的事实和取舍。它讲代码本身看不出来的东西：领域词汇、为什么这样设计、为什么不走另一条路、哪些边界会变化。

context 不记流水账，不引用一堆代码位置，不替关闭的 issue 保存历史。它只保留当前仍然有效、会影响未来判断的内容。

模板：`templates/entities/context.md`

### convention.md

跨 skill 共享口径。命名、结构、边界、稳定约定放这里。

它不是随手笔记。源头由 `cs-convention` 维护，`cs-onboard` 分发到项目里；其他 skill 读取项目相对路径 `.cs/convention.md`。

模板：`templates/entities/convention.md`

## 横切实体

### attention.md

启动必读。只放一两行当前最容易忘、最影响判断的提醒，也记录变更轴载体是 GitHub 还是本地。

attention 不是知识库。能沉淀成长期知识的，放进 `compound/` 或 `context/`。

模板：`templates/entities/attention.md`

### compound/

知识沉淀。坑点、技巧、调查结论、可复用判断、操作经验，都可以放成纯 markdown，靠全文检索找回来。

compound 不要求结构优雅，重点是下次能搜到。稳定到会影响系统判断的结论，再回写到 `context/`。

模板：`templates/entities/compound.md`

### tools/

跨工作流共享的小工具和脚本。比如登录、抓取、批处理、生成报告这类 AI 反复需要但不该每次重写的东西。

工具需要说明输入、输出、运行方式和危险边界。复杂脚本不要只靠记忆使用。

模板：`templates/entities/tool.md`

### clarify/

大需求还没拆成 epic / issue 前的讨论材料。它承接模糊想法，保存问题、术语、约束和分歧。

clarify 是临时承接区，不是最终归档。想清楚后，要进入 epic / issue；稳定结论再进入 `context/`。

模板：`templates/entities/clarify.md`

### reports/

维护和检查产生的报告。它保存某次观察结果，例如扫描、对账、评估、运行记录。

report 不替代 context。报告里的事实只有在稳定、仍然影响判断时，才回写到现状轴。

模板：`templates/entities/report.md`
