# cs-issue-e2e-001 hypotheses

## H1

在 `cs-issue` skill 引导下，agent 能定位并修复 taskhub seed 中注入的 bug，使 hidden 验收测试通过（主指标 `hidden_pass`），同时保持 seed 自带回归测试全绿。

## 对照计划

本轮为 `k=1` 冒烟实验，只跑 baseline。后续加入裸 agent（无 skill）对照，用同一批 seed、bug 注入器和 hidden tests 评估 skill 的增益。

## 诚实 caveats

- 出题者同时是 taskhub seed 作者，存在作者偏差；后续用 L2 裸 agent 对照抵消一部分偏差。
- `k=1` 只能证明管线可跑和题目可解，不能给出稳定统计结论。
- 三个 bug 刻意放在 seed 自带测试的暗角，适合评测 e2e outcome，不适合作为真实覆盖率结论。
