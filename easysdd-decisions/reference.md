# decisions 参考模板

本文件提供 `easysdd-decisions` 使用的 frontmatter、正文模板和示例。

## 1. frontmatter

```yaml
---
category: tech-stack | architecture | constraint | convention
date: YYYY-MM-DD
slug: {英文描述，连字符分隔}
status: active | superseded | deprecated
superseded-by: {可选}
area: {受影响领域}
tags: []
---
```

## 2. 正文模板

```markdown
## 背景

## 决定

## 理由

## 考虑过的替代方案

## 后果

## 相关文档
```

`考虑过的替代方案` 和 `相关文档` 都是可选节。

## 3. 技术选型示例

```markdown
---
category: tech-stack
date: 2026-04-11
slug: vite-as-bundler
status: active
area: frontend
tags: [vite, bundler, build-tool]
---

## 背景

项目启动时需要选择前端构建工具。

## 决定

使用 Vite 作为开发和生产构建工具。
```