# Hypotheses — {experiment}（预注册，冻结后须先 git commit 再跑任何 LLM）

实验对象：`{skill}` 在 {fixtures 描述} 上的 {指标}。
oracle：{scorer}（说明是否机械可验 → [measured]）。

- **H-{id}**: {metric} ≥ {threshold}，跨 ≥2 model 一致。
  - direction: observed ≥ threshold ⇒ CONFIRMED；< ⇒ REJECTED；方向反转 ⇒ NULL
  - threshold: {number}
- **H-{id2}**: {另一指标} ...

统计功效：k ≥ 5 且每类 n ≥ 8 方为 full power；否则结论标 [underpowered]。
混杂控制：judge_model 须独立于被测 model_list。

> 冻结记录：git commit `{hash}` @ {time}（由 provenance 校验使用）。
