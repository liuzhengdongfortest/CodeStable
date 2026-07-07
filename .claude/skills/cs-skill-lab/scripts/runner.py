#!/usr/bin/env python3
"""cs-skill-lab eval runner：跨 variant×harness×model×k 执行被测 skill，打分，写 results.json。

用法：
  python3 runner.py --experiment experiments/cs-code-review-001 [--harness mock] \
      [--model M] [--scorer planted_defect] [--k 1] [--dry-run] [--confirm] [--out PATH]

隔离：被测 SKILL.md 以快照文本注入 prompt（config.resolve_variant_text），每 cell 独立 tmp workdir。
成本：多模型真实运行前用 --dry-run 估算；超 budget_usd 需 --confirm。
"""

from __future__ import annotations

import argparse
import sys

sys.dont_write_bytecode = True  # 不污染 plugin 包（check-plugin-package 禁 __pycache__）

import tempfile
from pathlib import Path
from statistics import mean
from typing import Any

_SCRIPTS = Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

import harness as harness_pkg          # noqa: E402
import metrics                          # noqa: E402
import scorers as scorers_pkg          # noqa: E402
from _model import EvalResult, MEASURED, SOFT, UNDERPOWERED, render_tagged, tagged, write_json  # noqa: E402
from buildprompt import build_prompt   # noqa: E402
from config import ExperimentConfig, judge_issues, load_config, repo_root, resolve_variant_text  # noqa: E402
from fixtures import load_fixtures      # noqa: E402


def _agg_tag(tags: set[str]) -> str:
    """聚合认知诚实 tag：全 measured 才 measured；含 soft 则 soft；否则 underpowered。"""
    if tags == {MEASURED}:
        return MEASURED
    if SOFT in tags:
        return SOFT
    return UNDERPOWERED


def _models_for(config: ExperimentConfig, override: str | None, harness: str) -> list[str]:
    if override:
        return [override]
    if config.model_list:
        return config.model_list
    return ["mock-model"] if harness == "mock" else ["default"]


def build_matrix(config: ExperimentConfig, args) -> list[tuple[str, str, str]]:
    variants = [args.variant] if args.variant else config.variants
    harnesses = [args.harness] if args.harness else config.harnesses
    cells = []
    for variant in variants:
        for h in harnesses:
            for model in _models_for(config, args.model, h):
                cells.append((variant, h, model))
    return cells


def dry_run(config: ExperimentConfig, fixtures, cells, k: int, exp_dir: Path | None = None) -> dict[str, Any]:
    total = 0.0
    per_cell = []
    for variant, h, model in cells:
        text = resolve_variant_text(config, variant, repo_root(), exp_dir)
        cell_cost = 0.0
        for fx in fixtures:
            prompt = build_prompt(fx, text)
            cell_cost += metrics.estimate_cost(prompt, model) * k
        per_cell.append({"variant": variant, "harness": h, "model": model, "est_usd": round(cell_cost, 4)})
        total += cell_cost
    return {"est_total_usd": round(total, 2), "per_cell": per_cell, "budget_usd": config.budget_usd,
            "fixtures": len(fixtures), "cells": len(cells), "k": k}


def run(config: ExperimentConfig, fixtures, cells, scorer_names, k: int, exp_dir: Path | None = None) -> list[EvalResult]:
    results: list[EvalResult] = []
    root = repo_root()
    for variant, h, model in cells:
        text = resolve_variant_text(config, variant, root, exp_dir)
        harness = harness_pkg.get_harness(h)
        for fx in fixtures:
            prompt = build_prompt(fx, text)
            for ki in range(k):
                with tempfile.TemporaryDirectory(prefix="cs-eval-") as tmp:
                    hr = harness.invoke(prompt, model, Path(tmp), timeout_s=600)
                er = EvalResult(fixture_id=fx.id, variant=variant, model=model, harness=h, k_index=ki)
                er.metrics = metrics.capture(hr, prompt)
                if hr.error:
                    er.status = "error"
                    er.evidence.append({"error": hr.error})
                    results.append(er)
                    continue
                # 打分：只跑与 fixture.answer_type 匹配的 scorer
                statuses = []
                for sname in scorer_names:
                    if not scorers_pkg.applies(sname, fx.answer_type):
                        continue
                    sc = scorers_pkg.get_scorer(sname)(fx, hr, config, root)
                    er.scores.update(sc.get("scores", {}))
                    er.evidence.extend(sc.get("evidence", []))
                    statuses.append(sc.get("status", "passed"))
                er.status = "failed" if "failed" in statuses else "passed"
                results.append(er)
    return results


