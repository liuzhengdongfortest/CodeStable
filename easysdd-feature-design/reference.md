# feature-design 参考模板

本文件提供 `easysdd-feature-design` 使用的 `{slug}-design.md` / `{slug}-checklist.yaml` 参考格式。

## 1. {slug}-design.md frontmatter

```markdown
---
doc_type: feature-design
feature: 2026-04-12-user-auth
requirement: user-auth-email
status: draft
summary: 支持用户通过邮箱验证码登录后台
tags: [auth, email, login]
---
```

必填字段：`doc_type`、`feature`、`status`、`summary`、`tags`。

`requirement` 字段：填本 feature 对应的 requirement slug（`easysdd/requirements/{slug}.md` 去掉 `.md` 后缀）。纯重构 / 技术债 / 工具链改造类 feature 不新增用户可感能力，允许留空，但要在第 1 节"决策与约束"里明确写"本 feature 不新增能力，无对应 requirement"。

## 2. 顶层节锚点

- `## 0. 术语约定`
- `## 1. 决策与约束`
- `## 2. 接口契约`
- `## 3. 实现提示`
- `## 4. 与项目级架构文档的关系`

## 3. {slug}-checklist.yaml 格式

```yaml
feature: {feature 目录名}
created: YYYY-MM-DD

steps:
  - action: "{步骤名}：{改动描述}"
    exit_signal: "{退出信号}"
    status: pending

checks:
  - item: "{检查项描述}"
    source: 接口契约 | 范围守护 | 测试约束
    status: pending
```

规则：

- `steps` 条目数必须与第 3 节"实现提示"里推进顺序子节一致
- `checks` 至少覆盖明确不做、关键接口契约、测试约束
- 不允许编造 `{slug}-design.md` 里不存在的条目

## 4. 各节写作要求

### `## 0. 术语约定`

- 每个关键术语写：术语 / 定义 / 防冲突结论
- 必须做 grep 防冲突

### `## 1. 决策与约束`

- 需求摘要：做什么、为谁、成功标准、明确不做什么
- 关键决策：选型/取舍/硬约束/被拒方案
- 前置依赖（仅在步骤 3 评估出"目标文件结构性问题需要先解决"时写）：列出当前 feature 推进所必须先完成的独立 feature / 改动，以及"等前置完成后再推进"的状态
- 主流程概述：正常路径 + 关键异常/边界

### `## 2. 接口契约`

- 示例优先，类型补充
- 只写新增/变更接口
- 每个示例底下用注释标来源（`// 来源：{文件路径} {函数名 / 组件名}`），方便 review 时直接跳到代码
- 必要时补一张主流程 Mermaid 图
- **后端 API**：输入→输出示例，含正常 + 主要错误路径
- **前端组件**（涉及 UI 时）：
  - 组件拆分：列出新增/变更组件及其父子关系，说明拆分理由
  - Props / Events（Emits） / Slots 契约：用示例说明而非纯类型定义
  - 状态归属：标注每个关键状态的归属层级（组件内部 / props 传递 / 全局 store）
  - 关键交互路径：用户操作 → 组件响应 → 状态变化（只写非显而易见的路径）

### `## 3. 实现提示`

- 目标文件状况评估结论（仅在步骤 3 评估出需要微重构时写）：说明目标文件当前行数/职责问题，以及拆分方案（extract 什么到哪里）。此条对应推进顺序第 1 步，范围锁死为"只搬不改行为"
- 改动计划
- 实现风险与约束
- 推进顺序（前端 feature 典型节奏：静态结构/组件骨架 → 交互逻辑 → 状态接入 → 联调/样式收尾）
- 测试设计

### `## 4. 与项目级架构文档的关系`

- 关联哪些架构 doc
- 是否要在架构总入口或子系统架构 doc 里补引用
- 如有，写明补充内容摘要

## 5. review 提示

> 方案 doc 已起草完成，请整体 review：
> 1. 术语有没有和已有概念冲突？
> 2. 决策与约束是否准确，“不做什么”有没有遗漏？
> 3. 契约示例是否覆盖了你关心的正常 + 异常场景？
> 4. 推进步骤和测试设计是否可执行？
>
> 有修改意见直接说，确认后进入实现阶段。