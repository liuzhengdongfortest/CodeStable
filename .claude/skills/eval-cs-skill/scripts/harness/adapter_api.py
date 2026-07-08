#!/usr/bin/env python3
"""直连 API 适配器（纯模型档位对比，无 harness/agent 开销）。

按 model 名分派：claude*/anthropic → Anthropic Messages API；gpt*/o* → OpenAI Chat。
用 urllib（无 SDK 依赖）。回收真实 usage（input/output tokens）→ 指标可标 [measured]。
鉴权走 env：ANTHROPIC_API_KEY / OPENAI_API_KEY。缺 key 抛 HarnessError。
"""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path

from .base import HarnessError, HarnessResult, register


_RETRY_CODES = {429, 500, 502, 503, 504}  # 暂时性：限流/网关超时/上游不可用
# max_tokens 是上限非固定成本（按实际 output 计费）；生成型/e2e 产 roadmap/diff 时
# 2048 会截断产物、污染覆盖率评测。默认给足 headroom，可用 CS_EVAL_MAX_TOKENS 覆盖。
_MAX_TOKENS = int(os.environ.get("CS_EVAL_MAX_TOKENS", "8192"))


def _post(url: str, headers: dict, payload: dict, timeout_s: int, retries: int = 3) -> dict:
    """带退避重试：消化间歇 504/超时（慢模型如 gpt-5.x 常触发 gateway 504）。"""
    last: HarnessError | None = None
    for attempt in range(retries):
        req = urllib.request.Request(url, data=json.dumps(payload).encode(), headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=timeout_s) as resp:
                return json.loads(resp.read().decode())
        except urllib.error.HTTPError as exc:
            last = HarnessError(f"API HTTP {exc.code}: {exc.read()[:300]!r}")
            if exc.code not in _RETRY_CODES:  # 非暂时性（4xx 鉴权/请求错）不重试
                raise last from exc
        except urllib.error.URLError as exc:
            last = HarnessError(f"API 网络错误: {exc}")
        if attempt < retries - 1:
            time.sleep(2 ** attempt)  # 退避 1/2/4s
    raise last  # 重试耗尽


class ApiHarness:
    name = "api"

    def invoke(self, prompt: str, model: str, workdir: Path, timeout_s: int) -> HarnessResult:
        low = (model or "").lower()
        start = time.monotonic()
        if low.startswith(("gpt", "o1", "o3", "o4")) or "openai" in low:
            output, usage = self._openai(prompt, model, timeout_s)
        else:
            output, usage = self._anthropic(prompt, model, timeout_s)
        return HarnessResult(output=output, model=model, harness=self.name,
                             wall_ms=int((time.monotonic() - start) * 1000), turns=1, usage=usage)

    def _anthropic(self, prompt: str, model: str, timeout_s: int):
        auth = os.environ.get("ANTHROPIC_AUTH_TOKEN")
        key = os.environ.get("ANTHROPIC_API_KEY")
        if not (auth or key):
            raise HarnessError("缺 ANTHROPIC_AUTH_TOKEN / ANTHROPIC_API_KEY")
        base = os.environ.get("ANTHROPIC_BASE_URL", "https://api.anthropic.com").rstrip("/")
        headers = {"anthropic-version": "2023-06-01", "content-type": "application/json"}
        if auth:                                      # 网关/OAuth：Bearer
            headers["authorization"] = f"Bearer {auth}"
        else:                                         # 官方 API key
            headers["x-api-key"] = key
        data = _post(
            f"{base}/v1/messages",
            headers,
            {"model": model, "max_tokens": _MAX_TOKENS, "messages": [{"role": "user", "content": prompt}]},
            timeout_s,
        )
        text = "".join(b.get("text", "") for b in data.get("content", []) if b.get("type") == "text")
        u = data.get("usage", {})
        usage = {"input_tokens": u.get("input_tokens"), "output_tokens": u.get("output_tokens"),
                 "cost_usd": None, "source": "claude-json"}  # 复用 claude-json：runner 视为 measured
        return text, usage

    def _openai(self, prompt: str, model: str, timeout_s: int):
        key = os.environ.get("OPENAI_API_KEY")
        if not key:
            raise HarnessError("缺 OPENAI_API_KEY")
        base = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com").rstrip("/")
        data = _post(
            f"{base}/v1/chat/completions",
            {"authorization": f"Bearer {key}", "content-type": "application/json"},
            {"model": model, "messages": [{"role": "user", "content": prompt}]},
            timeout_s,
        )
        text = data["choices"][0]["message"]["content"]
        u = data.get("usage", {})
        usage = {"input_tokens": u.get("prompt_tokens"), "output_tokens": u.get("completion_tokens"),
                 "cost_usd": None, "source": "claude-json"}
        return text, usage


register(ApiHarness())
