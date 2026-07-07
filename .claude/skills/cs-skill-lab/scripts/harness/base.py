#!/usr/bin/env python3
"""Harness 适配器基类与注册表。

自举底座：加一个 harness = 加一个 adapter 模块并 register，不改 runner/核心。
契约：invoke(prompt, model, workdir, timeout_s) -> HarnessResult；
      每次调用用独立 workdir/env 白名单隔离宿主；失败抛 HarnessError。
"""

from __future__ import annotations

import sys

sys.dont_write_bytecode = True  # 不污染 plugin 包

from pathlib import Path
from typing import Callable, Protocol

# scripts/ 目录在 sys.path[0]（runner.py 所在），保证 `from _model import ...` 可用
_SCRIPTS = Path(__file__).resolve().parent.parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from _model import HarnessResult  # noqa: E402


class HarnessError(RuntimeError):
    """harness 调用失败（CLI 缺失、超时、非零退出、无法解析输出等）。"""


class Harness(Protocol):
    name: str

    def invoke(self, prompt: str, model: str, workdir: Path, timeout_s: int) -> HarnessResult: ...


_REGISTRY: dict[str, Harness] = {}


def register(harness: Harness) -> Harness:
    _REGISTRY[harness.name] = harness
    return harness


def get_harness(name: str) -> Harness:
    if name not in _REGISTRY:
        raise HarnessError(
            f"未知 harness {name!r}；已注册 {sorted(_REGISTRY)}。"
            f" 新增请在 scripts/harness/ 下建 adapter 并 register。"
        )
    return _REGISTRY[name]


def available() -> list[str]:
    return sorted(_REGISTRY)


ENV_WHITELIST = (
    "PATH", "HOME", "LANG", "LC_ALL", "TERM",
    "ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN", "ANTHROPIC_BASE_URL", "ANTHROPIC_MODEL",
    "OPENAI_API_KEY", "OPENAI_BASE_URL",
    "CLAUDE_CODE_OAUTH_TOKEN", "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC",
    "CLAUDE_CODE_ATTRIBUTION_HEADER", "CODEX_HOME",
    "HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy", "ALL_PROXY", "NO_PROXY",
)


def whitelisted_env(extra: dict[str, str] | None = None) -> dict[str, str]:
    import os
    env = {k: os.environ[k] for k in ENV_WHITELIST if k in os.environ}
    if extra:
        env.update(extra)
    return env
