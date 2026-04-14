#!/usr/bin/env python3
"""
validate-yaml.py — Validate YAML frontmatter syntax in markdown files.

Scans markdown files for YAML frontmatter (--- ... ---) and checks:
  1. Frontmatter block is properly delimited (opening and closing ---)
  2. YAML syntax is valid (parseable without errors)
  3. (Optional) Required fields are present (--require flag)

Designed for AI agent use: structured output, exit code reflects pass/fail,
no required external dependencies (falls back to builtin parser if PyYAML unavailable).

Usage examples:
  # Validate all .md files under easysdd/features
  python easysdd/tools/validate-yaml.py --dir easysdd/features

  # Validate a single file
  python easysdd/tools/validate-yaml.py --file easysdd/features/2026-04-11-auth/design.md

  # Check that required fields exist in frontmatter
  python easysdd/tools/validate-yaml.py --dir easysdd/features --require doc_type --require status

  # JSON output for programmatic consumption
  python easysdd/tools/validate-yaml.py --dir docs/api --json

  # Validate the libdoc manifest
  python easysdd/tools/validate-yaml.py --file docs/api/_manifest.yaml --yaml-only
"""

import argparse
import json
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# YAML parsing
# ---------------------------------------------------------------------------

_HAS_PYYAML = False
try:
    import yaml  # type: ignore
    _HAS_PYYAML = True
except ImportError:
    pass


def _builtin_parse_yaml(text: str) -> dict:
    """Minimal YAML parser for flat key-value frontmatter (no nested structures)."""
    result: dict = {}
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or ":" not in stripped:
            continue
        key, _, raw = stripped.partition(":")
        val = raw.strip()
        # Inline list
        if val.startswith("[") and val.endswith("]"):
            inner = val[1:-1]
            result[key.strip()] = [
                item.strip().strip("'\"") for item in inner.split(",") if item.strip()
            ]
        else:
            result[key.strip()] = val.strip("'\"") if val else ""
    return result


def parse_yaml_text(text: str) -> tuple[dict | None, str | None]:
    """
    Parse a YAML string. Returns (parsed_dict, None) on success,
    or (None, error_message) on failure.
    """
    if _HAS_PYYAML:
        try:
            result = yaml.safe_load(text)
            if result is None:
                return {}, None
            if not isinstance(result, dict):
                return None, f"Expected a mapping, got {type(result).__name__}"
            return result, None
        except yaml.YAMLError as exc:
            return None, str(exc)
    else:
        # Builtin fallback — can only detect gross syntax issues
        try:
            result = _builtin_parse_yaml(text)
            return result, None
        except Exception as exc:
            return None, str(exc)


# ---------------------------------------------------------------------------
# Frontmatter extraction
# ---------------------------------------------------------------------------

def extract_frontmatter(text: str) -> tuple[str | None, str | None]:
    """
    Extract YAML frontmatter from a markdown file.
    Returns (frontmatter_text, None) on success,
    or (None, error_message) if frontmatter is missing or malformed.
    """
    if not text.startswith("---"):
        return None, "No opening '---' delimiter found"

    end = text.find("\n---", 3)
    if end == -1:
        return None, "No closing '---' delimiter found (frontmatter block not terminated)"

    fm_text = text[3:end].strip()
    if not fm_text:
        return None, "Frontmatter block is empty"

    return fm_text, None


# ---------------------------------------------------------------------------
# Validation logic
# ---------------------------------------------------------------------------

class ValidationResult:
    def __init__(self, file_path: str):
        self.file = file_path
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.fields: list[str] = []  # fields found in frontmatter

    @property
    def ok(self) -> bool:
        return len(self.errors) == 0

    def to_dict(self) -> dict:
        d: dict = {"file": self.file, "status": "pass" if self.ok else "fail"}
        if self.errors:
            d["errors"] = self.errors
        if self.warnings:
            d["warnings"] = self.warnings
        if self.fields:
            d["fields"] = self.fields
        return d


def validate_markdown_file(
    file_path: Path,
    required_fields: list[str] | None = None,
    base_dir: Path | None = None,
) -> ValidationResult:
    """Validate YAML frontmatter in a single markdown file."""
    display_path = (
        str(file_path.relative_to(base_dir)) if base_dir else str(file_path)
    )
    result = ValidationResult(display_path)

    try:
        text = file_path.read_text(encoding="utf-8")
    except OSError as exc:
        result.errors.append(f"Cannot read file: {exc}")
        return result

    fm_text, extract_err = extract_frontmatter(text)
    if extract_err:
        result.errors.append(extract_err)
        return result

    parsed, parse_err = parse_yaml_text(fm_text)
    if parse_err:
        result.errors.append(f"YAML syntax error: {parse_err}")
        return result

    result.fields = list(parsed.keys()) if parsed else []

    if required_fields:
        for field in required_fields:
            if field not in (parsed or {}):
                result.errors.append(f"Missing required field: '{field}'")

    if not _HAS_PYYAML:
        result.warnings.append(
            "PyYAML not installed — using builtin fallback parser "
            "(may miss some syntax errors). Install with: pip install pyyaml"
        )

    return result


