---
doc_type: requirement
slug: plugin-market-distribution
pitch: 让 CodeStable 像插件一样被安装和升级
status: current
last_reviewed: 2026-07-01
implemented_by:
  - 2026-07-01-plugin-market-distribution
tags: [plugin, distribution, versioning]
---

# 让 CodeStable 像插件一样被安装和升级

## 用户故事

- 作为第一次接触 CodeStable 的开发者，我希望用一条插件安装命令拿到完整 `cs` 工作流，而不是自己拷贝一堆 skill 目录。
- 作为同时使用 Codex 和 Claude 的开发者，我希望两边安装到的是同一个 CodeStable 版本，而不是两套内容逐渐漂移。
- 作为不使用 Codex / Claude plugin marketplace 的开发者，我希望仍能用 `npx skills@latest add ...` 安装 CodeStable skills。
- 作为维护者，我希望发布前能检查版本号、manifest 和打包内容一致，而不是发布后才发现某个 skill 或 reference 漏了。

## 为什么需要

现在 CodeStable 更像一个源码仓库和 skill 集合，本机同步可以工作，但对外分发还不够稳定。用户需要知道从哪里装、装到哪一版、升级后变了什么；维护者也需要一个明确的发布边界，避免 Codex、Claude、本机 skill repo 之间出现内容不一致。

## 怎么解决

为 CodeStable 增加一组可提交的插件安装资产。维护者在当前仓库的插件实体里维护唯一 skill 源，同时适配 Codex、Claude 和 `skills` CLI；统一版本号和变更日志说明这一版包含什么。

## 边界

- 第一版不迁移仓库地址，也不要求立刻拥有 `codestable/codestable` GitHub 仓库。
- 第一版不发布到公开 marketplace，只产出可检查、可试装的插件安装资产。
- 第一版只打包 CodeStable 自己的 `cs` / `cs-*` skills，不捆绑通用第三方 skills。
- 它不负责 Nacos skill-sync；本机同步仍按现有 `nacos-skill-sync` 流程处理。
- 安装器需要读取的 marketplace catalog 和插件实体必须进入 git；被 ignore 的临时 `dist/` 目录不能作为用户安装入口。

## 实现记录

- 2026-07-01：`2026-07-01-plugin-market-distribution` 完成第一版插件分发结构。CodeStable `cs` / `cs-*` skills 迁移到 `plugins/codestable/skills/`，新增 Codex / Claude marketplace catalog、插件 manifest、`VERSION` / `CHANGELOG.md`，并用 `tools/check-plugin-package.py` 校验版本、manifest、目录边界和临时产物排除。
