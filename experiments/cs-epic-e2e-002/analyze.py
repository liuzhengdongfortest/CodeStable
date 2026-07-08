#!/usr/bin/env python3
"""cs-epic 路B 分析：H5（补漏有效）/ H5b（结构化 review 增量）/ revise 损坏率。

读 full-k3.json（run_review_loop --full-out），按 treatment/control 聚合：
- v1_recall → v2_recall（补漏是否让覆盖率上升）
- recovered = v1_missed ∩ v2_matched（漏项精准补回数）
- lost = v2 漏了 v1 已覆盖的项（revise 损坏 = 结构化 review 的隐藏价值面）
"""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path
from statistics import mean


def load(path: Path) -> list[dict]:
    return json.loads(path.read_text(encoding="utf-8"))


def analyze(rows: list[dict]) -> None:
    variants = ("treatment", "control")
    agg = {v: {"v1": [], "v2": [], "recov": 0, "miss": 0, "lost_rows": 0, "lost_items": 0} for v in variants}
    per_fix = defaultdict(lambda: {v: {"v1": [], "v2": []} for v in variants})

    for r in rows:
        fid = r["fixture"]
        for v in variants:
            a, d = agg[v], r[v]
            a["v1"].append(r["v1_recall"])
            a["v2"].append(d["v2_recall"])
            a["recov"] += len(d["recovered"])
            a["miss"] += len(r["v1_missed"])
            lost = [m for m in d["still_missed"] if m not in r["v1_missed"]]
            a["lost_items"] += len(lost)
            if lost:
                a["lost_rows"] += 1
            per_fix[fid][v]["v1"].append(r["v1_recall"])
            per_fix[fid][v]["v2"].append(d["v2_recall"])

    n = len(rows)
    print(f"== 路B 聚合（n={n} 条，每条含同一 v1 分别喂 treatment/control review）==\n")
    print(f"{'变体':10s} | {'v1均':>5s} {'v2均':>5s} {'Δ':>6s} | {'补漏率':>8s} | {'损坏(行/项)':>12s}")
    for v in variants:
        a = agg[v]
        v1m, v2m = mean(a["v1"]), mean(a["v2"])
        rate = a["recov"] / a["miss"] if a["miss"] else 0.0
        print(f"{v:10s} | {v1m:5.2f} {v2m:5.2f} {v2m-v1m:+6.2f} | "
              f"{a['recov']:>2d}/{a['miss']:<2d}={rate:.2f} | {a['lost_rows']:>2d}行/{a['lost_items']}项")

    print("\n== 逐 fixture（v1→v2）==")
    for fid in sorted(per_fix):
        parts = []
        for v in variants:
            p = per_fix[fid][v]
            parts.append(f"{v[:4]}: {mean(p['v1']):.2f}→{mean(p['v2']):.2f}")
        print(f"  {fid}: " + "  ".join(parts))

    t, c = agg["treatment"], agg["control"]
    tv2, cv2 = mean(t["v2"]), mean(c["v2"])
    v1m = mean(t["v1"])
    print("\n== 判定 ==")
    print(f"  H5  (review 补漏有效, v2>v1):     treatment {mean(t['v2'])-v1m:+.2f} / control {cv2-mean(c['v1']):+.2f}")
    print(f"  H5b (结构化 review 增量, T>C):    Δ(T−C) = {tv2-cv2:+.2f}")
    print(f"  隐藏面 (revise 损坏率):           treatment {t['lost_rows']}/{n} vs control {c['lost_rows']}/{n}")
    print(f"\n  [underpowered] n={n}, haiku 单模型；sonnet 网关 504 未测。")


if __name__ == "__main__":
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent / "artifacts/full-k3.json"
    analyze(load(path))
