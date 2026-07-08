#!/usr/bin/env python3
"""cs-epic 路B：roadmap-review 补漏环节 e2e（H5）。

三阶段编排 planning→review→revise：
  1. planning：cs-epic 全文 + 需求 → roadmap_v1
  2. review：treatment(cs-epic review protocol 结构化审查) / control(泛泛自查) → findings
  3. revise：v1 + findings → roadmap_v2（两组同一 revise，只 review 不同 → 干净隔离）
对 v1/v2 各评 recall_judge（opus 语义）。recovered = v1_missed ∩ v2_matched。

全 haiku（避 sonnet 网关 504）。多阶段串联 + 网关间歇 504 → 每阶段做阶段级重试，
review 输出强制简洁（只点漏项，减生成时间即降 504）；单 fixture 任一阶段最终失败则整条丢弃。
"""
from __future__ import annotations

import argparse
import json
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / ".claude/skills/eval-cs-skill/scripts"))
sys.dont_write_bytecode = True

import buildprompt as bp          # noqa: E402
import config as cf               # noqa: E402
import harness as harness_pkg     # noqa: E402
import scorers as scorers_pkg     # noqa: E402
from _model import Fixture, HarnessResult  # noqa: E402

MODEL = "claude-haiku-4-5"
FIX_DIR = ROOT / "experiments/cs-epic-e2e-001/fixtures/planning"

# treatment = cs-epic review protocol 独立 reviewer 的审查维度（protocol.md 58-73 行精神，
# 材料内联）；control = 泛泛"再想一次"。两者都不点名具体漏项（不看 answer）→ 忠实隔离。
_REVIEW = {
    "treatment": (
        "你是 CodeStable roadmap 的独立规划审查 agent，只做只读审查、不改拆解。\n"
        "按 epic review 的审查维度检查下面这份大需求拆解：目标完成信号是否可验收、范围与\"明确不做\"、"
        "模块拆分是否有遗漏或万能模块、接口契约是否可执行、子功能是否原子可独立验证、依赖关系、最小闭环、"
        "验证策略、风险与回滚，以及**是否遗漏了应有的子功能**——特别留意跨切面、非功能性、边界与失败路径"
        "这类初次拆解容易忽略的部分。"
    ),
    "control": (
        "下面是一份需求拆解。请再检查一遍，指出任何可以补充或遗漏的子功能。"
    ),
}
# 强制简洁：findings 只需点出漏项（减 haiku 生成时间 = 降网关 504），不写长篇报告
_BREVITY = ("\n\n输出要求：只用短 bullet 列出你认为**遗漏或应补充的子功能**（每条一句话，"
            "最多再加 3 条关键问题）；不要复述已有内容、不要写长篇报告或证据段落。")


def _review_prompt(variant: str, spec: str, context: str, v1: str) -> str:
    return f"{_REVIEW[variant]}{_BREVITY}\n\n## 需求\n{spec}\n\n## 现状\n{context}\n\n## 待审拆解\n{v1}"


def _revise_prompt(spec: str, context: str, v1: str, findings: str) -> str:
    return (
        "下面是一份需求拆解和对它的审查意见。请根据审查意见修订这份拆解，补全被指出遗漏的子功能，"
        "输出修订后的**完整**子功能拆解列表（保留原有的，加上补充的）。\n\n"
        f"## 需求\n{spec}\n\n## 现状\n{context}\n\n## 原拆解\n{v1}\n\n## 审查意见\n{findings}\n\n## 输出修订后的完整拆解\n"
    )


def _hr(text: str) -> HarnessResult:
    return HarnessResult(output=text, model=MODEL, harness="api", wall_ms=0)


def _invoke_retry(h, prompt: str, tmpp: Path, label: str, tries: int = 4) -> str:
    """阶段级重试：消化网关间歇 504（adapter 内建 3 次退避不够时再兜底）。"""
    last: Exception | None = None
    for i in range(tries):
        try:
            return h.invoke(prompt, MODEL, tmpp, 600).output
        except Exception as exc:  # noqa: BLE001
            last = exc
            if i < tries - 1:
                time.sleep(6 * (i + 1))  # 6/12/18s 让网关恢复
    raise RuntimeError(f"{label} 阶段 {tries} 次仍失败: {last}")


