#!/usr/bin/env python3
"""回归电池：对 release 候选跑 N 次，用 CI 判是否相对 baseline 退步。

判据（严格）：improved = cand_lo > base_hi；regressed = cand_hi < base_lo；否则 inconclusive。
仅 regressed 阻断（exit 3）。baseline 存 artifacts/analysis/baseline.json。
"""

from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path
from statistics import mean, stdev

sys.dont_write_bytecode = True

_SCRIPTS = Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

import runner  # noqa: E402
from _model import read_json, write_json  # noqa: E402
from config import load_config  # noqa: E402
from fixtures import load_fixtures  # noqa: E402


def ci95(samples: list[float]) -> tuple[float, float, float]:
    """(mean, lo, hi)，正态近似 95% CI。n<2 时零宽。"""
    if not samples:
        return 0.0, 0.0, 0.0
    m = mean(samples)
    if len(samples) < 2:
        return m, m, m
    half = 1.96 * stdev(samples) / math.sqrt(len(samples))
    return m, m - half, m + half


def verdict(base: list[float], cand: list[float]) -> str:
    _, blo, bhi = ci95(base)
    _, clo, chi = ci95(cand)
    if clo > bhi:
        return "improved"
    if chi < blo:
        return "regressed"
    return "inconclusive"


def samples_for(exp_dir: Path, variant: str, n: int) -> list[float]:
    """跑 variant，k=n，每个 k_index 的跨 fixture 平均 recall 作一个样本。"""
    config = load_config(exp_dir)
    fixtures = load_fixtures(exp_dir, config.fixture_classes)
    cells = [(variant, h, m) for h in config.harnesses
             for m in (config.model_list or ["default"])]
    results = runner.run(config, fixtures, cells, ["planted_defect"], n)
    by_k: dict[int, list[float]] = {}
    for r in results:
        rec = r.scores.get("recall")
        if rec is not None:
            by_k.setdefault(r.k_index, []).append(float(rec["value"]))
    return [mean(v) for v in by_k.values() if v]


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="cs-skill-lab 回归电池")
    p.add_argument("--experiment", required=True)
    p.add_argument("--n", type=int, default=5)
    p.add_argument("--candidate", default="baseline", help="候选 variant 名")
    p.add_argument("--record-baseline", action="store_true", help="把当前 candidate 存为 baseline")
    args = p.parse_args(argv)

    exp_dir = Path(args.experiment).resolve()
    base_path = exp_dir / "artifacts" / "analysis" / "baseline.json"

    cand = samples_for(exp_dir, args.candidate, args.n)
    if args.record_baseline or not base_path.is_file():
        write_json(base_path, {"variant": args.candidate, "n": args.n, "samples": cand})
        print(f"[cs-skill-lab] 已记录 baseline（{args.candidate}, n={args.n}, mean={mean(cand) if cand else 0:.4f}）")
        return 0

    base = read_json(base_path).get("samples", [])
    v = verdict(base, cand)
    bm = mean(base) if base else 0.0
    cm = mean(cand) if cand else 0.0
    print(f"[cs-skill-lab] 回归判定: {v}（baseline mean={bm:.4f} → candidate mean={cm:.4f}, n={args.n}）")
    return 3 if v == "regressed" else 0


if __name__ == "__main__":
    raise SystemExit(main())
