# Results — cs-issue-e2e-001（P0：outcome 层首批数据 + L2 对照）

evidence：`artifacts/runs/e2e-*.json`；判分全 [measured]（hidden tests / 回归 / 产物存在性）。

## 冒烟（2026-07-08）

g01 × sonnet × claude-headless × k=1：e2e_ok = **1.0**（hidden 红→绿、回归绿、fix-note 齐）——
seed→注入→真 agent 修复→机械判分全链首通。

## L2 对照 verdict（3 bugs × k=3 × sonnet，n=9/组，零 error）

| 变体 | hidden_pass | 回归 | artifact | e2e_ok | wall | turns | out tokens |
|---|---|---|---|---|---|---|---|
| baseline（cs-issue skill）| 1.000 | 1.000 | 1.000 | 1.000 | 94.4s | 14.7 | 4661 |
| bare（一句通用指令）| 1.000 | 1.000 | 1.000 | 1.000 | 76.3s | 12.0 | 3515 |

**结果层：双满分，天花板效应（ceiling）**——三个 bug（含"难题"g03 跨文件映射）对 sonnet
都是一次修复，该难度下**无法检测** skill 增益（是 ceiling，不是 absence of value 的证据）。

**过程层：skill 在此象限是净开销**——baseline 多花 ~24% wall / ~23% turns / ~33% output
tokens（report/analyze/fix-note 流程产物的成本），未换来任何结果质量差。

## 诚实结论（对预注册 H2 的裁决）

1. H2 判定：落在预注册的两个分支之外（全指标无差）→ **该难度水平下 NULL**。
2. 与 routing 层互证：cs-issue 在 routing 层也是 ±0（规则简单清晰）。两层证据一致：
   **「强模型 × 简单 bug」象限，cs-issue 的流程收益≈0、成本 +25%~33%**。
3. skill 的价值假设被收窄到（P1 待验证）：难 bug（多根因/误导症状/需系统化诊断）、
   非顶级模型（haiku——routing 层 Measured Rule 3 的同构预期）、流程产物的长期价值
   （fix-note 对后人，本实验不可测）。

## 方法学缺陷（P1 必修）

- **共享 prompt 模板泄题**：`build_e2e_prompt` 的输出要求把「写 fix-note / 跑回归」
  给了两组——bare 组照做导致 artifact/回归指标失去判别力。P1：bare 组模板只保留
  「处理 issue」，把过程要求还给 skill 文本本身。
- 难度天花板：P1 需种"复现困难/多根因/症状误导"级 bug，并加 haiku 拉开能力边界。
- g02/g03 hidden 测试需 bind localhost（本机可跑；受限沙箱需提权，记录在案）。

## P1 verdict（2026-07-08：模板修复 + 难 bug g04-06 + haiku，54 次，零 error）

| 难度 | 模型 | 变体 | hidden | 回归 | artifact | turns | out-tok |
|---|---|---|---|---|---|---|---|
| hard | sonnet | skill | 1.000 | 1.000 | 0.333 | 13 | 4.7k |
| hard | sonnet | bare | 1.000 | 1.000 | 0.000 | 11 | 3.0k |
| hard | haiku | skill | 1.000 | 1.000 | 0.778 | 26 | 8.6k |
| hard | haiku | bare | 1.000 | 1.000 | 0.000 | 20 | 6.5k |
| easy | haiku | skill | 1.000 | 1.000 | 0.889 | 27 | 9.7k |
| easy | haiku | bare | 1.000 | 1.000 | 0.000 | 21 | 6.8k |

1. **修复能力：全象限天花板**。协同根因（g04，单点修复自证仍红）、症状误导（g05）、
   复现边界（g06）对 sonnet 和 haiku 都是 k=3 全过。**在千行级代码库+明确症状的合成
   bug 上，cs-issue 的可测价值不在"帮模型修对 bug"**——现代模型（含 haiku）本身就能修。
2. **过程契约是真实差异面（模板修复后 artifact 指标复活）**：bare 三格 27 次零产物
   （泄题修复生效的证明）；skill 组 0.33~0.89。
3. **分诊（手动复现 g04×sonnet，保留 workdir 查实）**：sonnet artifact=0 是真没写——
   `.codestable/` 空树、修复与自加回归测试完美。**但归因混杂了我方评测环境缺口：seed
   没有 `.codestable/`（未 onboard）**，cs-issue preflight 规定缺 attention→先 onboard，
   sonnet 跳过产物流程是对 skill 规则的一种合理解读；haiku 机械照写反而"得分"。
   → sonnet 0.33 vs haiku 0.78 的差异**不能**下"sonnet 不守流程"的结论 [confounded]。
4. 成本：skill 组 +18~30% turns/tokens（与 P0 一致）。

### P2 必修（按序）
1. **seed 补 `.codestable/`**（attention.md + issues 骨架，进 build-seed 阶段）——P0 计划
   第 2 步的欠账；补齐后 artifact 指标才公平，重跑 P1 的 artifact 列。
2. scorer evidence 留 `.codestable/` 目录快照（本次分诊靠手动复现才定位，成本高）。
3. 修复能力若要测出差异：需"症状模糊/复现需多步/跨仓库知识"级 bug，或转向 cs-feat
   （设计缺口类任务天花板更高）。

## P2 消混杂 verdict（2026-07-08：seed 补 .codestable/ 后重跑 baseline 三段，27 次零 error）

| 段 | onboard 前 artifact | onboard 后 artifact |
|---|---|---|
| hard × sonnet | 0.333 | **1.000** |
| hard × haiku | 0.778 | **1.000** |
| easy × haiku | 0.889 | **1.000** |

1. **[confounded] 判定正确，混杂消除**：sonnet 低 artifact 是 seed 未 onboard 的环境缺口，
   非"不守流程"。反转：sonnet 当时是**更严格遵守 skill 规则**（preflight 缺 attention →
   不建产物体系）；haiku 机械照写反而在错误环境"得分"。onboard 后两者全满分。
2. **效度铁律 2 的 outcome 层实证**（与 routing 层 bare-input 0.31→0.92 同构）：skill 必须
   在其设计环境（onboarded repo）中评测，否则产物类指标失真可达 3 倍。
3. **cs-issue outcome 层最终结论**：修复能力全象限天花板（此复杂度合成 bug 测不出差异）；
   **过程契约是可测且完全可靠的增益**（onboard 环境下 skill 组 27/27 产物落盘 vs 裸 agent
   27/27 零产物）；成本 +20~30% tokens。**skill 本体经两层评测无需任何修改**——e2e 同时
   验证了 routing 层重构版在真实执行中的健壮性（第三层互证）。
