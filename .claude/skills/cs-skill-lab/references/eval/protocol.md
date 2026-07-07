# eval stage 协议

对某个 cs skill 跑「fixtures × models × harnesses」评测，产出带 tag 的 measured 分数与证据。评测执行引擎在 `scripts/`，被测 SKILL.md 以快照文本注入 prompt（隔离宿主已装版本）。

## 何时进入

- 已有 `experiments/{skill}-{NNN}/fixtures/`，但缺 `artifacts/analysis/*-results.json`。
- optimize 生成新变体后需要复测。
- release 前跑回归 baseline。

## 1. 声明实验

`experiments/{skill}-{NNN}/config.json`：

```json
{
  "name": "cs-code-review-001",
  "skill_under_test": "cs-code-review",
  "variants": ["baseline"],
  "model_list": ["claude-opus-4-8", "claude-sonnet-4-6"],
  "k": 5,
  "harnesses": ["claude-headless"],
  "scorers": ["planted_defect", "llm_judge"],
  "fixture_classes": ["planted-defect", "golden"],
  "budget_usd": 50.0,
  "judge_model": "claude-sonnet-4-6"
}
```

- `variants`：`baseline`=当前仓库被测 skill 的 SKILL.md；其余=optimize 产出的 `experiments/{name}/variants/<v>.md`。
- `inject_context`（**效度关键，默认 true**）：cs skills 为已 onboard 的 `.codestable/` 仓库设计（启动检查要 attention.md / 来源 spec / git diff）。评测须在 prompt 里补齐这套 onboard 上下文，否则测到的是「skill 在错误环境下拒绝执行」的假象而非真实能力（实测：cs-code-review haiku bare=0.31 → 补上下文=0.92）。设 `false` 只用于专门测「bare-input/ad-hoc 健壮性」。
- `model_list` ≥2（跨模型一致性，BAIME 硬约束）。`judge_model` 须独立于被测 model。

## 2. 作 fixtures

`fixtures/<class>/<id>.json`，字段 `id / answerType / answer / task`：

- `answerType: findings-recall`：`answer` 是应被发现的缺陷列表；scorer=`planted_defect` 按 token 重叠判召回。
- `answerType: dod-gate`：给 `checklist_path`，scorer=`dod_gate` 跑 checklist 命令判 pass/fail。
- `answerType: dimensions-judge`：scorer=`llm_judge` 按 8 维 rubric 两轴打分。
- `task`：`{kind: review|fix|audit, diff, spec}`；`kind` 决定 buildprompt 分派。

每类 `n ≥ 8` 才有统计功效；否则结论标 `[underpowered]`。planted-defect 应含**关键词可检**与**需推理**两种缺陷，避免只测到关键词匹配。

## 3. 预注册与冻结

写 `hypotheses.md`（`H-<id>: metric ≥ threshold`），**先 git commit 再跑任何 LLM**——provenance 由 `tests/test_cs_skill_convergence.py` 校验。

## 4. 跑评测

```bash
# 先估成本（多模型必做）
python3 {skill_dir}/scripts/runner.py --experiment experiments/{skill}-{NNN} --dry-run
# 正式跑（超预算需 --confirm）
python3 {skill_dir}/scripts/runner.py --experiment experiments/{skill}-{NNN}
# 快速探路：单 harness/model、低 k
python3 {skill_dir}/scripts/runner.py --experiment experiments/{skill}-{NNN} --harness mock --k 1
```

分层省钱：确定性 scorer（planted_defect / dod_gate）先跑，`llm_judge` 只在候选变体上跑；cheap model 探路，贵 model 只做终判。

## 5. 读结果

`artifacts/analysis/exp-{name}-results.json`：

- `aggregate.<variant>.scores.<name>`：`{value, tag, evidence}`，tag=`measured` 表示 oracle 可验。
- `aggregate.<variant>.metrics`：`wall_ms/turns`=`[measured]`，`*_tokens/cost_usd` 视 harness 是否回传 usage 定 `measured`/`soft`。
- `runs[]`：逐 cell 的 `scores/evidence/status`，`evidence` 含 `matched/missed`。

把人读摘要写 `results.md`，给出 `evidence_pointer` 指向该 json。

## 退出条件

- [ ] config.json、fixtures、hypotheses.md 落盘且 hypotheses 已 git commit。
- [ ] `--dry-run` 成本在预算内（或已 `--confirm`）。
- [ ] `artifacts/analysis/*-results.json` 产出，分数带 tag。
- [ ] `results.md` 有摘要与 evidence_pointer。
- [ ] 跨模型跑了 ≥2 model，或明确标注为 `[underpowered]` 探路。
