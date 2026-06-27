---
name: cs-convention
description: 维护 CodeStable 体系的共识与约定（两轴模型 / 启动必读 / 变更轴载体 / 路径命名 / 单目标 / 退出骨架）。源真相在 cs-onboard/reference/convention.md，由 cs-onboard 分发到项目 .codestable/convention.md。触发：要改一条跨技能的共享口径。
---

# cs-convention

CodeStable 所有 cs-* 技能共享的口径放在**一份** convention 里，省得每个技能重复样板。

- **源真相**：`cs-onboard/reference/convention.md`（技能包内）。放在 onboard 包里，因为运行时只有 onboard 能把它分发出去（技能之间互相读不到文件）。
- **项目副本**：`.codestable/convention.md`，由 `cs-onboard` 分发；各技能运行时读它。
- 各技能开头一行「遵循 `.codestable/convention.md`」即可。

## 要改一条共享口径

1. 改 `cs-onboard/reference/convention.md`
2. 提示已 onboard 的项目重跑 `cs-onboard` 同步副本
3. 若口径变动牵动某技能的独有判断，顺带核对那个技能（CLAUDE.md：改体系要同步改相关表述）

## 收哪些 / 不收哪些

- **收**：跨多个技能共享的口径——两轴模型、启动必读、变更轴载体、路径命名、单目标、不发散、人在环、scoped-commit、退出骨架。
- **不收**：某技能独有的判断——留在它自己的 SKILL.md，别往 convention 堆。

判据：一条口径只被一个技能用 → 不进 convention；被两个以上共享 → 进。
