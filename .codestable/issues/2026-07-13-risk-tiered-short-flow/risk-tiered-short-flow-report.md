---
doc_type: issue-report
issue: 2026-07-13-risk-tiered-short-flow
status: confirmed
severity: P1
summary: 小型明确功能被默认推进为完整 feature 和 goal 流程
tags: [workflow, skill-routing, efficiency]
github_issue: 43
---

# 风险分级与短流程 Issue Report

## 1. 问题现象

一个需求明确、沿用既有桥接接口且代码改动局部的功能，执行 `cs-feat` 后耗时约两小时，经历五轮设计审查、goal driver、三轮代码审查、QA、浏览器烟测、验收及多份状态回写。实际业务代码约十分钟即可完成，流程成本与任务规模不成比例。

## 2. 复现步骤

1. 提出一个边界明确、沿用既有接口、有明确目标测试的局部功能改动。
2. 使用 `cs-feat` 且不显式指定 fastforward 模式。
3. 设计确认后继续默认工作流。
4. 观察到：任务进入完整 design、goal package、implementation、重复 review、QA 和 acceptance 流程，并生成整套产物。

复现频率：按当前默认规则稳定复现。

## 3. 期望 vs 实际

**期望行为**：此类任务应自动选择短流程，完成实现、必要行为测试和构建、一次独立代码审查及简短交付记录；只有风险或范围升级时才进入标准或 goal 流程。

**实际行为**：除非用户事先知道并显式选择 fastforward，否则新功能默认进入完整 feature/goal 管线；用户中途指出流程过重时也不会重新分级。

## 4. 环境信息

- 涉及模块 / 功能：`cs` 路由、`cs-feat`、design review、code review、goal/QA/acceptance 编排
- 相关文件 / 函数：`plugins/codestable/skills/cs/`、`plugins/codestable/skills/cs-feat/`、`plugins/codestable/skills/cs-code-review/`
- 运行环境：CodeStable 1.0.3 skills 工作流
- 其他上下文：GitHub #43；安装更新、standalone 版本和 current-session 定位已分别拆到 #45、#47、#46，不在本次修复范围

## 5. 严重程度

**P1** — 核心功能仍可完成且可显式选择短流程绕过，但默认路径会显著放大日常开发成本，并降低用户继续使用工作流的意愿。

## 备注

本次按任务风险、边界清晰度和已有验证证据分级，不按模型名称或所谓“智商”分级。
