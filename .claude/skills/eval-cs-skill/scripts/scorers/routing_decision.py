#!/usr/bin/env python3
"""routing-decision scorer：决策 fixture 的执行引擎（机械比对、measured）。

模型被 build_routing_prompt 要求只输出 JSON {"result_type", "target", "reason"}。
本 scorer 解析后与 fixture.raw["expect"] 比对：
  - result_type 必须一致（大小写不敏感）
  - target 命中 expect.target 或 expect.target_any 之一（normalize 后相等或包含）
  - expect.must_not_target 若给出则 observed target 不得命中（禁止分支）
纯机械可验 → [measured]。解析失败记 parse-error 并计 0 分。
"""

from __future__ import annotations

import json
import re
from typing import Any

from _model import MEASURED, tagged
from scorers.base import register

_JSON_RE = re.compile(r"\{[^{}]*\}", re.S)


def _norm(s: Any) -> str:
    return re.sub(r"[\s\-_`'\"，。]+", "", str(s or "").lower())


def _extract_json(output: str) -> dict | None:
    try:
        return json.loads(output.strip())
    except Exception:
        pass
    for m in _JSON_RE.finditer(output or ""):
        try:
            obj = json.loads(m.group(0))
            if isinstance(obj, dict) and "result_type" in obj:
                return obj
        except Exception:
            continue
    return None


def _target_hits(observed: str, candidate: str) -> bool:
    o, c = _norm(observed), _norm(candidate)
    if not c:
        return True   # expect 未约束 target → 只看 result_type
    return bool(o) and (o == c or c in o or o in c)


@register("routing_decision", applies_to={"routing-decision"})
def score(fixture, result, config=None, root=None) -> dict[str, Any]:
    expect = dict((fixture.raw or {}).get("expect") or {})
    parsed = _extract_json(result.output or "")

    if parsed is None:
        return {
            "scores": {"routing_ok": tagged(0.0, MEASURED, evidence="parse-error")},
            "evidence": [{"error": "输出不含合法 JSON 决策", "head": (result.output or "")[:200]}],
            "status": "failed",
        }

    obs_type = _norm(parsed.get("result_type"))
    obs_target = str(parsed.get("target") or parsed.get("stage") or "")
    type_candidates = expect.get("result_type_any") or [expect.get("result_type")]
    type_ok = obs_type in {_norm(t) for t in type_candidates}

    candidates = expect.get("target_any") or ([expect["target"]] if expect.get("target") else [])
    target_ok = (not candidates) or any(_target_hits(obs_target, c) for c in candidates)

    forbidden = expect.get("must_not_target")
    forbidden_hit = bool(forbidden) and _norm(obs_target) != "" and _target_hits(obs_target, forbidden) \
        and not any(_target_hits(obs_target, c) for c in candidates)

    ok = type_ok and target_ok and not forbidden_hit
    return {
        "scores": {"routing_ok": tagged(1.0 if ok else 0.0, MEASURED,
                                        evidence=f"type={'✓' if type_ok else '✗'} target={'✓' if target_ok else '✗'}"
                                                 f"{' forbidden-hit' if forbidden_hit else ''}")},
        "evidence": [{"observed": parsed, "expected": expect}],
        "status": "passed" if ok else "failed",
    }
