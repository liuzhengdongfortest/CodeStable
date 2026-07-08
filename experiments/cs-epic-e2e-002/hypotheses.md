# Hypotheses — cs-epic-e2e-002（roadmap-review 补漏，预注册）

## 背景
路 A（cs-epic-e2e-001）只测了 cs-epic 拆解的**首轮**（单次 planning），edge 覆盖 haiku baseline 0.78——首轮也漏 ~22% 边角子任务。但 cs-epic 的完整价值主张是**多阶段流程**：planning 后有 roadmap-review 环节（独立 reviewer 审查→挑漏项→修订）。路 A 砍掉了这一环、低估了 skill。路 B 测这一环。

## 评测
三阶段编排（api harness, haiku，避 sonnet 网关 504）：
1. planning：cs-epic 全文 + 需求 → roadmap_v1
2. review：treatment=cs-epic review protocol 的结构化审查 prompt（忠实 references/review/protocol.md 独立 reviewer 维度）/ control=泛泛"再检查一遍" → findings
3. revise：v1 + findings → roadmap_v2（两组同一 revise，只有 review 不同）
对 v1、v2_treatment、v2_control 各评 recall_judge（opus 语义）。3 fixture × k3。

## H5（主假设）
review→revise 能把 v1 漏的 edge 子任务补回：v2_recall > v1_recall。
**直接测量**：recovered = v1_missed ∩ v2_matched（漏项被补回数）。

## H5b（增量隔离）
v2_treatment recovered > v2_control recovered：cs-epic 的**结构化 review protocol**（审查维度 + 跨切面/失败路径提示）比泛泛"再想一次"补回更多漏项。否则 review 价值 = 单纯二次迭代，非 protocol 特有。

## 诚实 caveats
1. review prompt 只给通用审查维度（不点名具体漏项、不看 answer）——忠实隔离。
2. haiku 单模型 + 3 fixture × k3，[underpowered]；sonnet 待独立网络。
3. 编排是 cs-epic review 环节的**忠实抽取**（reviewer prompt 取自 protocol 58-73 行精神），非跑全流程（childDesign/goal 无关）。
4. 冒烟先验"review 能否挑出漏项"——挑不出则 H5 证伪，止损。
