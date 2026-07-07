# iteration-{n} — variant `{variant}`

（本文件由 `scripts/optimize.py` 自动生成；此模板说明字段含义。）

## 价值（认知诚实标注）
- V_instance = {value} [measured|soft]   ← 任务质量，加权 measured 分数
- V_meta_experiment = {value} [measured]  ← 方法质量，四机械分量/4

## V_meta 分量
- pre_registration: pass|fail   ← hypotheses.md 已提交且早于首个 run
- statistical_power: pass|fail  ← k≥5 且每类 n≥8
- oracle_calibration: pass|fail ← calibration.md 存在
- confound_control: pass|fail   ← judge_model 独立于被测 model

## 决策
- keep/kill: keep（严格改进→采纳为新 best）| kill（无改进）
- 收敛: 是|否（模式 standard|meta-focused|not-converged）

## 本轮分数
- {scorer}: {value} [tag]

## Observe（下一轮方向）
- instance 差距: ...
- meta 差距: ...
