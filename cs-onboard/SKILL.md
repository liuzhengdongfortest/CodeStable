---
name: cs-onboard
description: 初始化或补齐 CodeStable .cs 工作区。触发：第一次使用 cs、初始化 cs、重跑 onboard。只补骨架，不迁移旧需求。
---

# cs-onboard

## 背景

`cs-onboard` 负责把 CodeStable 的本地工作区放进项目：创建 `.cs/`、基础实体目录、启动事实和 project spec 主文档骨架。

它只做初始化和补齐。已有内容默认保留，不迁移旧文档，不替用户整理需求，不创建 issue。

## 原则

onboard 可以观察项目，但不能编项目。能从代码、README、配置、测试和 git 历史推断的，只能作为候选事实或下一步建议；业务目标、路线图、明确不做什么、用户故事和长期取舍，除非已有文档证据或用户确认，否则不要写进 `.cs/`。

默认不覆盖已有文件。只有用户明确要求重置 `facts.md` 或 `.cs/spec/index.md` 时，才使用 `--force`，并在执行前再次确认。

## 行动指南

优先运行：

```bash
python cs-onboard/scripts/init_codestable.py --project .
```

初始化后确认 `.cs/facts.md` 和 `.cs/spec/index.md` 存在，并确认基础实体目录已创建或保留。

如果项目已有旧文档，只指出下一步可以用 `cs-talk`、`cs-spec`、`cs-plan`、`cs-note`、`cs-maketools` 或 `cs-close` 逐步沉淀，不在 onboard 里强迁移。

## 产物契约

脚本会创建 `.cs/facts.md`、`.cs/spec/index.md` 和这些目录：

- `.cs/talks/`
- `.cs/spec/`
- `.cs/issues/`
- `.cs/epics/`
- `.cs/notes/`
- `.cs/tools/`

`.cs/spec/index.md` 只是 project spec 主文档骨架，用来承载未来的项目导读、当前方向、能力地图、架构地图、统一语言和阅读路径；onboard 不替用户填写真实需求，不创建 issue、epic、note 或 tool 正文，不覆盖已有内容。

## 收尾汇报

告诉用户创建或补齐了哪些目录和文件、哪些已存在所以保留、下一步该用哪个技能：想法模糊用 `cs-talk`，需要维护 project/epic spec 用 `cs-spec`，已有讨论或 epic spec 本轮可计划范围用 `cs-plan`，要记知识用 `cs-note`，内部流程未知用 `cs-maketools`。

## 应用场景

第一次使用 cs、项目还没有 `.cs/`、用户说接入 CodeStable/初始化 cs/搭好 cs 基础结构/重跑 onboard 同步缺失骨架时使用。
