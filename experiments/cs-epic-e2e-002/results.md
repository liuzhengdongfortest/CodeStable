# cs-epic-e2e-002 结果（路B：roadmap-review 补漏环节）

被测：`cs-epic` @ commit 11fa14a（issue#39 输入幂等修复**之前**的版本）。
三阶段编排 planning→review→revise（api harness, haiku）：v1 = cs-epic 首轮拆解；
treatment = cs-epic review protocol 结构化审查 / control = 泛泛"再检查一遍"；revise 两组同一。
recall_judge（opus 语义）。3 fixture × k3，**504 丢弃 4/9，有效 n=5**。

## Verdict：H5/H5b 证据不足，且发现 revise 损坏风险 [underpowered]

**诚实纠正**：k=1 诊断跑曾显示"treatment 三 fixture 全胜"——这是小样本乐观假象，**k=3 未复现**。

| 变体 | v1均 | v2均 | Δ | 补漏率 | revise 损坏 |
|---|---|---|---|---|---|
| treatment | 0.86 | 0.89 | **+0.03** | 4/5 | 1/5 行 |
| control | 0.86 | 0.80 | **−0.06** | 2/5 | 2/5 行 |

逐 fixture **自相矛盾**：
- e01: treatment 1.00→0.79、control 1.00→0.71（**满分基础上双双损坏**）
- e02: treatment 0.71→**1.00**、control 0.71→0.79（treatment 赢）
- e03: treatment 0.86→0.86、control 0.86→**1.00**（**control 反而赢**）

### 三条诚实结论

1. **H5（review 补漏有效）证据不足**：treatment Δ+0.03 近零、control Δ−0.06 负。补漏收益被 revise 损坏抵消。
2. **H5b（结构化 review 增量）方向支持但不可信**：Δ(T−C)=+0.09、损坏 1/5<2/5，方向偏向 treatment，但量级小、逐 fixture 矛盾（e03 反向）、n=5 [underpowered]。
3. **意外负面发现——revise 会损坏已有覆盖**（e01 满分→双降）：在合成任务+haiku 上，"根据 review 修订、重写完整拆解"这一步本身有丢项风险，两组都中招（treatment 略轻）。这是对"多阶段流程"的真实警示：修订不当会吃掉补漏收益。

## 测量受限（为什么信号不可信）

1. **504 丢弃 4/9**：sonnet 网关问题在多阶段串联下更致命（5 阶段任一 504 整条丢），haiku 也未能幸免，有效样本仅 5。
2. **recall_judge 判定抖动**：在 Δ=0.03~0.09 这种小差异下，同一份 v2 的 judge 判定噪声可能主导信号——e01 的满分→大跌，无法区分"真损坏"与"判定抖动"。
3. **revise prompt 让 haiku 重写整个拆解**：引入的重写噪声可能压过 review 的补漏信号。

## 与全系列一致的大结论

路A（首轮拆解 H4 弱阳性）+ 路B（多阶段 review 补漏证据不足 + revise 损坏）合起来印证：
**现代模型在合成大需求上的多阶段增益很难稳定测出，且流程本身可能引入噪声/损坏**。cs-epic 的 review 环节**未被证明**在此设置下带来可靠净收益——不是证明它没用，是当前证据（504 受限 + judge 抖动 + 天花板）测不出可信信号。

## P3（若要坐实）

1. 稳定网络消 504 → 拿满 k≥5 有效样本 + 补 sonnet。
2. revise prompt 加"**只增不减**"硬约束（保留 v1 所有项，只追加）→ 隔离补漏信号、消除损坏噪声。
3. 每份 v2 多次 judge 取多数 → 压掉判定抖动。
4. 提高补漏空间：选 v1 覆盖率低的更难需求（当前 haiku 首轮 0.71~1.00，天花板压缩了空间）。
