# Hypotheses — cs-code-review-robustness-001

背景：cs-code-review 在 bare-input（只给 diff、无 `.codestable/` 上下文）下，haiku 因「启动检查」前置未满足而拒审（0.31），sonnet 照跑（1.00）。核心问题：这是模型/skill 缺陷，还是评测没给 skill 设计所依赖的 onboard 环境？

oracle：`planted_defect` 召回（[measured]），13 例，harness=api，经 sub2global 网关。

- **H-context-recovers**: 用**原始 skill**（无 fast-path）+ 补齐 onboard 上下文后，haiku recall ≥ 0.85（bare ≈ 0.31）。
  - 结果：**CONFIRMED**，haiku=0.92 → 低分是缺上下文的评测假象，非模型缺陷。
- 推论：真实 haiku↔sonnet 审查能力差很小（≈0.08）。

功效：k=1、13 例（效应量 0.31↔0.92 极大，方向无歧义）。provenance：真实 harness 探索，据实标注。
