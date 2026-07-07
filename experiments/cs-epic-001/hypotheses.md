# Hypotheses — cs-epic-001（预注册，冻结后先 git commit 再跑 LLM）

实验对象：`cs-epic` 拆解大需求时，是否覆盖关键的分解/一致性/灰度/可观测等系统级关注点。
kind=design（高层规划=design 型，纯数据接入，复用 build_design_prompt）。
oracle：`planted_defect` 召回（roadmap/规划是否点出每个必须覆盖的关注点），[measured]。

- **H-epic-coverage**: 对每个大需求的「必须覆盖关注点」recall ≥ 0.80，跨 ≥2 model。threshold: 0.80。

**离线局限**：mock 不产规划 → recall≈0，仅验 pipeline 执行；有效结论须跑真实 harness。
fixtures：8 个大需求，每个带 3 个系统级关注点（n≥8）。