def aggregate(config: ExperimentConfig, results: list[EvalResult]) -> dict[str, Any]:
    agg: dict[str, Any] = {}
    for variant in {r.variant for r in results}:
        rs = [r for r in results if r.variant == variant]
        score_names = {name for r in rs for name in r.scores}
        scores = {}
        for name in score_names:
            vals = [r.scores[name]["value"] for r in rs if name in r.scores]
            tags = {r.scores[name]["tag"] for r in rs if name in r.scores}
            if vals:
                scores[name] = tagged(round(mean(vals), 4), _agg_tag(tags), evidence=f"mean over n={len(vals)}")
        metric_names = {name for r in rs for name in r.metrics}
        metrics = {}
        for name in metric_names:
            vals = [r.metrics[name]["value"] for r in rs if name in r.metrics and isinstance(r.metrics[name]["value"], (int, float))]
            tags = {r.metrics[name]["tag"] for r in rs if name in r.metrics}
            if vals:
                metrics[name] = tagged(round(mean(vals), 2), _agg_tag(tags), evidence=f"mean n={len(vals)}")
        agg[variant] = {"scores": scores, "metrics": metrics, "n": len(rs)}
    return agg


def write_results_md(exp_dir: Path, config: ExperimentConfig, agg: dict, cells: list, k: int, json_path: Path) -> None:
    """人读摘要 + evidence_pointer。收敛模式由 optimize 阶段补写。"""
    try:
        pointer = json_path.relative_to(exp_dir)
    except ValueError:
        pointer = json_path
    lines = [
        f"# Results — {config.name}", "",
        f"- skill_under_test: `{config.skill_under_test}`",
        f"- cells: {len(cells)}（variant×harness×model）× k={k}",
        f"- evidence_pointer: `{pointer}`",
        "- generated_by: cs-skill-lab/scripts/runner.py", "",
        "## Aggregate（每个数值带认知诚实 tag）", "",
        "| variant | 指标 | 值 |", "|---|---|---|",
    ]
    for variant, a in sorted(agg.items()):
        for name, t in sorted(a.get("scores", {}).items()):
            lines.append(f"| {variant} | {name} | {render_tagged(t)} |")
        for name, t in sorted(a.get("metrics", {}).items()):
            lines.append(f"| {variant} | {name} | {render_tagged(t)} |")
    lines += ["", "## 收敛模式", "", "（optimize 阶段填：V_instance∧V_meta 是否达标、留/杀了哪些变体）", ""]
    (exp_dir / "results.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="cs-skill-lab eval runner")
    p.add_argument("--experiment", required=True)
    p.add_argument("--harness")
    p.add_argument("--model")
    p.add_argument("--variant")
    p.add_argument("--scorer", action="append", help="可多次；默认取 config.scorers")
    p.add_argument("--k", type=int)
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--confirm", action="store_true", help="确认超预算仍执行")
    p.add_argument("--out")
    args = p.parse_args(argv)

    exp_dir = Path(args.experiment).resolve()
    config = load_config(exp_dir)
    k = args.k if args.k is not None else config.k
    scorer_names = args.scorer or config.scorers
    fixtures = load_fixtures(exp_dir, config.fixture_classes)
    if not fixtures:
        print(f"[cs-skill-lab] 无 fixtures：{exp_dir}/fixtures/{config.fixture_classes}", file=sys.stderr)
        return 2
    cells = build_matrix(config, args)

    for issue in judge_issues(config):
        print(f"[cs-skill-lab][judge] {issue}", file=sys.stderr)

    est = dry_run(config, fixtures, cells, k, exp_dir)
    print(f"[cs-skill-lab] 预估成本 ${est['est_total_usd']} / 预算 ${est['budget_usd']} "
          f"(cells={est['cells']} × fixtures={est['fixtures']} × k={k})")
    if args.dry_run:
        if args.out:
            write_json(Path(args.out), est)
        return 0
    if est["est_total_usd"] > config.budget_usd and not args.confirm:
        print(f"[cs-skill-lab] 阻断：预估 ${est['est_total_usd']} 超预算 ${config.budget_usd}；加 --confirm 放行。", file=sys.stderr)
        return 3

    results = run(config, fixtures, cells, scorer_names, k, exp_dir)
    agg = aggregate(config, results)
    out_path = Path(args.out) if args.out else exp_dir / "artifacts" / "analysis" / f"exp-{config.name}-results.json"
    payload = {
        "experiment": config.name,
        "skill_under_test": config.skill_under_test,
        "generated_by": "cs-skill-lab/scripts/runner.py",
        "k": k, "scorers": scorer_names,
        "cells": [f"{v}|{h}|{m}" for v, h, m in cells],
        "aggregate": agg,
        "runs": [r.to_dict() for r in results],
    }
    write_json(out_path, payload)
    if not args.out:  # 默认路径运行才写 results.md 到实验目录（测试传 --out 不 clobber）
        write_results_md(exp_dir, config, agg, cells, k, out_path)

    print(f"[cs-skill-lab] 完成 {len(results)} runs → {out_path}")
    for variant, a in agg.items():
        rec = a["scores"].get("recall")
        if rec:
            print(f"  {variant}: recall = {render_tagged(rec)} (n={a['n']})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
