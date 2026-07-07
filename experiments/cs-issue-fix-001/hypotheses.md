# Hypotheses — cs-issue-fix-001（预注册，冻结后先 git commit 再跑 LLM）

实验对象：`cs-issue`（fix 阶段）对一组 bug fixtures 的根因识别。
oracle：`planted_defect` 召回（fix 输出是否点中已知根因），[measured]。

- **H-rootcause-recall**: 对已知根因的 recall ≥ 0.85，跨 ≥2 model。
  - threshold: 0.85
- **H-no-overreach**: fix 不应引入超出根因范围的改动（由 llm_judge compliance 轴衡量，[soft]）。

统计功效：当前仅 3 fixtures（n<8）→ 结论标 [underpowered]，仅作接入自举证明，非正式结论。
