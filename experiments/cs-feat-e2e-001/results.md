# Results — cs-feat-e2e-001（三轮出题迭代 + 终版矩阵，2026-07-08）

evidence：`artifacts/runs/`（feat-* = v2 段，featv3-* = f02/f03 终版段）；全 [measured]。

## 终 verdict（f01 v2 段 + f02/f03 v3 段，n=9/格）

| 段 | explicit | implicit | 回归 | design 产物 |
|---|---|---|---|---|
| skill × sonnet | 1.00 | 0.67 | 1.00 | 0.11 |
| bare × sonnet | 1.00 | 0.67 | 1.00 | 0.00 |
| skill × haiku | 1.00 | 0.56 | 1.00 | **1.00** |
| bare × haiku | 1.00 | 0.44 | 1.00 | 0.00 |

逐 feature implicit（难度梯度）：f01 四格全过（csv.writer 免费，判别力≈0）；
f02 sonnet 两组全过、**haiku：skill 0.67 vs bare 0.33（+0.33，唯一正向 H3 信号）**；
f03 四格全挂同一断言（tag 大小写归一/多 tag 各计——资深自证可过的真隐含，无人处理）。

## H3 裁决（design 挖隐含需求的价值）

- **sonnet：NULL**（implicit 无差 0.67=0.67）——能力足以覆盖中难隐含，无需 design 辅助。
- **haiku：方向性弱正**（+0.11 总体 / f02 上 +0.33），n=3/格 **[underpowered]**——与
  routing 层 Measured Rule 3 同构（增益在非顶级模型），但样本不足以 CONFIRMED。
- f03 揭示 design 流程的上限：haiku 走了完整 design（产物 1.00）仍没想到 tag 归一——
  **design 文档质量 ≠ 隐含边界覆盖**（"design 里列没列该边界"的分诊记 P3）。

## 稳定副产品结论

- **流程遵守跨模型差异（三轮复现）**：haiku+skill design 产物 1.00 vs sonnet+skill 0.11
  （豁免块点名"产物照常落盘"后仍 0.11→sonnet 在明确需求下持续跳过 cs-feat 流程产物，
  这是真实模型行为非环境混杂——消混杂记录：豁免块修正贡献 0→0.22）。
- explicit / 回归全象限天花板（与 cs-issue 同构）。

## 三轮出题迭代（方法学资产，已固化铁律 6/7）

1. 接口锁定（`--output` vs 位置参数）→ 接口契约显式进需求
2. 显式化过度（隐含全暴露，H3 被摧毁）→ 显式/隐含分治 + 双轨自证（字面红=真隐含）
3. 观测通道纠缠（`untagged` 字面桶名）→ implicit 只测状态/数据行为
另：GoalHandoff 环境交互（headless 无 driver，agent 守规矩退出）→ 豁免块 driver 条款。

## P3 待办

- scorer hidden 按测试粒度（当前文件粒度掩盖部分通过）
- f03 类"高难隐含"的 design 内容分诊（design 列了边界但实现没跟上 vs 根本没想到）
- H3 haiku 信号补功效：f02 类中难场景扩容 + k≥5