def validate_yaml_file(
    file_path: Path,
    required_fields: list[str] | None = None,
    base_dir: Path | None = None,
) -> ValidationResult:
    """Validate a pure YAML file (not markdown with frontmatter)."""
    display_path = (
        str(file_path.relative_to(base_dir)) if base_dir else str(file_path)
    )
    result = ValidationResult(display_path)

    try:
        text = file_path.read_text(encoding="utf-8")
    except OSError as exc:
        result.errors.append(f"Cannot read file: {exc}")
        return result

    parsed, parse_err = parse_yaml_text(text)
    if parse_err:
        result.errors.append(f"YAML syntax error: {parse_err}")
        return result

    result.fields = list(parsed.keys()) if parsed else []

    if required_fields:
        for field in required_fields:
            if field not in (parsed or {}):
                result.errors.append(f"Missing required field: '{field}'")

    if not _HAS_PYYAML:
        result.warnings.append(
            "PyYAML not installed — using builtin fallback parser. "
            "Install with: pip install pyyaml"
        )

    return result


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

def print_text_results(results: list[ValidationResult]) -> None:
    passed = sum(1 for r in results if r.ok)
    failed = len(results) - passed

    print(f"Validated {len(results)} file(s): {passed} passed, {failed} failed.\n")

    for r in results:
        icon = "✓" if r.ok else "✗"
        print(f"  {icon} {r.file}")
        for err in r.errors:
            print(f"      ERROR: {err}")
        for warn in r.warnings:
            print(f"      WARN:  {warn}")

    if failed > 0:
        print(f"\n{failed} file(s) have YAML errors.")
    else:
        print("\nAll files valid.")


def print_json_results(results: list[ValidationResult]) -> None:
    output = {
        "total": len(results),
        "passed": sum(1 for r in results if r.ok),
        "failed": sum(1 for r in results if not r.ok),
        "results": [r.to_dict() for r in results],
    }
    print(json.dumps(output, indent=2, ensure_ascii=False))


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate YAML frontmatter in markdown files or pure YAML files.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument(
        "--dir",
        type=str,
        help="Directory to scan recursively for .md files",
    )
    source.add_argument(
        "--file",
        type=str,
        help="Single file to validate",
    )

    parser.add_argument(
        "--require",
        action="append",
        default=[],
        metavar="FIELD",
        help="Require this field in frontmatter (repeatable)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="json_output",
        help="Output results as JSON",
    )
    parser.add_argument(
        "--yaml-only",
        action="store_true",
        help="Treat input as pure YAML (not markdown with frontmatter). "
             "Use for .yaml/.yml files like _manifest.yaml.",
    )

    args = parser.parse_args()
    results: list[ValidationResult] = []

    if args.file:
        fp = Path(args.file)
        if not fp.exists():
            print(f"Error: File not found: {fp}", file=sys.stderr)
            sys.exit(2)

        if args.yaml_only or fp.suffix in (".yaml", ".yml"):
            results.append(validate_yaml_file(fp, args.require))
        else:
            results.append(validate_markdown_file(fp, args.require))

    elif args.dir:
        dp = Path(args.dir)
        if not dp.is_dir():
            print(f"Error: Directory not found: {dp}", file=sys.stderr)
            sys.exit(2)

        # Scan .md files
        md_files = sorted(dp.rglob("*.md"))
        # Also scan .yaml/.yml files if --yaml-only or auto-detect
        yaml_files = sorted(dp.rglob("*.yaml")) + sorted(dp.rglob("*.yml"))

        if not md_files and not yaml_files:
            print(f"No .md or .yaml files found under {dp}", file=sys.stderr)
            sys.exit(2)

        for md in md_files:
            results.append(validate_markdown_file(md, args.require, dp))

        for yf in yaml_files:
            results.append(validate_yaml_file(yf, args.require, dp))

    if args.json_output:
        print_json_results(results)
    else:
        print_text_results(results)

    # Exit code: 0 if all pass, 1 if any fail
    sys.exit(0 if all(r.ok for r in results) else 1)


if __name__ == "__main__":
    main()
