#!/usr/bin/env python3
"""自治路径 A（轻量 cron，默认）：实验队列。

- enqueue：把一个实验的某 stage 入队（experiments/.queue.jsonl）。
- run-next：取下一个 queued 项跑（runner=eval / optimize），幂等，供宿主 cron/CI 反复调用。
路径 B（BAIME loop-backlog）见 references/autonomy/protocol.md，绑 Node/backlog/worktree，仅 Claude Code 宿主。
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.dont_write_bytecode = True

_SCRIPTS = Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

import optimize  # noqa: E402
import runner    # noqa: E402
from config import repo_root  # noqa: E402


def _queue_path() -> Path:
    return repo_root() / "experiments" / ".queue.jsonl"


def _load() -> list[dict]:
    p = _queue_path()
    if not p.is_file():
        return []
    return [json.loads(line) for line in p.read_text(encoding="utf-8").splitlines() if line.strip()]


def _save(items: list[dict]) -> None:
    p = _queue_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("\n".join(json.dumps(i, ensure_ascii=False) for i in items) + "\n", encoding="utf-8")


def enqueue(experiment: str, stage: str) -> None:
    items = _load()
    items.append({"experiment": experiment, "stage": stage, "status": "queued"})
    _save(items)


def run_next() -> int:
    items = _load()
    for item in items:
        if item.get("status") == "queued":
            item["status"] = "running"
            _save(items)
            exp = item["experiment"]
            if item["stage"] == "optimize":
                rc = optimize.main(["--experiment", exp])
            else:
                rc = runner.main(["--experiment", exp])
            item["status"] = "done" if rc == 0 else f"failed:{rc}"
            _save(items)
            return rc
    print("[eval-cs-skill] 队列空")
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="eval-cs-skill 实验队列（自治路径 A）")
    p.add_argument("--experiment")
    p.add_argument("--stage", default="eval", choices=["eval", "optimize"])
    p.add_argument("--run-next", action="store_true")
    p.add_argument("--list", action="store_true")
    args = p.parse_args(argv)

    if args.list:
        for i in _load():
            print(f"  [{i['status']}] {i['stage']} {i['experiment']}")
        return 0
    if args.run_next:
        return run_next()
    if args.experiment:
        enqueue(args.experiment, args.stage)
        print(f"[eval-cs-skill] 入队 {args.stage} {args.experiment}")
        return 0
    p.error("需 --experiment / --run-next / --list 之一")


if __name__ == "__main__":
    raise SystemExit(main())
