# explore 参考模板

本文件提供 `cs-explore` 使用的 frontmatter、正文结构和写作说明。

## 1. frontmatter

```yaml
---
doc_type: explore
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

文件名：`codestable/compound/YYYY-MM-DD-explore-{slug}.md`。

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

## 4. 后续建议

`后续建议` 节写一句话提示用户接下来可能的方向（下一步由用户自己决定，本节不枚举候选技能）。用户说"不用"就跳过。