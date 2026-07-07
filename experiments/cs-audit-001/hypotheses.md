# Hypotheses — cs-audit-001（预注册，冻结后先 git commit 再跑 LLM）

实验对象：`cs-audit` 对一组已知漏洞样本的审计召回。
oracle：`planted_defect` 召回，[measured]。

- **H-audit-recall**: 对已知漏洞的 recall ≥ 0.85，跨 ≥2 model。threshold: 0.85。

统计功效：当前 3 fixtures（n<8）→ 结论标 [underpowered]，用于接入自举证明。
