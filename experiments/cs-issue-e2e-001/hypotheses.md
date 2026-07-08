# cs-issue-e2e-001 hypotheses

## H1

在 `cs-issue` skill 引导下，agent 能定位并修复 taskhub seed 中注入的 bug，使 hidden 验收测试通过（主指标 `hidden_pass`），同时保持 seed 自带回归测试全绿。

## 对照计划

本轮为 `k=1` 冒烟实验，只跑 baseline。后续加入裸 agent（无 skill）对照，用同一批 seed、bug 注入器和 hidden tests 评估 skill 的增益。

## 诚实 caveats

- 出题者同时是 taskhub seed 作者，存在作者偏差；后续用 L2 裸 agent 对照抵消一部分偏差。
- `k=1` 只能证明管线可跑和题目可解，不能给出稳定统计结论。
- 三个 bug 刻意放在 seed 自带测试的暗角，适合评测 e2e outcome，不适合作为真实覆盖率结论。

## L2 对照细节（预注册，2026-07-08，先于对照运行）

- `bare` 变体 = 一句通用助手指令（`variants/bare.md`），prompt 其余结构与 baseline 完全相同
  （同 issue 报告、同"落盘修复/写 fix-note/跑回归"输出要求）——单一变量 = skill 协议文本。
- H2（L2）：baseline 的 e2e_ok 均值 ≥ bare。若 hidden_pass 无差而 artifact_ok 有差，
  结论降级为"skill 的增益在过程契约而非修 bug 能力"（对简单 bug 这是合理预期——
  真差异预计出现在难题 g03 与过程指标上）。
- 规模：2 variants × 3 fixtures × k=3 = 18 次真实全流程，sonnet，claude-headless。

## P1 难 bug 预注册（2026-07-08，先于评测运行）

- H3：在 g04/g05/g06 这组三个难 bug 上，`baseline`（cs-issue skill）hidden_pass 高于
  `bare`。若 baseline 只在回归测试或修复说明质量上领先，则结论降级为过程收益。
- g04 覆盖判据 1 和 3：创建任务与改期两条入口都漏掉 due date 格式校验；症状依赖
  `MM/DD/YYYY` 这类特定日期形态。只修一条入口 hidden 仍红。
- g05 覆盖判据 2：用户看到的是 HTTP `completedAt` 返回值不可解析，误导路径是修
  camelCase/JSON 映射；真实根因在 workflow 存储了非 ISO 完成时间。只修 HTTP 映射
  hidden 仍红。
- g06 覆盖判据 3：症状依赖搜索调用传入 `tags=[]` 的边界形态；`tags=None` 和非空
  tag 过滤都可能正常，必须先复现调用差异。
