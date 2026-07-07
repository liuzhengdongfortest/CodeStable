#!/usr/bin/env python3
"""optimize：autoresearch OCA 循环的**确定性测量+记账+收敛引擎**。

分工（对齐 BAIME）：变体的创意生成是 agent 的活（照 references/optimize/protocol.md
写 experiments/<name>/variants/iter-<n>.md）；本脚本负责：跑 eval → 算 V_instance / V_meta →
keep/kill → 写 iteration-<n>.md（带 [measured]/[soft]）→ 收敛检查。不 Task-launch BAIME
iteration-executor（它调不到本地 runner）。

CLI:
  optimize.py --experiment E [--max-iterations 3]
  # iter-0 评 baseline；iter-n 若存在 variants/iter-<n>.md 则评之，否则复用 baseline 并标注「无新变体」。
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
from statistics import mean

sys.dont_write_bytecode = True

_SCRIPTS = Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

import runner  # noqa: E402
from _model import MEASURED, SOFT, render_tagged, tagged, write_json  # noqa: E402
from config import ExperimentConfig, load_config, repo_root  # noqa: E402
from fixtures import load_fixtures  # noqa: E402

CONVERGENCE_STANDARD = 0.80       # V_instance ∧ V_meta 双阈值
CONVERGENCE_META_INSTANCE = 0.55  # meta-focused：V_meta≥0.80 且 V_instance≥0.55


# ---------- 双层价值函数 ----------

def v_instance(agg_scores: dict, weights: dict[str, float]) -> dict:
    """加权 measured 分数（默认只用 measured 的 recall/dod_pass，保 V_instance 为 measured）。"""
    num, den, tags = 0.0, 0.0, set()
    for name, w in weights.items():
        t = agg_scores.get(name)
        if t is None:
            continue
        num += w * float(t["value"])
        den += w
        tags.add(t["tag"])
    if den == 0:
        return tagged(0.0, SOFT, evidence="no scoring signal")
    tag = MEASURED if tags == {MEASURED} else SOFT
    return tagged(round(num / den, 4), tag, evidence=f"weighted over {sorted(weights)}")


def v_meta_experiment(exp_dir: Path, config: ExperimentConfig, k: int, fixtures) -> tuple[dict, dict]:
    """BAIME 四机械分量（全 [measured]）：预注册 / 统计功效 / oracle 校准 / 混杂控制。"""
    comp: dict[str, bool] = {}
    comp["pre_registration"] = _preregistered(exp_dir)
    per_class_ok = _min_class_count(exp_dir, config.fixture_classes) >= 8
    comp["statistical_power"] = (k >= 5) and per_class_ok
    comp["oracle_calibration"] = (exp_dir / "calibration.md").is_file()
    comp["confound_control"] = _confound_ok(config)
    score = sum(1 for v in comp.values() if v) / 4.0
    return tagged(round(score, 4), MEASURED, evidence=f"{sum(comp.values())}/4 components"), comp


def _preregistered(exp_dir: Path) -> bool:
    """hypotheses.md 已 git 提交，且提交时间早于 artifacts/runs 首个产物。"""
    hyp = exp_dir / "hypotheses.md"
    if not hyp.is_file():
        return False
    root = repo_root()
    try:
        out = subprocess.run(["git", "log", "-1", "--format=%ct", "--", str(hyp.relative_to(root))],
                             cwd=root, text=True, capture_output=True, check=False)
        committed = int(out.stdout.strip()) if out.stdout.strip() else None
    except (ValueError, subprocess.SubprocessError):
        committed = None
    if committed is None:
        return False  # 未提交 = 未冻结 → 不给分（诚实）
    runs = exp_dir / "artifacts" / "runs"
    if runs.is_dir():
        mtimes = [p.stat().st_mtime for p in runs.rglob("*") if p.is_file()]
        if mtimes and committed > min(mtimes):
            return False  # 提交晚于首个 run → provenance 破坏
    return True


def _min_class_count(exp_dir: Path, classes: list[str]) -> int:
    counts = [len(list((exp_dir / "fixtures" / c).glob("*.json"))) for c in classes]
    counts = [c for c in counts if c > 0]
    return min(counts) if counts else 0


def _confound_ok(config: ExperimentConfig) -> bool:
    if "llm_judge" not in config.scorers:
        return True  # 不用 judge，无同源偏差
    jm = (config.judge_model or "").strip()
    return bool(jm) and jm not in set(config.model_list)


# ---------- 迭代 ----------

def _run_variant(config: ExperimentConfig, variant: str, fixtures, k: int, exp_dir: Path | None = None) -> dict:
    cells = [(variant, h, m) for h in config.harnesses
             for m in (config.model_list or (["mock-model"] if "mock" in h else ["default"]))]
    results = runner.run(config, fixtures, cells, config.scorers, k, exp_dir)
    agg = runner.aggregate(config, results)
    return agg.get(variant, {"scores": {}, "metrics": {}, "n": 0})


def _variant_for(exp_dir: Path, n: int) -> str:
    """iter-0=baseline；iter-n 若有 variants/iter-<n>.md 则用之，否则复用 baseline。"""
    if n == 0:
        return "baseline"
    cand = exp_dir / "variants" / f"iter-{n}.md"
    return f"iter-{n}" if cand.is_file() else "baseline"


def convergence(vi: float, vm: float) -> tuple[bool, str]:
    if vi >= CONVERGENCE_STANDARD and vm >= CONVERGENCE_STANDARD:
        return True, "standard"
    if vm >= CONVERGENCE_STANDARD and vi >= CONVERGENCE_META_INSTANCE:
        return True, "meta-focused"
    return False, "not-converged"


def write_iteration(exp_dir: Path, n: int, variant: str, vi: dict, vm: dict,
                    comp: dict, decision: str, converged: bool, mode: str, agg: dict) -> None:
    lines = [
        f"# iteration-{n} — variant `{variant}`", "",
        "## 价值（认知诚实标注）",
        f"- V_instance = {render_tagged(vi)}",
        f"- V_meta_experiment = {render_tagged(vm)}",
        "",
        "## V_meta 分量",
        *[f"- {name}: {'pass' if ok else 'fail'}" for name, ok in comp.items()],
        "",
        "## 决策",
        f"- keep/kill: **{decision}**",
        f"- 收敛: {'是' if converged else '否'}（模式 {mode}；判据 V_instance∧V_meta ≥ {CONVERGENCE_STANDARD}）",
        "",
        "## 本轮分数",
        *[f"- {name}: {render_tagged(t)}" for name, t in sorted(agg.get("scores", {}).items())],
        "",
    ]
    (exp_dir / f"iteration-{n}.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="cs-skill-lab optimize（OCA 测量+记账+收敛）")
    p.add_argument("--experiment", required=True)
    p.add_argument("--max-iterations", type=int, default=3)
    p.add_argument("--weights", help="V_instance 权重 JSON，如 '{\"recall\":1.0}'")
    args = p.parse_args(argv)

    exp_dir = Path(args.experiment).resolve()
    config = load_config(exp_dir)
    k = config.k
    fixtures = load_fixtures(exp_dir, config.fixture_classes)
    import json as _json
    weights = _json.loads(args.weights) if args.weights else config.raw.get("v_instance_weights", {"recall": 1.0})

    best_vi = -1.0
    history = []
    for n in range(args.max_iterations):
        variant = _variant_for(exp_dir, n)
        agg = _run_variant(config, variant, fixtures, k, exp_dir)
        vi = v_instance(agg.get("scores", {}), weights)
        vm, comp = v_meta_experiment(exp_dir, config, k, fixtures)
        decision = "keep" if vi["value"] > best_vi else "kill"  # 仅严格改进才采纳为新 best
        if decision == "keep":
            best_vi = vi["value"]
        converged, mode = convergence(vi["value"], vm["value"])
        write_iteration(exp_dir, n, variant, vi, vm, comp, decision, converged, mode, agg)
        history.append({"iter": n, "variant": variant, "v_instance": vi, "v_meta": vm,
                        "decision": decision, "converged": converged, "mode": mode})
        print(f"  iter-{n} [{variant}] V_instance={render_tagged(vi)} V_meta={render_tagged(vm)} "
              f"→ {decision}{' CONVERGED('+mode+')' if converged else ''}")
        if converged:
            break

    write_json(exp_dir / "artifacts" / "analysis" / f"optimize-{config.name}.json", {"history": history})
    conv = history[-1]["converged"]
    print(f"[cs-skill-lab] optimize 完成 {len(history)} 轮；收敛={conv}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
