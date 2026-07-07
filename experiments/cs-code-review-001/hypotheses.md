# Hypotheses — cs-code-review-001（预注册，冻结后须先 git commit 再跑任何 LLM）

实验对象：`cs-code-review` skill 在一组 planted-defect fixtures 上的缺陷召回。
oracle：`planted_defect` scorer（token 重叠，机械可验，[measured]）。

- **H-recall-baseline**: 被测 skill 在 planted-defect 集上的 mean recall ≥ 0.85，跨 ≥2 model 一致。
  - direction: observed ≥ threshold ⇒ CONFIRMED
  - threshold: 0.85
- **H-severity-blocking**: 对标注 severity=blocking 的缺陷，recall ≥ 0.90（严重缺陷不应漏）。
  - threshold: 0.90
- **H-cross-model**: 最强与最弱 model 的 recall 差 ≤ 0.15（skill 指令稳健、非依赖单一 model）。
  - threshold: 0.15（差值 ≤ 阈值 ⇒ CONFIRMED）

统计功效：k ≥ 5 且每类 n ≥ 8 方为 full power；否则结论标 [underpowered]。
planted-defect 集混合难度：8 个关键词可检 + 5 个需推理（difficulty:reasoning，如 off-by-one、可变默认参数、资源泄漏、边界错误、空列表越界）。共 13（n≥8 达标）。
区分度证据：离线 mock（纯关键词匹配）在混合集上 recall≈0.67——正说明难例把「关键词匹配」和「会推理的 skill」区分开；H-recall-baseline≥0.85 需真实 skill 跑真实 harness 才可能 CONFIRMED。
注：mock harness 仅用于离线打通管线，其 recall 不构成对真实 skill 的 [measured] 结论。
