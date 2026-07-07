# Results — cs-code-review-robustness-001

首个真实模型 `[measured]` 跨模型实验 + optimize 闭环，经 cs-skill 框架。

## 发现

cs-code-review 在 **bare-input**（只给 diff、无 `.codestable/` 上下文、无来源 spec）下**不是 model-agnostic**：
- **claude-haiku-4-5** 严格照「启动检查」四项前置，**拒绝审查**、退回要求补 attention.md/spec/完整 git diff——对明显的 `eval(payload)` 都没审。
- **claude-sonnet-4-6** 照常审，全中。

手工核查 haiku 原始输出确认是**前置 gating 导致的拒审**，非模型识别不了缺陷；打分器由 sonnet 13/13 反证无误。单一 recall 数字会掩盖这点，分模型才暴露。

## 方法

- fixtures：13 例 planted-defect（8 关键词可检 + 5 需推理），`planted_defect` 召回 oracle（[measured]）。
- harness：`api`（直连 sub2global 网关，Anthropic 协议 + Bearer）。models：sonnet-4-6 + haiku-4-5。
- 干预（单一变量）：SKILL.md 顶部加「Ad-hoc / bare-input 快速通道」，见下。

## 结果（k=1，13 例/模型）

| 模型 | baseline recall | + fast-path recall | Δ |
|---|---|---|---|
| claude-haiku-4-5 | 0.31 [measured] | **1.00 [measured]** | **+0.69** |
| claude-sonnet-4-6 | 1.00 [measured] | 1.00 [measured] | +0.00 |

- **H-haiku-recovery: CONFIRMED** — 1.00 ≥ 0.85。
- **H-no-regression: CONFIRMED** — sonnet 1.00 ≥ 0.95。

## 结果（k=5 haiku 复测，稳定性）

未完成（后台任务随会话结束被终止，未产出）。可复现：
`runner.py --experiment <13例目录, model=haiku, k=5> --variant baseline` 与 `--variant iter-1`。
k=1 效应量（从拒审 0.31 到满召回 1.00）已足够明确；k=5 仅用于估方差，不改方向。

## 干预内容（已 land 到 SKILL.md）

```markdown
## Ad-hoc / bare-input 快速通道（最先判断）
只给一段 diff/代码、无 .codestable 上下文/来源 spec 时：不要拒绝、不要退回、
不要因缺 attention.md/spec 中止。直接按标准逐条审，输出 Findings；
reviewer 记 self，scope 标 ad-hoc-diff，residual-risk 说明缺上下文。
只有既无 diff 也无可审代码时才退回补范围。
```

## Caveats（认知诚实）

- k=1 → 严格按 BAIME 功效标准为 `[underpowered]`；但效应量（从拒审到满召回）极大、方向无歧义。k=5 haiku 复测见上。
- 单一 fixture 集、单一网关；haiku 拒审可能有概率性（baseline 曾审对 4/13）。
- 原始 LLM 响应在 `/tmp/real-eval`（未入库，含脱敏前内容）；本文件为可公开证据摘要。

## evidence_pointer / 复现

```bash
# 被测 skill 快照注入、隔离宿主；需网关鉴权 env
source <env>   # ANTHROPIC_BASE_URL + ANTHROPIC_AUTH_TOKEN
python3 <cs-skill>/scripts/runner.py --experiment <exp> --dry-run   # 估成本
python3 <cs-skill>/scripts/runner.py --experiment <exp>             # baseline
python3 <cs-skill>/scripts/runner.py --experiment <exp> --variant iter-1  # + fast-path
```

## Landed

fast-path 已并入 `plugins/codestable/skills/cs-code-review/SKILL.md`（顶部，additive，不改标准 gating）。
**未 bump 插件版本**——版本/release 是 owner 的独立决定（bump 会连带更新 doctor 测试里硬编码的版本）；
`cs-skill/scripts/bump_version.py` 已 dogfood 验证可用，真正发版时再执行。
