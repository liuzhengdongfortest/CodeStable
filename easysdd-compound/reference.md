# compound 参考模板

本文件提供 `easysdd-compound` 的两条轨道模板和示例。

## 1. 坑点轨道（pitfall）

### frontmatter

```yaml
---
track: pitfall
date: YYYY-MM-DD
slug: {英文描述，连字符分隔}
component: {受影响模块/层}
severity: low | medium | high
tags: []
---
```

### 正文结构

1. 问题
2. 症状
3. 没用的做法
4. 解法
5. 为什么有效
6. 预防

## 2. 知识轨道（knowledge）

### frontmatter

```yaml
---
track: knowledge
date: YYYY-MM-DD
slug: {英文描述，连字符分隔}
component: {适用模块/领域}
tags: []
---
```

### 正文结构

1. 背景
2. 指导原则
3. 为什么重要
4. 何时适用
5. 示例

## 3. 示例

完整示例可按仓库需要逐步补充；当前技能正文只保留流程，不再内嵌长示例。