def _score(rj, fx: Fixture, text: str, cfg) -> tuple[float, list, list]:
    r = rj(fx, _hr(text), cfg, None)
    ev = next((e for e in r.get("evidence", []) if e.get("source")), {})
    return r["scores"]["recall_judge"]["value"], ev.get("matched", []), ev.get("missed", [])


def run_one(fx: Fixture, cs_text: str, cfg) -> dict | None:
    h = harness_pkg.get_harness("api")
    rj = scorers_pkg.get_scorer("recall_judge")
    task = fx.raw["task"]
    spec, context = task["spec"], task.get("context", "")
    try:
        with tempfile.TemporaryDirectory(prefix="cs-epic-b-") as tmp:
            tmpp = Path(tmp)
            v1 = _invoke_retry(h, bp.build_prompt(fx, cs_text, True), tmpp, "planning")
            v1r, _v1m, v1miss = _score(rj, fx, v1, cfg)
            out = {"fixture": fx.id, "v1_recall": v1r, "v1_missed": v1miss, "v1": v1}
            for variant in ("treatment", "control"):
                findings = _invoke_retry(h, _review_prompt(variant, spec, context, v1), tmpp, f"review-{variant}")
                v2 = _invoke_retry(h, _revise_prompt(spec, context, v1, findings), tmpp, f"revise-{variant}")
                v2r, v2m, v2miss = _score(rj, fx, v2, cfg)
                out[variant] = {
                    "v2_recall": v2r,
                    "recovered": [x for x in v1miss if x in v2m],
                    "still_missed": v2miss,
                    "findings": findings,
                    "v2": v2,
                }
            return out
    except Exception as exc:  # noqa: BLE001 - 单 fixture 失败不崩整批
        print(f"  [丢弃 {fx.id}] {exc}")
        return None


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fixture", action="append", help="e01/e02/e03；默认全部")
    ap.add_argument("--k", type=int, default=3)
    ap.add_argument("--out", help="精简结果 JSON（不含全文）")
    ap.add_argument("--full-out", help="含 v1/v2/findings 全文（gitignore）")
    ap.add_argument("--smoke", action="store_true", help="逐条打印机制证据")
    a = ap.parse_args()

    exp_dir = Path(__file__).resolve().parent
    cfg = cf.load_config(exp_dir)
    cs_text = cf.resolve_variant_text(cfg, "baseline", ROOT, exp_dir)
    fids = a.fixture or ["e01", "e02", "e03"]

    rows, fails = [], 0
    for fid in fids:
        fx = Fixture.from_dict(json.loads((FIX_DIR / f"{fid}.json").read_text(encoding="utf-8")))
        for ki in range(a.k):
            r = run_one(fx, cs_text, cfg)
            if r is None:
                fails += 1
                continue
            r["k"] = ki
            rows.append(r)
            if a.smoke:
                print(f"\n{'='*64}\n[{fid} k{ki}] v1_recall={r['v1_recall']:.2f} 漏 {len(r['v1_missed'])} 项")
                print("  v1 漏项:", r["v1_missed"])
                for v in ("treatment", "control"):
                    d = r[v]
                    print(f"  [{v:9s}] v2_recall={d['v2_recall']:.2f} "
                          f"recovered={len(d['recovered'])}/{len(r['v1_missed'])} {d['recovered']}")
                print("  treatment findings:", r["treatment"]["findings"][:300].replace("\n", " "))

    print(f"\n完成 {len(rows)} 条，丢弃 {fails} 条")
    if a.full_out:
        Path(a.full_out).write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
    if a.out:
        slim = [{k: v for k, v in r.items() if k != "v1"} for r in rows]
        for r in slim:
            for v in ("treatment", "control"):
                r[v] = {k: val for k, val in r[v].items() if k not in ("findings", "v2")}
        Path(a.out).write_text(json.dumps(slim, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
