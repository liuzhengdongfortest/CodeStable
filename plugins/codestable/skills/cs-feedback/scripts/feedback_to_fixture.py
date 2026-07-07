#!/usr/bin/env python3
"""把 cs-feedback 采集到的失败案例转成 cs-skill 的 regression fixture + hypothesis 骨架。

闭环起点：生产失败 → 评测 fixture。cs-feedback 自有脚本（不跨 skill 依赖 cs-skill 内部）。
输入：--failure 文本 或 --evidence public-issue-context.json（collect_feedback_context 产出）。
输出：experiments/<experiment>/fixtures/regression/reg-<slug>.json + 打印建议 hypothesis 行。
生成的是**骨架**：diff/answer 需人工补全为可复现样本后再冻结。
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.dont_write_bytecode = True


def _slug(text: str, n: int = 6) -> str:
    words = re.findall(r"[0-9a-zA-Z]+", text.lower())
    return "-".join(words[:n]) or "case"


def _fixture(kind: str, summary: str, spec: str, diff: str) -> dict:
    return {
        "id": f"reg-{_slug(summary)}",
        "answerType": "findings-recall",
        "answer": [summary],
        "task": {"kind": kind, "spec": spec, "diff": diff or "TODO: 补全可复现代码"},
        "_source": "cs-feedback",
        "_status": "skeleton",   # 需人工补全 diff/answer 后方可用于正式实验
    }


def from_evidence(path: Path) -> list[dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    events = data.get("events") or data.get("candidates") or []
    out = []
    for ev in events:
        summary = ev.get("actual_behavior") or ev.get("sanitized_excerpt") or ev.get("failure_type") or "unknown failure"
        spec = ev.get("expected_behavior") or ""
        out.append(_fixture(ev.get("kind", "review"), summary[:120], spec[:200], ""))
    return out


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="feedback 失败 → regression fixture 骨架")
    p.add_argument("--experiment", required=True, help="目标实验目录，如 experiments/cs-code-review-001")
    p.add_argument("--failure", help="单条失败描述")
    p.add_argument("--evidence", help="public-issue-context.json 路径")
    p.add_argument("--kind", default="review", choices=["review", "fix", "audit"])
    p.add_argument("--spec", default="")
    p.add_argument("--diff", default="")
    args = p.parse_args(argv)

    exp = Path(args.experiment).resolve()
    reg_dir = exp / "fixtures" / "regression"
    reg_dir.mkdir(parents=True, exist_ok=True)

    fixtures: list[dict] = []
    if args.evidence:
        fixtures += from_evidence(Path(args.evidence))
    if args.failure:
        fixtures.append(_fixture(args.kind, args.failure[:120], args.spec, args.diff))
    if not fixtures:
        print("需 --failure 或 --evidence", file=sys.stderr)
        return 2

    for fx in fixtures:
        out = reg_dir / f"{fx['id']}.json"
        out.write_text(json.dumps(fx, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"[cs-feedback] 写 regression fixture 骨架 → {out}")
        print(f"  建议 hypothesis: H-regression-{fx['id']}: 该 skill 应识别「{fx['answer'][0]}」（recall=1.0）")
    print("提示：补全 diff/answer 为可复现样本后，把 hypotheses.md 冻结并 git commit 再评测。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
