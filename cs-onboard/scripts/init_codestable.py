from __future__ import annotations

import argparse
from pathlib import Path


FACTS = """# facts.md

## 启动必读事实

- [一句当前最影响判断的稳定事实]

## 流程索引

- [做某个已跑通流程前，先读 .cs/notes/YYYY/MM/DD/{slug}.md]
"""

REQUIREMENTS_INDEX = """# [项目或领域] requirements

## 综述

[这是 requirements 主文档。填写真实内容前，先用它统领背景、目标、术语和子文档索引。]

## 目标

[当前阶段最重要的目标。]

## 子文档索引

- [子领域/模块/题型]：`relative/path.md` - [它负责什么]

## 词汇

- [全局术语]：[稳定含义]
"""

DIRS = [
    ".cs/talks",
    ".cs/specs",
    ".cs/issues",
    ".cs/epics",
    ".cs/requirements",
    ".cs/wiki/topics",
    ".cs/notes",
    ".cs/tools",
]


def init_codestable(project: Path, force: bool) -> int:
    project = project.resolve()

    for rel in DIRS:
        (project / rel).mkdir(parents=True, exist_ok=True)

    facts = project / ".cs" / "facts.md"
    requirements_index = project / ".cs" / "requirements" / "index.md"
    created: list[str] = []
    kept: list[str] = []

    if facts.exists() and not force:
        kept.append(str(facts))
    else:
        facts.write_text(FACTS, encoding="utf-8")
        created.append(str(facts))

    if requirements_index.exists() and not force:
        kept.append(str(requirements_index))
    else:
        requirements_index.write_text(REQUIREMENTS_INDEX, encoding="utf-8")
        created.append(str(requirements_index))

    print(f"Initialized CodeStable workspace at {project / '.cs'}")
    print(f"Created or updated files: {len(created)}")
    for path in created:
        print(f"  + {path}")
    if kept:
        print(f"Kept existing files: {len(kept)}")
        for path in kept:
            print(f"  = {path}")

    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Initialize a CodeStable .cs workspace.")
    parser.add_argument("--project", default=".", help="Project root to initialize.")
    parser.add_argument("--force", action="store_true", help="Overwrite existing template files.")
    args = parser.parse_args()

    return init_codestable(Path(args.project), args.force)


if __name__ == "__main__":
    raise SystemExit(main())
