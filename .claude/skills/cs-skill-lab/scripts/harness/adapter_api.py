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


def _post(url: str, headers: dict, payload: dict, timeout_s: int) -> dict:
    req = urllib.request.Request(url, data=json.dumps(payload).encode(), headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout_s) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as exc:
        raise HarnessError(f"API HTTP {exc.code}: {exc.read()[:300]!r}") from exc
    except urllib.error.URLError as exc:
        raise HarnessError(f"API 网络错误: {exc}") from exc


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
            {"model": model, "max_tokens": 2048, "messages": [{"role": "user", "content": prompt}]},
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
