---
name: easysdd
description: easysdd 工作流家族的根技能——介绍工作流体系并把用户路由到正确子技能。触发场景：用户提到"easysdd"、"sdd"、"规约驱动"、"怎么用这套流程"、"我该用哪个技能"、"从哪开始"，或描述了新功能但还没决定切入阶段。已知意图（brainstorm/设计/实现/验收/BUG/探索等）优先触发对应子技能而非本技能。
---

# easysdd

AI 辅助开发里，有几类场景会反复出现——加新功能、修 bug、遇到值得沉淀的经验、做技术选型、摸新模块的代码、接入新仓库。每种场景如果每次从零处理，都会出各自的典型翻车：AI 给功能起的术语跟老代码冲突、bug 改完没人记得当时怎么诊断的、上周刚踩过的坑下周又踩一遍。

easysdd 把这几类场景各配一套子技能，产物放进统一的目录结构、带统一的 YAML frontmatter，互相之间可以检索引用。


## 技能分成三部分

**做事**——从一段模糊想法走到上线的功能、或者从一份错误报告走到修好的 bug：

- `easysdd-feature` — 新功能，brainstorm → design → implement → acceptance
- `easysdd-issue` — 修 bug，report → analyze → fix

两类都不直接让 AI 写代码，而是先产出 spec（功能方案 / 问题分析），用户 review 后再动手，代码和 doc 一起交付。防的是术语冲突、范围失控、改完不留存档这三种 AI 默认会翻的车。

**沉淀**——把做事过程产生的知识存下来，下次遇到同类问题直接复用：

- `easysdd-learning` — 回顾"做 X 时踩了 Y 这个坑"
- `easysdd-tricks` — 处方"以后做 X 就这样做"
- `easysdd-decisions` — 规定"全项目今后都按 X 来"
- `easysdd-explore` — 存档"调查了 X 问题，看到代码里是这样的"

**辅助**——围着前两类转的周边工具：

- `easysdd-onboarding` — 把新仓库接入 easysdd 目录结构
- `easysdd-requirements` — 起草或刷新 `easysdd/requirements/` 下的需求文档（"为什么要有这个能力"）
- `easysdd-architecture-gen` — 起草或刷新 `easysdd/architecture/` 下的架构文档（"用什么结构实现"）
- `easysdd-architecture-check` — 检查 design 自洽或 design 与代码一致
- `easysdd-guidedoc` — 写给外部读者的开发者指南 / 用户指南
- `easysdd-libdoc` — 为库的公开 API 逐条目生成参考文档


## 场景路由

仓库里还没有 `easysdd/` 目录，先用 `easysdd-onboarding` 搭骨架。

| 场景 | 子技能 |
|---|---|
| 新功能 / 新能力 | `easysdd-feature` |
| BUG / 异常 / 文档错误 | `easysdd-issue` |
| 摸代码、提问调研 | `easysdd-explore` |
| 补 / 更新需求文档 | `easysdd-requirements` |
| 补 / 更新架构文档 | `easysdd-architecture-gen` |
| 检查 design 一致性 | `easysdd-architecture-check` |
| 技术选型 / 约束 / 规约 | `easysdd-decisions` |
| 踩坑回顾、经验总结 | `easysdd-learning` |
| 可复用的编程模式、库用法 | `easysdd-tricks` |
| 开发者指南 / 用户指南 | `easysdd-guidedoc` |
| 库 API 参考 | `easysdd-libdoc` |

完整的操作手册、退出条件、和其他工作流的关系，各子技能里讲。


## 沉淀类四个子技能如何区分

learning / trick / decision / explore 都是存档文档类型，区别在记录内容的性质：

- 回顾某次做 X 时发现了 Y —— `easysdd-learning`（产出 `doc_type: learning`）
- 以后做 X 就这样做的处方 —— `easysdd-tricks`（产出 `doc_type: trick`）
- 全项目今后都得遵守的规定 —— `easysdd-decisions`（产出 `doc_type: decision`）
- 调查了一个问题，留份证据 —— `easysdd-explore`（产出 `doc_type: explore`）

四者共用 `easysdd/compound/` 目录，靠 frontmatter 的 `doc_type` 字段和文件名中间的类型段（`YYYY-MM-DD-{doc_type}-{slug}.md`）区分。每个子技能只认自己的 `doc_type`，不读写别家产物——**"A 和 B 有什么不同"这种判断由本节负责，子技能里不再重复**。


## feature 和 issue 的阶段不可跳

feature 走 brainstorm（可选） → design → implement → acceptance，issue 走 report → analyze → fix。每个阶段有退出条件，上一个没满足，下一个不开始。

AI 最常见的翻车方式是一口气铺几百行代码才让人看——等发现问题已经很难截停。阶段间的人工 checkpoint 就是为了早一步截停。每个 checkpoint 具体检查什么，对应子技能里讲。

例外两种：issue 根因一眼确定时走快速通道，跳过 analyze 直接 fix；feature 范围小时走 `easysdd-feature-fastforward`，写完 spec 直接进实现。


## 进一步参考

共享参考文档由 `easysdd-onboarding` 从技能包 `easysdd-onboarding/reference/` 一次性复制到项目的 `easysdd/reference/` 目录——各子技能在运行时用项目相对路径读取，这是 skill 独立安装前提下唯一可达的共享方式。

- `easysdd/reference/shared-conventions.md` — 目录结构、YAML frontmatter 口径、`{slug}-checklist.yaml` 生命周期、收尾 commit 约定、归档类共享规则
- `easysdd/reference/tools.md` — `search-yaml.py` / `validate-yaml.py` 用法
- `easysdd/reference/maintainer-notes.md` — 断点恢复、新增子工作流的登记

目录结构（requirements/、architecture/、features/、issues/、compound/、tools/、reference/）的权威定义在 `shared-conventions.md`。要改目录先改那里——方法是改 `easysdd-onboarding/reference/shared-conventions.md` 这个模板，新项目 onboarding 时会带上新版本。

四个沉淀子技能（learning / tricks / decisions / explore）共用一个 `compound/` 目录，靠 frontmatter `doc_type` 和文件名里的类型段区分来源，不再各自建目录。


## 相关

- `AGENTS.md` — 全项目代码规范和已知坑
- `easysdd/architecture/DESIGN.md` — 项目架构总入口
