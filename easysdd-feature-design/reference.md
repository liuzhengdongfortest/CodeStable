# feature-design 参考模板

本文件提供 `easysdd-feature-design` 使用的 `design.md` / `checklist.yaml` 参考格式。

## 1. design.md frontmatter

```markdown
---
doc_type: feature-design
feature: 2026-04-12-user-auth
status: draft
summary: 支持用户通过邮箱验证码登录后台
tags: [auth, email, login]
---
```

必填字段：`doc_type`、`feature`、`status`、`summary`、`tags`。

## 2. 顶层节锚点

- `## 0. 术语约定`
- `## 1. 决策与约束`
- `## 2. 接口契约`
- `## 3. 实现提示`
- `## 4. 与项目级架构文档的关系`

## 3. checklist.yaml 格式

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

- `steps` 条目数必须与第 3 节推进顺序一致
- `checks` 至少覆盖明确不做、关键接口契约、测试约束
- 不允许编造 design.md 里不存在的条目

## 4. 各节写作要求

### `## 0. 术语约定`

- 每个关键术语写：术语 / 定义 / 防撞车结论
- 必须做 grep 防撞车

### `## 1. 决策与约束`

- 需求摘要：做什么、为谁、成功标准、明确不做什么
- 关键决策：选型/取舍/硬约束/被拒方案
- 主流程概述：正常路径 + 关键异常/边界

### `## 2. 接口契约`

- 示例优先，类型补充
- 只写新增/变更接口
- 必要时补一张主流程 Mermaid 图

### `## 3. 实现提示`

- 改动计划
- 实现风险与约束
- 推进顺序
- 测试设计

### `## 4. 与项目级架构文档的关系`

- 关联哪些架构 doc
- 是否要在架构总入口或子系统架构 doc 里补引用
- 如有，写明补充内容摘要

## 5. review 提示

> 方案 doc 已起草完成，请整体 review：
> 1. 术语有没有和已有概念撞车？
> 2. 决策与约束是否准确，“不做什么”有没有遗漏？
> 3. 契约示例是否覆盖了你关心的正常 + 异常场景？
> 4. 推进步骤和测试设计是否可执行？
>
> 有修改意见直接说，确认后进入实现阶段。