# onboard 参考模板与迁移详步

## `.codestable/attention.md` 最小模板

attention.md 是 CodeStable 技能启动必读的项目注意事项入口。onboard 创建最小骨架，不替项目 owner 填实质内容；后续短规则由 `cs-note` 追加。顶部 `载体` 字段在 onboard 时确定。

```markdown
# Attention

本文件是 CodeStable 技能启动必读的项目注意事项入口。所有 CodeStable 子技能开始工作前必须读取它。

载体: github | local   <!-- 变更轴(issue/epic)落在 GitHub 还是 .codestable 本地 -->

## 项目碎片知识

<!-- cs-note managed: 用 cs-note 维护，新条目按下面分节追加 -->

### 编译与构建

### 运行与本地起服务

### 测试

### 命令与脚本陷阱

### 路径与目录约定

### 环境变量与凭证

### 其他
```

---

## 迁移路径详步

### 步骤 1：生成审计报告

| 现有文件 | 推测内容类型 | 建议归入 | 置信度 |
|---|---|---|---|
| `docs/glossary.md` | 领域术语 | `context/CONTEXT.md`（cs-context 写） | 高 |
| `docs/adr-*.md` | 架构决策 | `context/` 对应取舍说明的「为什么需要灵活性」节 | 中 |
| `docs/feature-*.md` | 功能设计稿 | 已实现 → `context/` 取舍说明；未实现 → 开 issue | 中 |
| `SPEC.md` | 需求？ | 需用户确认 | 低 |

置信度：高 = 语义明确匹配；中 = 可推断有歧义；低 = 不明确或多个位置都合理。

### 步骤 2：逐条对齐

中 / 低置信度用 `AskUserQuestion` 问：中 = 给推断理由问"按这个归位？"；低 = 描述内容给 2-3 候选 + "跳过"。高置信度不逐条问但在汇报里列，给复审机会。

### 步骤 3：处理已部分存在的 `.codestable/`

- 命名不符规范但有内容 → 提示是否重命名
- 空占位（`.gitkeep` / 空 `.md`）→ 直接补齐不问

### 步骤 4：补齐缺失骨架

对照标准骨架补齐**用户确认后仍缺失**的目录 / 文件，已有内容不覆盖。`convention.md` / `tools/` / `reference/` 例外——这三样无条件用技能包新版覆盖（命令见 SKILL.md）。

### 步骤 5：处理不迁移的文件

用户选"跳过"的：**不移动 / 不删除 / 不重命名**，汇报标"保留原位（未纳入 CodeStable）"。绝不允许未经确认就动。

### 步骤 6：验收汇报

列：迁移清单（from → to）、新建骨架、未迁移文件（保留原位）、变更轴载体、下一步建议。

---

## 旧模型迁移提示

从旧版（feature / roadmap / refactor / requirements 四目录）迁来的项目：

- `requirements/` → `context/`：能力文档剥掉产品口吻重铸成取舍说明；CONTEXT.md / adrs 的术语与决策理由并入 context
- `roadmap/` → 未完成的当 epic 重开；已完成的契约毕业进 context
- `features/ refactors/ issues/` 旧 spec → 未完成的当 issue 重开；已完成的取舍进 context，spec 本身进 git 历史
