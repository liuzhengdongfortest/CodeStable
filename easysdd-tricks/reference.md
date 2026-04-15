# tricks 参考模板

本文件提供 `easysdd-tricks` 使用的技巧文档模板和示例。

## 1. frontmatter

```yaml
---
type: pattern | library | technique
date: YYYY-MM-DD
slug: {英文描述，连字符分隔}
topic: {一句话描述这条技巧解决什么问题}
language: {可选}
framework: {可选}
tags: []
status: active | superseded
superseded-by: {可选}
---
```

## 2. 正文模板

```markdown
## 适用场景

## 做法

## 为什么有效

## 示例

## 何时不适用

## 已知坑

## 相关文档
```

`何时不适用`、`已知坑`、`相关文档` 都是可选节。

## 3. pattern 示例

```markdown
---
type: pattern
date: 2026-04-11
slug: repository-pattern-data-access
topic: 用 Repository 模式把数据访问逻辑和业务逻辑分开，方便单测和未来替换 ORM
language: typescript
tags: [repository, orm, testability, architecture]
status: active
---

## 适用场景

业务层代码直接调用 ORM，导致单测难写且切换 ORM 成本高。

## 做法

为每个聚合根创建 Repository 接口与实现，业务层只依赖接口，不直接导入 ORM。
```