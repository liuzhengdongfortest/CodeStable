# Hypotheses — cs-feat-001（预注册，冻结后先 git commit 再跑 LLM）

实验对象：`cs-feat` 的 design 阶段——给一个需求，产出的 design 是否覆盖必须处理的关注点
（验收标准、边界/异常、范围边界、隐含需求）。kind=design（生成型，用 build_design_prompt）。
oracle：`planted_defect` 召回（design 是否点出每个必须覆盖的关注点），[measured]。

- **H-design-coverage**: 对每个 fixture 的「必须覆盖关注点」recall ≥ 0.80，跨 ≥2 model。threshold: 0.80。

**离线局限（重要）**：mock harness 是关键词 reviewer，**不产 design**——本实验 kind=design 在离线 mock 下 recall≈0，
仅验证 pipeline 能执行与 buildprompt design 分派。**有效结论必须跑真实 harness**（claude-headless/codex/api）。
fixtures：8 个需求，每个带 2-3 个必须覆盖的关注点（n≥8）。
