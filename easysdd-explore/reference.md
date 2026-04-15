# explore 参考模板

本文件提供 `easysdd-explore` 使用的 frontmatter、正文结构和写作说明。

## 1. frontmatter

```yaml
---
type: question | module-overview | spike
date: YYYY-MM-DD
slug: {英文描述，连字符分隔}
topic: {一句话描述探索问题}
scope: {探索范围}
keywords: []
status: active | outdated
confidence: high | medium | low
---
```

## 2. 正文结构

```markdown
## 问题与范围
## 速答
## 关键证据
## 细节展开
## 未决问题
## 后续建议
## 相关文档
```

## 3. 写法说明

- `速答` 必须结论前置
- `关键证据` 目标 3–8 条
- 涉及多模块协作时，在速答节附 Mermaid 图
- 结论必须能被证据支撑

## 4. 后续建议路由

- 需求未落方案 → `easysdd-feature-design`
- 需求已有方案 → `easysdd-feature-implement`
- 问题已成型但根因未明 → `easysdd-issue-analyze`
- 根因明确且用户确认 → `easysdd-issue-fix`
- 形成长期规范拍板 → `easysdd-decisions`
- 沉淀通用做法 → `easysdd-tricks`