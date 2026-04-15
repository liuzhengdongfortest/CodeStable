# easysdd 共享口径

本文件存放跨多个 easysdd 子技能共享、但不适合继续堆在根技能 `SKILL.md` 里的规范。根技能负责路由和高层约束；本文件负责可复用的细口径。

---

## 1. 共享元数据口径

### feature spec

- `design.md` / `acceptance.md` 共用 `doc_type`、`feature`、`status`、`summary`、`tags` 这组核心字段
- 子技能只补充本阶段特有字段，不重复改写这组字段的含义

### issue spec

- `report.md` / `analysis.md` / `fix-note.md` 共用 `doc_type`、`issue`、`status`、`tags` 这组核心字段
- `severity`、`root_cause_type`、`path` 等属于阶段特有字段，由对应阶段按需补充

### 归档类文档

- `compound` / `decisions` / `tricks` / `explore` 各自保留专属 frontmatter
- `status` 一类通用字段的语义必须和本文件保持一致，不另起一套口径
- 子技能里如果需要解释状态，只保留该工作流特有的状态流，不重新定义通用语义

### 面向外部读者的文档

- `guidedoc` / `libdoc` 的 frontmatter 由各自子技能定义
- 如无特殊说明：`draft` = 待 review，`current` = 当前有效，`outdated` = 代码已变更待同步

### 写作约束

- 子技能提到字段时，优先写"本技能额外字段"或"本阶段状态变化"
- 不要把整套通用字段定义在多个技能里重复展开

---

## 2. checklist.yaml 生命周期

- `checklist.yaml` 是 feature 工作流的唯一执行清单
- 由 `easysdd-feature-design` 或 `easysdd-feature-fastforward` 在 `design.md` 确认通过后一次生成

### design / fastforward 的职责

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

- 子技能描述 `checklist.yaml` 时，只补充本阶段具体要读/写哪一部分
- 不重新定义整份文件的生命周期

---

## 3. 阶段收尾推荐

### feature-acceptance

收尾时按顺序判断是否要推荐：

1. `compound`：沉淀经验
2. `decisions`：记录长期约束/选型
3. `guidedoc`：更新开发者/用户指南
4. `libdoc`：更新公开 API 参考
5. `scoped-commit`

### issue-fix

收尾时按顺序判断是否要推荐：

1. `compound`：记录坑点
2. `decisions`：如修复暴露出长期约束
3. `scoped-commit`

### 推荐动作的统一规则

- 一律一句话提示
- 用户说"不用"立刻跳过
- 推荐不是强制，不得把用户拖入新的工作流
- 上游技能负责主动提示，下游技能负责承接执行
- 不要出现下游说"应该由上游推荐"、上游却没有动作的漂移