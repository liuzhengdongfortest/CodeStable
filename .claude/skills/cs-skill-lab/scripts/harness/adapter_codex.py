#!/usr/bin/env python3
"""Codex CLI headless 适配器：`codex exec`。

隔离：独立 workdir + env 白名单。Codex 一般不回传 token usage → 指标走 [soft] 估算。
CLI 缺失/超时/非零退出抛 HarnessError。真实运行前请对齐本机 codex 版本的 exec 参数。
"""

from __future__ import annotations

import shutil
import subprocess
import time
from pathlib import Path

from .base import HarnessError, HarnessResult, register, whitelisted_env


class CodexHarness:
    name = "codex-cli"

    def invoke(self, prompt: str, model: str, workdir: Path, timeout_s: int) -> HarnessResult:
        binary = shutil.which("codex")
        if not binary:
            raise HarnessError("找不到 `codex` CLI，无法用 codex-cli harness")
        workdir.mkdir(parents=True, exist_ok=True)
        # codex exec：非交互执行；--skip-git-repo-check 便于在 tmp workdir 跑
        cmd = [binary, "exec", "--skip-git-repo-check"]
        if model:
            cmd += ["--model", model]
        cmd.append(prompt)
        start = time.monotonic()
        try:
            completed = subprocess.run(
                cmd, cwd=workdir, env=whitelisted_env(), text=True,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout_s, check=False,
            )
        except subprocess.TimeoutExpired as exc:
            raise HarnessError(f"codex-cli 超时 {timeout_s}s") from exc
        wall_ms = int((time.monotonic() - start) * 1000)
        if completed.returncode != 0:
            raise HarnessError(f"codex 退出码 {completed.returncode}: {completed.stderr[-500:]}")
        return HarnessResult(output=completed.stdout, model=model, harness=self.name,
                             wall_ms=wall_ms, turns=None, usage=None)


register(CodexHarness())
