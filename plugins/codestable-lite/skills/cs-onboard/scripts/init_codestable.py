from __future__ import annotations

import argparse
from pathlib import Path


FACTS = """# facts.md

## 启动必读事实

- [一句当前最影响判断的稳定事实]

## 流程索引

- [做某个已跑通流程前，先读 .cs/notes/YYYY/MM/DD/{短语}.md]
"""

PROJECT_SPEC_INDEX = """# Project Spec

## 这个项目是什么

[面向第一次进入项目的开发者，说明项目解决什么问题、服务谁、当前最重要的能力是什么。]

## 当前方向

[项目接下来往哪里走，哪些能力正在强化，哪些方向暂不优先。]

## 能力地图

- [能力区]：[它负责什么，读者要深入时去哪里看]

## 架构地图

- [系统 / 模块 / 子系统]：[它负责什么，和谁交互，读者要深入时去哪里看]

## 统一语言

- [术语]：[在本 spec 范围内的稳定含义]

## 阅读路径

- 想理解用户和场景：读 `[path]`
- 想理解架构分工：读 `[path]`
"""

DIRS = [
    ".cs/talks",
    ".cs/spec",
    ".cs/issues",
    ".cs/epics",
    ".cs/notes",
    ".cs/tools",
]


def init_codestable(project: Path, force: bool) -> int:
    project = project.resolve()

    for rel in DIRS:
        (project / rel).mkdir(parents=True, exist_ok=True)

    facts = project / ".cs" / "facts.md"
    project_spec_index = project / ".cs" / "spec" / "index.md"
    created: list[str] = []
    kept: list[str] = []

    if facts.exists() and not force:
        kept.append(str(facts))
    else:
        facts.write_text(FACTS, encoding="utf-8")
        created.append(str(facts))

    if project_spec_index.exists() and not force:
        kept.append(str(project_spec_index))
    else:
        project_spec_index.write_text(PROJECT_SPEC_INDEX, encoding="utf-8")
        created.append(str(project_spec_index))

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
