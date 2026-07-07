#!/usr/bin/env python3
"""mock-weak harness：离线、确定性、比 mock 弱（签名子集）。

用途：让「多 harness 矩阵」与 optimize 的强弱对比可离线确定性验证——
mock 召回高、mock-weak 召回低，跨 harness 差异真实可测，无需外部 CLI/成本。
"""

from __future__ import annotations

import time
from pathlib import Path

from .base import HarnessResult, register

# 只认最扎眼的几种签名（mock 的子集）→ 召回更低
WEAK_SIGNATURES = ("eval(", "os.system", "password")


class MockWeakHarness:
    name = "mock-weak"

    def invoke(self, prompt: str, model: str, workdir: Path, timeout_s: int) -> HarnessResult:
        start = time.monotonic()
        findings, seen = [], set()
        for raw in prompt.splitlines():
            line = raw.strip()
            if line.startswith("```") or line.startswith("====="):
                continue
            low = line.lower()
            if any(sig in low for sig in WEAK_SIGNATURES) and line not in seen:
                seen.add(line)
                findings.append(f"- [diff] 疑似缺陷：{line[:120]}")
        body = "## Findings\n" + ("\n".join(findings) if findings else "(none)") + "\n"
        return HarnessResult(
            output=body, model=model, harness=self.name,
            wall_ms=int((time.monotonic() - start) * 1000), turns=1,
            usage={"input_tokens": max(1, len(prompt) // 4), "output_tokens": max(1, len(body) // 4),
                   "cost_usd": 0.0, "source": "mock-estimate"},
        )


register(MockWeakHarness())
