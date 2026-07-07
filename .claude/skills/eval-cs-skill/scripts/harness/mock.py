#!/usr/bin/env python3
"""mock harness：离线、确定性、零成本。

只看 prompt（不看 fixture.answer，不作弊）：扫描 prompt 里 diff 区的每一行，
命中缺陷签名的行就作为一条 finding 输出——一个「关键词 reviewer」。
用于 skeleton 主链验证与单测，让 runner/scorer/metrics 全链路可离线跑通且可复现。
"""

from __future__ import annotations

import time
from pathlib import Path

from .base import HarnessResult, register

# 常见缺陷签名（真实但粗糙；planted-defect fixtures 会在缺陷行放这些 token）
SIGNATURES = (
    "eval(", "exec(", "os.system", "subprocess", "shell=true", "pickle.loads",
    "md5", "verify=false", "password", "secret", "token", "api_key",
    "todo", "fixme", "== none", "!= none", "innerhtml", "format(",
    "select ", "concat(", "yaml.load", "assert ", "except:", "sleep(",
)


class MockHarness:
    name = "mock"

    def invoke(self, prompt: str, model: str, workdir: Path, timeout_s: int) -> HarnessResult:
        start = time.monotonic()
        findings: list[str] = []
        seen: set[str] = set()
        # mock 仅用于离线打通管线：扫描所有行的缺陷签名（不作真实 review，误报不影响召回验证）
        for raw in prompt.splitlines():
            line = raw.strip()
            if line.startswith("```") or line.startswith("====="):
                continue
            low = line.lower()
            if any(sig in low for sig in SIGNATURES):
                if line not in seen:
                    seen.add(line)
                    findings.append(f"- [diff] 疑似缺陷：{line[:120]}")
        if not findings:
            body = "## Findings\n(none)\n"
        else:
            body = "## Findings\n### blocking\n" + "\n".join(findings) + "\n"
        wall_ms = int((time.monotonic() - start) * 1000)
        # mock 提供 usage 让指标链路可测（标为估算，真实 harness 会覆盖）
        usage = {
            "input_tokens": max(1, len(prompt) // 4),
            "output_tokens": max(1, len(body) // 4),
            "cost_usd": 0.0,
            "source": "mock-estimate",
        }
        return HarnessResult(
            output=body,
            model=model,
            harness=self.name,
            wall_ms=wall_ms,
            turns=1,
            usage=usage,
        )


register(MockHarness())
