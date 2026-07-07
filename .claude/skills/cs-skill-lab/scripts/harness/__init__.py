"""harness 适配器包：import 即注册。加 harness = 加一个 adapter 模块并在此 import。"""

from __future__ import annotations

import importlib

from .base import HarnessError, available, get_harness  # noqa: F401

# import 副作用 = 注册进 registry（离线 harness 恒加载）
from . import mock  # noqa: F401
from . import mock_weak  # noqa: F401

# 真实 harness 依赖外部 CLI/API；import 失败（缺依赖）不应阻断离线路径
for _mod in ("adapter_claude", "adapter_codex", "adapter_paseo", "adapter_api"):
    try:
        importlib.import_module(f".{_mod}", __name__)
    except Exception:  # noqa: BLE001 - 适配器可选
        pass
