#!/usr/bin/env python3
"""Claude Code headless 适配器：`claude -p <prompt> --output-format json`。

隔离：在独立 workdir 跑、env 白名单。尽量从 --output-format json 回收 usage（升为 measured）。
CLI 缺失或超时抛 HarnessError。真实运行才用，离线测试用 mock。
"""

from __future__ import annotations

import json
import shutil
import subprocess
import time
from pathlib import Path

from .base import HarnessError, HarnessResult, register, whitelisted_env


class ClaudeHarness:
    name = "claude-headless"

    def invoke(self, prompt: str, model: str, workdir: Path, timeout_s: int) -> HarnessResult:
        binary = shutil.which("claude")
        if not binary:
            raise HarnessError("找不到 `claude` CLI，无法用 claude-headless harness")
        workdir.mkdir(parents=True, exist_ok=True)
        cmd = [binary, "-p", prompt, "--output-format", "json"]
        if model:
            cmd += ["--model", model]
        start = time.monotonic()
        try:
            completed = subprocess.run(
                cmd,
                cwd=workdir,
                env=whitelisted_env(),
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=timeout_s,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            raise HarnessError(f"claude-headless 超时 {timeout_s}s") from exc
        wall_ms = int((time.monotonic() - start) * 1000)
        if completed.returncode != 0:
            raise HarnessError(f"claude 退出码 {completed.returncode}: {completed.stderr[-500:]}")

        output, turns, usage = _parse(completed.stdout)
        return HarnessResult(
            output=output,
            model=model,
            harness=self.name,
            wall_ms=wall_ms,
            turns=turns,
            usage=usage,
        )


def _parse(stdout: str) -> tuple[str, int | None, dict | None]:
    """解析 claude -p --output-format json 输出：{result, usage, num_turns, ...}。"""
    text = stdout.strip()
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return text, None, None
    output = data.get("result") or data.get("text") or json.dumps(data, ensure_ascii=False)
    turns = data.get("num_turns")
    usage = None
    raw_usage = data.get("usage") or {}
    if raw_usage:
        usage = {
            "input_tokens": raw_usage.get("input_tokens"),
            "output_tokens": raw_usage.get("output_tokens"),
            "cost_usd": data.get("total_cost_usd") or data.get("cost_usd"),
            "source": "claude-json",
        }
    return output, turns, usage


register(ClaudeHarness())
