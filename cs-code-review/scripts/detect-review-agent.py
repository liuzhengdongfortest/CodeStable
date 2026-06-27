#!/usr/bin/env python3
"""Detect optional independent reviewer capabilities for cs-code-review."""

from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import urllib.error
import urllib.request
from pathlib import Path


def find_paseo_cli() -> str | None:
    candidates: list[str] = []
    found = shutil.which("paseo")
    if found:
        candidates.append(found)

    system = platform.system()
    if system == "Darwin":
        candidates.extend(
            [
                "/Applications/Paseo.app/Contents/Resources/bin/paseo",
                str(Path.home() / ".local/bin/paseo"),
            ]
        )
    elif system == "Linux":
        candidates.append(str(Path.home() / ".local/bin/paseo"))
    elif system == "Windows":
        candidates.append(r"C:\Program Files\Paseo\resources\bin\paseo.cmd")

    for candidate in candidates:
        path = Path(candidate).expanduser()
        if path.exists() and os.access(path, os.X_OK):
            return str(path)
    return None


def paseo_health() -> dict[str, object]:
    listen = os.environ.get("PASEO_LISTEN", "127.0.0.1:6767")
    url = listen if listen.startswith(("http://", "https://")) else f"http://{listen}"
    if not url.endswith("/api/health"):
        url = f"{url.rstrip('/')}/api/health"

    try:
        with urllib.request.urlopen(url, timeout=0.8) as response:
            return {
                "ok": 200 <= response.status < 400,
                "url": url,
                "status": response.status,
            }
    except (OSError, urllib.error.URLError) as exc:
        return {"ok": False, "url": url, "error": str(exc)}


def read_paseo_preferences() -> dict[str, object]:
    paseo_home = Path(os.environ.get("PASEO_HOME", str(Path.home() / ".paseo"))).expanduser()
    path = paseo_home / "orchestration-preferences.json"
    result: dict[str, object] = {
        "path": str(path),
        "exists": path.exists(),
        "audit_provider": None,
        "preferences": [],
        "error": None,
    }
    if not path.exists():
        return result

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        result["error"] = str(exc)
        return result

    providers = data.get("providers") if isinstance(data, dict) else None
    if isinstance(providers, dict) and isinstance(providers.get("audit"), str):
        result["audit_provider"] = providers["audit"]

    preferences = data.get("preferences") if isinstance(data, dict) else None
    if isinstance(preferences, list):
        result["preferences"] = [item for item in preferences if isinstance(item, str)]

    return result


def detect_native_agent_tool() -> dict[str, object]:
    """检测当前 runtime 是否暴露了原生 Agent tool（Claude Code / Codex 均支持）。

    判据：存在 CLAUDE_CODE_ENTRYPOINT 或 CODEX_AGENT 环境变量，或可探测到
    claude / codex CLI 且当前进程由其启动（父进程名包含 claude/codex）。
    这里做保守检测：只要 runtime 能识别的标志存在就视为可用。
    """
    indicators = {
        "claude_code": bool(os.environ.get("CLAUDE_CODE_ENTRYPOINT")),
        "codex": bool(os.environ.get("CODEX_AGENT") or os.environ.get("OPENAI_API_KEY")),
        "claude_cli": bool(shutil.which("claude")),
        "codex_cli": bool(shutil.which("codex")),
    }
    available = indicators["claude_code"] or indicators["codex"] or indicators["claude_cli"] or indicators["codex_cli"]
    return {
        "available": available,
        "indicators": indicators,
        "note": "Agent tool 独立上下文 review 通过主 agent 调用 Agent tool 实现，不需要额外 CLI。",
    }


def detect_ocr_cli() -> dict[str, object]:
    """检测 open-code-review (ocr) CLI 是否可用。"""
    path = shutil.which("ocr")
    return {
        "available": bool(path),
        "path": path,
        "note": "ocr review --audience agent --background '{spec}' 做行级扫描。",
    }


def detect_direct_agent_clis() -> list[dict[str, str]]:
    names = ["claude", "gemini", "opencode", "aider"]
    found = []
    for name in names:
        path = shutil.which(name)
        if path:
            found.append({"name": name, "path": path})
    return found


def build_result() -> dict[str, object]:
    paseo_cli = find_paseo_cli()
    health = paseo_health()
    preferences = read_paseo_preferences()
    native_agent = detect_native_agent_tool()
    ocr = detect_ocr_cli()
    direct_agents = detect_direct_agent_clis()

    paseo_available = bool(paseo_cli or health.get("ok"))
    native_available = native_agent["available"]
    ocr_available = ocr["available"]

    # 推导并行审查方案
    parallel_reviewers: list[str] = []
    if paseo_available:
        parallel_reviewers.append("paseo-subagent")
    if native_available:
        parallel_reviewers.append("native-agent-tool")
    if ocr_available:
        parallel_reviewers.append("ocr-cli")

    if parallel_reviewers:
        mode = "independent-review"
        reason = (
            "以下独立 reviewer 可并行启动，各自角度不同互补："
            + "、".join(parallel_reviewers)
            + "。paseo/native-agent 做 spec-aware 整体审查（独立上下文），ocr 做行级代码扫描。"
        )
    else:
        mode = "local-review"
        reason = "未检测到任何独立 reviewer，回退到主 agent 本地 review。"

    return {
        "paseo": {
            "cli": paseo_cli,
            "health": health,
            "preferences": preferences,
        },
        "native_agent_tool": native_agent,
        "ocr_cli": ocr,
        "direct_agent_clis": direct_agents,
        "recommendation": {
            "mode": mode,
            "parallel_reviewers": parallel_reviewers,
            "audit_provider": preferences.get("audit_provider"),
            "reason": reason,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output.")
    args = parser.parse_args()

    result = build_result()
    print(json.dumps(result, ensure_ascii=False, indent=2 if args.pretty else None))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
