# Results — cs-code-review-robustness-001

真实模型评测中发现并纠正了一个**评测效度硬伤**。经 eval-cs-skill 框架，经 sub2global 网关（api harness）。

## 发现（含纠错）

初测：cs-code-review 在**裸 diff、无 `.codestable/` 上下文**下，claude-haiku-4-5 recall=**0.31**、claude-sonnet-4-6=**1.00**。一度误读为「haiku 通用健壮性 gap」。

手工核查 haiku 原始输出：它严格照「启动检查」四项前置，因缺 attention.md / 来源 spec / 完整 git diff 而**拒绝审查**——这是**正确行为**（preconditions 不满足就退回）。问题在评测：cs skills 为已 onboard 的 `.codestable/` 仓库设计，评测却把 skill 拉出设计环境喂裸输入。

## 对照实验（原始 skill，无 fast-path，haiku，13 例）

| 条件 | haiku recall |
|---|---|
| 裸 diff、零上下文 | 0.31 [measured] |
| **补 onboard 上下文**（attention 就位 + 来源/范围确认，preflight 满足） | **0.92 [measured]** |

**结论：haiku 的低分 ~90% 是「缺 cs-onboard 上下文」造成的评测假象，不是模型/skill 缺陷。** 补上设计所依赖的环境后 haiku≈0.92，逼近 sonnet。真实 haiku↔sonnet 审查能力差 ≈ 0.08（小）。

## 纠正动作

1. **回退**先前 land 到 cs-code-review 的「ad-hoc/bare-input fast-path」——它治标（教 gate 在裸输入下别拒绝），且有弱化这个刻意做重的 gate 的风险。真修复是评测/使用补齐 onboard 上下文。
2. 框架加 `inject_context`（config 字段 + buildprompt 注入 onboard 上下文块），并把它设为**核心 skill 评测的标准条件**，公平测「主路径」而非 bare-input。

## Caveats

- k=1、13 例、单网关；haiku 拒审有概率性（bare 时仍审对 4/13）。效应量（0.31↔0.92）足够明确。
- 原始 LLM 响应在 `/tmp`（未入库）。本文件为可公开证据摘要。
- 「ad-hoc/bare-input 容错」作为**产品选择**仍可另议（skill 文档确有 ad-hoc 来源行），但不应以「修复通用 gap」为由，也不在本次范围。

## 教训（写进方法论）

评测 skill 必须复现它设计所依赖的运行环境（onboard 上下文）；否则测到的是「skill 在错误环境下的反应」，而非其真实能力。分模型看 + 手工核查原始输出，才没把假象当结论。
