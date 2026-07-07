#!/usr/bin/env python3
"""planted-defect 召回 scorer：确定性、measured。

对 fixture.answer 里每条已知缺陷，检查 harness 输出是否「提及」它（token 重叠）。
recall = 命中数 / 总数。这是机械可验的 oracle，故标 [measured]。
"""

from __future__ import annotations

import re
from typing import Any

from _model import MEASURED, tagged
from scorers.base import register

_ASCII = re.compile(r"[0-9a-zA-Z_]{3,}")
_CJK = re.compile(r"[一-鿿]+")
_MATCH_THRESHOLD = 0.5   # 判别 token 有 ≥50% 出现在输出即算命中

# 语义噪声词：出现与否不构成「是否识别到该缺陷」的判别信号
_STOP = {"the", "and", "for", "via", "with", "into", "use", "used", "using", "code", "risk"}


def _cjk_bigrams(text: str) -> list[str]:
    out: list[str] = []
    for run in _CJK.findall(text):
        if len(run) == 1:
            out.append(run)
        else:
            out += [run[i:i + 2] for i in range(len(run) - 1)]
    return out


def _salient(answer: str) -> list[str]:
    """判别性 token：优先代码标识符/英文词（安全缺陷的判别信号多在此）；纯中文退化为 bigram。"""
    ascii_toks = [t for t in _ASCII.findall(answer.lower()) if t not in _STOP]
    if ascii_toks:
        return ascii_toks
    return _cjk_bigrams(answer)


def _recalled(answer: str, output_low: str) -> bool:
    toks = _salient(answer)
    if not toks:
        return False
    hit = sum(1 for t in toks if t in output_low)
    return (hit / len(toks)) >= _MATCH_THRESHOLD


@register("planted_defect", applies_to={"findings-recall"})
def score(fixture, result, config=None, root=None) -> dict[str, Any]:
    answers = list(fixture.answer or [])
    output_low = (result.output or "").lower()
    matched, missed = [], []
    for ans in answers:
        (matched if _recalled(ans, output_low) else missed).append(ans)
    total = len(answers)
    recall = (len(matched) / total) if total else 0.0
    return {
        "scores": {
            "recall": tagged(round(recall, 4), MEASURED, evidence=f"{len(matched)}/{total} planted defects"),
        },
        "evidence": [{"matched": matched, "missed": missed}],
        "status": "passed" if not missed else "failed",
    }
