# cs-epic-e2e-001 结果（路 A：拆解覆盖度）

被测：`cs-epic` 大需求拆解。生成型 eval（api harness 产 roadmap 文本，不跑真仓库）。
3 大需求（e01 通知 / e02 审计权限 / e03 批量迁移），各 7 必需子任务（4 obvious + 3 edge）。
对照：baseline=cs-epic 全文注入 vs bare=一句资深工程师指令。k=3。
scorer：recall_judge（opus 语义，主判）+ planted_defect（token，仅作背离诊断）。

## Verdict：H4 弱阳性 [underpowered]

**cs-epic 的系统化拆解在"易漏的跨切面边角子任务"上有覆盖优势，但样本不足以定量。**
这是 e2e 系列（cs-issue/cs-feat 均天花板/NULL）**首个非天花板的正方向信号**。

### 数据（haiku，本网关唯一能产完整 roadmap 的模型）

| 变体 | obvious | EDGE | 成功 run |
|---|---|---|---|
| baseline (cs-epic) | 0.96 | **0.78** | 6/9 |
| bare (裸 agent) | 1.00 | **0.60** | 5/9 |

- obvious 两组≈天花板：现代模型（含 haiku）裸拆也能想到显眼子任务。
- **EDGE Δ+0.18**：判别面在边角子任务，方向正。

### 机制证据：逐 EDGE 子任务覆盖（比聚合数字更有说服力）

| edge 子任务（所属需求） | baseline | bare | Δ |
|---|---|---|---|
| CLI 操作的用户身份传递（e02 审计） | 0.33 | **0.00** | +0.33 |
| 批量操作 dry-run 预览变更（e03 迁移） | 0.50 | **0.00** | +0.50 |
| 部分失败回滚 + 任务 id 重映射（e03） | 0.50 | 0.33 | +0.17 |
| 通知偏好/去重幂等/送达状态（e01） | 1.00 | 1.00 | 0 |
| 越权审计留痕/审计历史查询（e02） | 1.00 | 1.00 | 0 |
| 导入冲突检测（e03） | 1.00 | 1.00 | 0 |

- 差异**集中在跨切面/非功能性边角**（身份传递、dry-run、回滚重映射）——bare 系统性漏（0.00），cs-epic 部分覆盖。
- **信号领域相关**：通知类(e01) edge 两组天花板；审计/迁移类(e02/e03)的跨切面 edge 才拉开。不是"所有大需求 cs-epic 都赢"。
- 样本 2–3 run/子任务，[anecdotal]——机制方向可信，量级不可信。

## 测量环境约束（诚实记录）

1. **sonnet 网关 504 无法测**：baseline-sonnet 成功 2/9、bare-sonnet **0/9**。sonnet 完整 roadmap（~3000 tok）生成耗时卡在第三方网关固定超时窗口；2048 截断时因返回快而全过。本机只有网关 `AUTH_TOKEN`、无官方 `API_KEY`，无法直连绕开。→ sonnet 是否复现 haiku 的 edge 优势，待独立网络环境验证（P3）。
2. **haiku 也有部分 504**（6/9, 5/9），进一步压低功效。

## 方法学发现（可复用，已回写效度铁律 8/9）

1. **[截断污染] 首轮 36/36 撞 `max_tokens=2048`，差点误导出 H4 NULL**。覆盖率实际测成了"2048 token 内塞得下多少子任务文本"——cs-epic 的 roadmap 格式更冗长、被砍得更狠。修 `adapter_api.py`（默认 8192 + `CS_EVAL_MAX_TOKENS` 覆盖）后 edge 优势才显现。→ **生成型 eval 必须校验 output 未撞 max_tokens 上限**（撞则数据作废）。
2. **[scorer 选型] planted_defect（token recall）对自然语言拆解低估 32pp**（全量均值 0.49 vs judge 0.81）。决定性案例：同一 roadmap，planted 判 recall=0.43（漏 4 项含 obvious），opus judge 判 1.0（7 项全覆盖）——措辞自由度高，token 匹配必漏。→ **拆解/生成型覆盖度只能用语义 judge，token recall 不可作 measured 下界**。

## P3 待办（坐实 H4）

1. 独立网络环境（消除 504）重跑 sonnet 双段 → 补第二模型，验 edge 优势跨模型复现。
2. 扩 fixture（尤其审计/迁移等跨切面重的需求）+ k≥5 → 把 [anecdotal] 机制证据提到 [measured]。
3. 路 B（全程 e2e）：单次生成砍掉了 cs-epic 的 roadmap-review 补漏环节；其"系统化拆解"的完整价值应在 planning→review 迭代中测，当前仅测首轮拆解已见正信号，review 环节预计放大差异。
