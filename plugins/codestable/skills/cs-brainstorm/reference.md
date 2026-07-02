# cs-brainstorm 模板

本文件只放落盘模板。`cs-brainstorm/SKILL.md` 负责分诊和对话流程；真正要写文件时再读取这里。

## feature brainstorm 模板

用于 case 2，路径为 `.codestable/features/{feature}/{slug}-brainstorm.md`。

```markdown
---
doc_type: feature-brainstorm
feature: YYYY-MM-DD-{slug}
status: confirmed
summary: 一句话讲选定方向
tags: [...]
---

# {功能名称} Brainstorm

> Stage 0 | {YYYY-MM-DD} | 下一步：design

## 想做什么、为什么
{出发点 + 关键发现和转折}

## 考虑过的方向

### 方向 A：{名}

- 描述 / 价值 / 代价
- 结论：选定 / 否决（原因）

### 方向 B / C ...

## 已敲定的设计点
{聊过程已达成共识的具体设计：库选型 / Schema / 接口形态 / 技术约束}
{每条标：已确认 / 倾向 / 待验证。design 直接落，不重复讨论}
{没聊到这一层整节删掉，别留空}

## 选定方向与遗留问题
{选定方向 2-3 句重述 + 粗粒度轮廓（核心行为 / 明显不做 / 最大未知）+ 遗留给 design 的问题}
```

## open brainstorm 模板

用于 case 4，路径为 `.codestable/brainstorms/{slug}/brainstorm.md`。

```markdown
---
doc_type: brainstorm
slug: {slug}
created: YYYY-MM-DD
status: active
summary: 一句话讲这块要探索什么
tags: [...]
---

# {主题名}

> 创意空间 | {YYYY-MM-DD} | 下一步：cs-epic

## 出发点
{什么触发了这个想法 / 想解决什么问题 / 为什么觉得值得做}

## 聊过的方向
{发散过程的关键转折、候选方向、讨论过的可能性；不要求收敛，保留探索痕迹}

## 当前倾向
{聊到目前的模糊方向，可以是 2-3 个还在摇摆的方向，各自一两句}
{如果已经比较清楚，写"倾向于 X 方向，核心是 Y"}

## 已敲定的点
{聊过程中已经达成共识的：约束、不做、类比、技术判断}
{什么都没有就删掉这节}

## 遗留问题 & 下一步
{最大的未知 / 需要验证的假设 / 建议 roadmap 注意的点}
```
