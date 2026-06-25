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
    direct_agents = detect_direct_agent_clis()

    if paseo_cli or health.get("ok"):
        mode = "paseo-subagent"
        reason = "Paseo appears available; use an audit subagent only when the runtime exposes Paseo tools or the CLI can be invoked."
    elif direct_agents:
        mode = "local-review-with-agent-cli-available"
        reason = "Direct agent CLIs exist, but cs-code-review should not invoke them automatically."
    else:
        mode = "local-review"
        reason = "No managed independent reviewer was detected."

    return {
        "paseo": {
            "cli": paseo_cli,
            "health": health,
            "preferences": preferences,
        },
        "direct_agent_clis": direct_agents,
        "recommendation": {
            "mode": mode,
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
