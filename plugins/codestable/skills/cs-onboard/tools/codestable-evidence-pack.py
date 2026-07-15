#!/usr/bin/env python3
"""Generate a minimal feature evidence pack markdown."""

from __future__ import annotations

import json
import os
import shutil
import sys
from pathlib import Path

if os.environ.get("PYTHONDONTWRITEBYTECODE") != "1":
    os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
    os.execvpe(sys.executable, [sys.executable, *sys.argv], os.environ)
sys.dont_write_bytecode = True

from codestable_gate_common import (
    file_sha256,
    gate_result,
    main_exit,
    parse_args,
    read_text,
    repo_relative_path,
    repo_root,
)


def load_json(path: str | None, label: str) -> tuple[dict, list[str]]:
    if not path:
        return {}, []
    target = Path(path)
    if not target.is_file():
        return {}, [f"{label} not found: {target}"]
    try:
        data = json.loads(target.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        return {}, [f"invalid JSON artifact: {target} ({type(error).__name__})"]
    if not isinstance(data, dict):
        return {}, [f"{label} JSON is not a mapping: {target}"]
    return data, []


def residual_risks(dod: dict, gates: dict) -> list[str]:
    risks: list[str] = []
    risks.extend(str(warning) for warning in dod.get("warnings", []) or [])
    risks.extend(str(warning) for warning in gates.get("warnings", []) or [])
    for gate in gates.get("gates", []) or []:
        if isinstance(gate, dict):
            risks.extend(f"{gate.get('gate_id')}: {warning}" for warning in gate.get("warnings", []) or [])
    return risks or ["none"]


def provider_status(name: str, mode: str) -> dict:
    if mode != "auto":
        return {"status": "skipped", "reason": f"{name} collection disabled", "warnings": []}
    if name == "archguard":
        binary = shutil.which("archguard")
        if binary:
            return {
                "status": "available",
                "signal_type": "availability",
                "summary": f"archguard binary found at {binary}; risk summary not collected in this minimal mode",
                "warnings": ["archguard available but risk summary not collected"],
            }
        return {"status": "unavailable", "reason": "archguard binary not found on PATH", "warnings": []}
    digest = Path(".codestable/meta-cc-summary.md")
    if digest.exists():
        return {"status": "available", "summary": str(digest), "warnings": []}
    return {"status": "unavailable", "reason": "meta-cc summary not found; realtime session collection is out of scope", "warnings": []}


def main() -> None:
    parser = parse_args("Generate a minimal CodeStable feature evidence pack.")
    parser.add_argument("--feature", required=True)
    parser.add_argument("--design", required=True)
    parser.add_argument("--checklist", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--dod-results")
    parser.add_argument("--gate-results")
    parser.add_argument("--with-archguard", choices=["off", "auto"], default="off")
    parser.add_argument("--with-meta-cc", choices=["off", "auto"], default="off")
    parser.add_argument("--stage", default="implementation.before_review")
    args = parser.parse_args()

    root = repo_root()
    design_input = repo_relative_path(root, args.design)
    checklist_input = repo_relative_path(root, args.checklist)
    out_input = repo_relative_path(root, args.out)
    feature_identity = Path(design_input).parent.name
    result_inputs = {
        "design": design_input,
        "checklist": checklist_input,
        "out": out_input,
    }
    input_paths = {
        "design": Path(args.design),
        "checklist": Path(args.checklist),
    }
    if args.dod_results:
        result_inputs["dod_results"] = repo_relative_path(root, args.dod_results)
        input_paths["dod_results"] = Path(args.dod_results)
    if args.gate_results:
        result_inputs["gate_results"] = repo_relative_path(root, args.gate_results)
        input_paths["gate_results"] = Path(args.gate_results)
    input_digests = {
        name: file_sha256(path)
        for name, path in input_paths.items()
        if path.is_file()
    }
    missing = [path for path in (args.design, args.checklist) if not Path(path).is_file()]
    if missing:
        result = gate_result(
            "evidence-pack",
            args.stage,
            "blocked",
            [f"missing input: {path}" for path in missing],
            feature=feature_identity,
            inputs=result_inputs,
            input_digests=input_digests,
        )
        main_exit(result, args.json_out)

    dod, dod_blocking = load_json(args.dod_results, "DoD results")
    gates, gate_blocking = load_json(args.gate_results, "gate results")
    artifact_blocking = [*dod_blocking, *gate_blocking]
    if artifact_blocking:
        result = gate_result(
            "evidence-pack",
            args.stage,
            "blocked",
            artifact_blocking,
            feature=feature_identity,
            inputs=result_inputs,
            input_digests=input_digests,
        )
        main_exit(result, args.json_out)
    providers = {
        "archguard": provider_status("archguard", args.with_archguard),
        "meta_cc": provider_status("meta-cc", args.with_meta_cc),
    }
    design_text = read_text(args.design)
    checklist_text = read_text(args.checklist)
    risk_lines = "\n".join(f"- {risk}" for risk in residual_risks(dod, gates))

    content = f"""---
doc_type: feature-evidence-pack
feature: {args.feature}
status: generated
---

# {args.feature} evidence pack

## 1. Scope

- Design: `{args.design}`
- Checklist: `{args.checklist}`

## 2. DoD Results

```json
{json.dumps(dod, ensure_ascii=False, indent=2)}
```

## 3. Validation Commands

Extracted from checklist `dod.commands`; see DoD Results for command status.

## 4. Scope And Cleanliness

Design bytes: {len(design_text)}
Checklist bytes: {len(checklist_text)}

## 5. Residual Risks

{risk_lines}

## 6. Provider Signals

```json
{json.dumps(providers, ensure_ascii=False, indent=2)}
```

## 7. Gate Results

```json
{json.dumps(gates, ensure_ascii=False, indent=2)}
```
"""
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(content, encoding="utf-8")
    input_digests["out"] = file_sha256(out)
    result = gate_result(
        "evidence-pack",
        args.stage,
        "passed",
        evidence=[{"out": str(out), "providers": providers}],
        feature=feature_identity,
        inputs=result_inputs,
        input_digests=input_digests,
    )
    main_exit(result, args.json_out)


if __name__ == "__main__":
    main()
