# Hypotheses — cs-docs-001（预注册，冻结后先 git commit 再跑 LLM）

实验对象：`cs-docs` 产出文档时，是否覆盖必要要素（参数/返回/错误、前置条件、可运行示例、边界坑）。
kind=docs（生成型，用 build_docs_prompt）。
oracle：`planted_defect` 召回（文档是否覆盖每个必须要素），[measured]。

- **H-docs-coverage**: 对每个文档任务的「必须覆盖要素」recall ≥ 0.80，跨 ≥2 model。threshold: 0.80。

**离线局限**：mock 不产文档 → recall≈0，仅验 pipeline 执行与 docs 分派；有效结论须跑真实 harness。
fixtures：8 个文档任务，每个带 3 个必须覆盖要素（n≥8）。
