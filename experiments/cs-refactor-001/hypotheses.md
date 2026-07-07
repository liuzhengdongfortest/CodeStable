# Hypotheses — cs-refactor-001（预注册，冻结后先 git commit 再跑 LLM）

实验对象：`cs-refactor` 识别「伪装成重构但实际改变行为」的能力（行为等价是其核心契约）。
oracle：`planted_defect` 召回（是否点出行为变化），[measured]。kind=review（纯数据接入，无新代码）。

- **H-behavior-change-recall**: 对已植入的行为变化的 recall ≥ 0.85，跨 ≥2 model。threshold: 0.85。

fixtures：8 个，多为需推理的行为等价违规（改默认值、and↔or、去 strip、改边界、is None↔truthiness、删早返回等），
另 2 个含关键词信号（引入 eval / md5）。
区分度：离线 mock（纯关键词）只能抓含信号的那 2 个 → recall≈0.25，正说明「行为等价判断」必须靠真实 skill 推理。
