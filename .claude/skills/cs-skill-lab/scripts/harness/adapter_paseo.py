#!/usr/bin/env python3
"""Paseo 托管 agent 适配器。

Paseo 主要通过 MCP 工具（create_agent/send_agent_prompt）驱动，不是纯 CLI。
本适配器提供两条路径：
- 若本机有 `paseo` CLI：shell 调用（best-effort，需对齐真实 CLI 契约）。
- 否则抛 HarnessError，指向 agent 编排路径：由 cs-skill-lab 的 autonomy 协议（references/autonomy/protocol.md）
  用 Paseo MCP 逐 cell 起 agent，属「路径 B 宿主」，不在纯 Python runner 内联执行。
"""

from __future__ import annotations

import shutil
import subprocess
import time
from pathlib import Path

from .base import HarnessError, HarnessResult, register, whitelisted_env


class PaseoHarness:
    name = "paseo"

    def invoke(self, prompt: str, model: str, workdir: Path, timeout_s: int) -> HarnessResult:
        binary = shutil.which("paseo")
        if not binary:
            raise HarnessError(
                "Paseo harness 需 `paseo` CLI 或 agent 编排路径。"
                "纯 Python runner 不内联 Paseo；见 references/autonomy/protocol.md 路径 B。"
            )
        workdir.mkdir(parents=True, exist_ok=True)
        cmd = [binary, "agent", "run", "--prompt", prompt]
        if model:
            cmd += ["--model", model]
        start = time.monotonic()
        try:
            completed = subprocess.run(
                cmd, cwd=workdir, env=whitelisted_env(), text=True,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout_s, check=False,
            )
        except subprocess.TimeoutExpired as exc:
            raise HarnessError(f"paseo 超时 {timeout_s}s") from exc
        if completed.returncode != 0:
            raise HarnessError(f"paseo 退出码 {completed.returncode}: {completed.stderr[-500:]}")
        return HarnessResult(output=completed.stdout, model=model, harness=self.name,
                             wall_ms=int((time.monotonic() - start) * 1000), turns=None, usage=None)


register(PaseoHarness())
