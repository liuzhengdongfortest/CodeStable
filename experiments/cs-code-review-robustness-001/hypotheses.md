# Hypotheses — cs-code-review-robustness-001

背景：cs-code-review 在 bare-input（只给 diff、无 CodeStable 上下文）下，弱模型会因「启动检查」前置未满足而**拒绝审查**（haiku 实测退回要求补 attention.md/spec/完整 git diff，未审明显的 `eval(payload)`）。强模型（sonnet）照审。

干预（单一变量）：在 SKILL.md 顶部加「Ad-hoc / bare-input 快速通道」，明确「只给 diff 时不拒绝、直接 best-effort 审、reviewer=self、scope=ad-hoc-diff」。

oracle：`planted_defect` 召回（[measured]），13 例 planted-defect，harness=api，经 sub2global 网关。

- **H-haiku-recovery**: 加 fast-path 后，haiku 在 bare-diff 上的 recall ≥ 0.85（baseline ≈ 0.31）。
- **H-no-regression**: sonnet 的 recall 保持 ≥ 0.95（baseline = 1.00）。

功效：首轮 k=1（效应量极大，方向明确）；k=5 haiku 复测确认稳定性（见 results.md）。
provenance 说明：本实验为真实 harness 探索，hypotheses 在观察到现象后成文，非严格 pre-register；结论 tag 据实标注。
