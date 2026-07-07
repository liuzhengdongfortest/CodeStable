#!/usr/bin/env python3
"""校准 LLM-judge oracle：判它能否在本实验里把分数升为 [measured]。

方法：对每个 sanity fixture 造一对输出——good（正确点出缺陷）/ bad（漏报），
让 judge 分别打分，pairwise 正确 = quality(good) > quality(bad)。准确率 ≥ 阈值且
judge_model 为真实模型（非 mock）→ measured-eligible；否则 soft-only。

写 calibration.json，供 optimize 的 oracle_calibration 分量与结论 tag 使用。
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.dont_write_bytecode = True

_SCRIPTS = Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

import scorers as scorers_pkg  # noqa: E402
from _model import HarnessResult, write_json  # noqa: E402
from config import load_config, repo_root  # noqa: E402
from fixtures import load_fixtures  # noqa: E402

THRESHOLD = 0.8


def _good(fixture) -> str:
    ans = (fixture.answer or ["the defect"])[0]
    return f"## Findings\n### blocking\n- [src:1] {ans}\n"


def _bad(fixture) -> str:
    return "## Findings\n(none)\n"


def _quality(scorer, fixture, output: str, config, root) -> float:
    hr = HarnessResult(output=output, model="judge", harness="mock", wall_ms=1, turns=1)
    return float(scorer(fixture, hr, config, root)["scores"]["judge_quality"]["value"])


def calibrate(exp_dir: Path) -> dict:
    config = load_config(exp_dir)
    root = repo_root()
    scorer = scorers_pkg.get_scorer("llm_judge")
    sanity = load_fixtures(exp_dir, ["sanity"]) or load_fixtures(exp_dir, config.fixture_classes)[:8]

    correct = 0
    for fx in sanity:
        qg = _quality(scorer, fx, _good(fx), config, root)
        qb = _quality(scorer, fx, _bad(fx), config, root)
        if qg > qb:
            correct += 1
    n = len(sanity)
    acc = (correct / n) if n else 0.0

    judge_model = (config.judge_model or "mock")
    is_mock = "mock" in judge_model.lower()
    if is_mock:
        verdict = "soft-only"      # mock 启发式：分数恒 [soft]，不可升 measured
    elif acc >= THRESHOLD:
        verdict = "measured-eligible"
    else:
        verdict = "insufficient"
    return {"judge_model": judge_model, "n": n, "pairwise_accuracy": round(acc, 4),
            "threshold": THRESHOLD, "verdict": verdict}


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="校准 LLM-judge oracle")
    p.add_argument("--experiment", required=True)
    args = p.parse_args(argv)
    exp_dir = Path(args.experiment).resolve()
    result = calibrate(exp_dir)
    write_json(exp_dir / "artifacts" / "analysis" / "judge-calibration.json", result)
    print(f"[cs-skill-lab] judge 校准: acc={result['pairwise_accuracy']} verdict={result['verdict']} "
          f"(judge={result['judge_model']}, n={result['n']})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
