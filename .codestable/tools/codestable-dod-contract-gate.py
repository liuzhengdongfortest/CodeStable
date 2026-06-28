#!/usr/bin/env python3
"""Check that a feature design contains a minimal DoD Contract."""

from __future__ import annotations

from pathlib import Path

from codestable_gate_common import gate_result, main_exit, parse_args, read_text


REQUIRED_PHRASES = [
    "DoD Contract",
    "Validation Commands",
    "Required Artifacts",
]


def main() -> None:
    parser = parse_args("Check a design document for minimal DoD Contract structure.")
    parser.add_argument("--design", required=True, help="Path to feature design markdown")
    parser.add_argument("--stage", default="feature_design.before_approve")
    args = parser.parse_args()

    path = Path(args.design)
    if not path.exists():
        result = gate_result("dod-contract-gate", args.stage, "blocked", [f"design not found: {path}"])
        main_exit(result, args.json_out)

    text = read_text(path)
    missing = [phrase for phrase in REQUIRED_PHRASES if phrase not in text]
    status = "failed" if missing else "passed"
    result = gate_result(
        "dod-contract-gate",
        args.stage,
        status,
        [f"missing required DoD phrase: {item}" for item in missing],
        evidence=[{"design": str(path), "required_phrases": REQUIRED_PHRASES}],
    )
    main_exit(result, args.json_out)


if __name__ == "__main__":
    main()
