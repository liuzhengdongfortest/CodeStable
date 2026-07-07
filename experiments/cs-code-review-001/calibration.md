# Judge / Scorer 校准 — cs-code-review-001

sanity 集是「任何合格 skill 都必须做对」的显然样本，用来校准 oracle：若 scorer/judge 在 sanity 上都不对，其对困难样本的结论不可信。

## planted_defect（确定性 oracle，[measured]）

- sanity 集（sn-001 eval(input())、sn-002 硬编码 password）召回应 = 1.0。
- 若 < 1.0，说明 token 匹配阈值或 fixture answer 措辞需修，先修 oracle 再谈实验结论。

## llm_judge（[soft]，校准后方可升 [measured]）

- 离线 heuristic 模式：compliance 依据是否有 Findings 结构、quality 依据发现是否带 `[locus]`。仅用于打通管线，**不构成质量结论**。
- 真实 judge 模型校准（TODO，需 judge_model 独立于被测 model）：在 sanity 集上，judge 对「正确指出缺陷的输出」应给 quality ≥ 0.8、对「漏报的输出」应给 ≤ 0.4。达成后 F1 ≥ 0.8 方可把 judge 分数在结论中标为 [measured]。
- 当前状态：heuristic-only，judge 分数一律 [soft]。
- 用 `scripts/calibrate_judge.py --experiment <dir>` 对 good/bad 配对输出算 pairwise 准确率：mock→`soft-only`；真实 judge 且 acc≥0.8→`measured-eligible`（写 `artifacts/analysis/judge-calibration.json`）。
- judge oracle 独立性：`judge_model` 必须不在 `model_list`（混杂控制，runner preflight 会告警，optimize 的 confound_control 分量机械校验）。

## 复现

```bash
python3 <cs-skill>/scripts/runner.py --experiment experiments/cs-code-review-001 --harness mock --k 1
# 看 aggregate.baseline.scores.recall（应含 sanity 在内仍高）与 judge_compliance/judge_quality
```
