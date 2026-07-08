# cs-feat-e2e-001 hypotheses

## H3

在 feature 需求场景中，`baseline`（cs-feat skill）在 implicit hidden 上的通过率应高于
`bare`。explicit hidden 只覆盖需求明说行为，可能出现天花板效应：两个变体都能实现。

## Artifact

baseline 应产出 design 产物，fixture 使用 `artifact_glob` =
`.codestable/features/**/*design*` 判定。

## Caveats

- 出题者同时设计了 seed 与 hidden 边界，存在作者偏差；用 L2 bare 对照缓解。
- implicit 边界清单本身来自出题者对“专业实现”的判断，不代表唯一正确需求解释。
- 本实验把 explicit 与 implicit 拆成独立文件，便于 scorer 读取隐含覆盖率。
- 2026-07-08 修订：需求文本只保留接口契约，语义边界恢复为 true implicit，用字面实现
  与资深实现双轨自证校准 H3。
