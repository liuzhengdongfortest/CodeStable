#!/usr/bin/env python3
"""把 knowledge-extractor 草稿翻译成 CodeStable 合规 skill 结构。

摩擦点解：extractor 输出 `.claude/skills/<name>/`（单数 reference/、inventory/、README.md、
根 templates/、可能超 300 行），直接落 plugins/ 会被 check-plugin-package fail。本脚本翻译：
- SKILL.md：去 emoji；≤300 行（超则拆到 references/overview/protocol.md）。
- reference/<x>.md（单数）→ references/<x>/protocol.md（复数 + 子目录）。
- templates/*、examples/* → references/<name>/support/*。
- 丢 README.md、inventory/（CS 不用）。scripts/ 原样保留。
禁止 extractor 直写 plugins/；必须经本翻译再 commit。
"""

from __future__ import annotations

import argparse
import re
import shutil
import sys
from pathlib import Path

sys.dont_write_bytecode = True

_SCRIPTS = Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from config import repo_root  # noqa: E402

_EMOJI = re.compile("[\U0001F000-\U0001FAFF\U00002600-\U000027BF\U0001F1E6-\U0001F1FF⬀-⯿️]")
MAX_SKILL_LINES = 300


def strip_emoji(text: str) -> str:
    return _EMOJI.sub("", text)


def adapt(draft: Path, target_dir: Path) -> list[str]:
    actions: list[str] = []
    if target_dir.exists():
        shutil.rmtree(target_dir)
    (target_dir / "references").mkdir(parents=True)

    # SKILL.md：去 emoji + 行数控制
    src_skill = draft / "SKILL.md"
    if not src_skill.is_file():
        raise FileNotFoundError(f"草稿缺 SKILL.md: {src_skill}")
    lines = strip_emoji(src_skill.read_text(encoding="utf-8")).splitlines()
    if len(lines) > MAX_SKILL_LINES:
        keep, overflow = lines[:MAX_SKILL_LINES - 1], lines[MAX_SKILL_LINES - 1:]
        (target_dir / "references" / "overview").mkdir(parents=True, exist_ok=True)
        (target_dir / "references" / "overview" / "protocol.md").write_text(
            "# overview（从超长 SKILL.md 溢出）\n\n" + "\n".join(overflow) + "\n", encoding="utf-8")
        keep.append("> 详细内容见 references/overview/protocol.md")  # 单行，保证总行数 ≤ MAX
        lines = keep
        actions.append(f"SKILL.md 超 {MAX_SKILL_LINES} 行 → 溢出移至 references/overview/protocol.md")
    (target_dir / "SKILL.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    actions.append("SKILL.md 已去 emoji 并落盘")

    # reference/（单数）→ references/<stem>/protocol.md
    sing = draft / "reference"
    if sing.is_dir():
        for md in sorted(sing.glob("*.md")):
            sub = target_dir / "references" / md.stem
            sub.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(md, sub / "protocol.md")
            actions.append(f"reference/{md.name} → references/{md.stem}/protocol.md")
        # case-studies 等子目录 → support
        for child in sorted(p for p in sing.iterdir() if p.is_dir()):
            dest = target_dir / "references" / child.name / "support"
            dest.mkdir(parents=True, exist_ok=True)
            for f in child.rglob("*"):
                if f.is_file():
                    shutil.copyfile(f, dest / f.name)
            actions.append(f"reference/{child.name}/ → references/{child.name}/support/")

    # templates/、examples/ → references/<name>/support/
    for kind in ("templates", "examples"):
        d = draft / kind
        if d.is_dir():
            dest = target_dir / "references" / kind / "support"
            dest.mkdir(parents=True, exist_ok=True)
            for f in d.rglob("*"):
                if f.is_file():
                    shutil.copyfile(f, dest / f.name)
            actions.append(f"{kind}/ → references/{kind}/support/")

    # scripts/ 原样保留
    if (draft / "scripts").is_dir():
        shutil.copytree(draft / "scripts", target_dir / "scripts")
        actions.append("scripts/ 保留")

    # 丢弃 README.md / inventory/
    for junk in ("README.md", "inventory"):
        if (draft / junk).exists():
            actions.append(f"丢弃 {junk}（CS 结构不用）")
    return actions


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="knowledge-extractor 草稿 → CS 合规结构")
    p.add_argument("--draft", required=True, help="草稿目录，如 .claude/skills/cs-code-review")
    p.add_argument("--target", required=True, help="目标 skill 名，如 cs-code-review")
    p.add_argument("--target-dir", help="覆盖目标目录（测试用）；默认 plugins/codestable/skills/<target>")
    args = p.parse_args(argv)

    draft = Path(args.draft).resolve()
    if args.target_dir:
        target_dir = Path(args.target_dir).resolve()
    else:
        target_dir = repo_root() / "plugins" / "codestable" / "skills" / args.target
    actions = adapt(draft, target_dir)
    print(f"[eval-cs-skill] 适配 {draft} → {target_dir}")
    for a in actions:
        print(f"  - {a}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
