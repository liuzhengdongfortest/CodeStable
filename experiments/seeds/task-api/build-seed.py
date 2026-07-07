#!/usr/bin/env python3
"""构建 seed-1（taskhub）：按 stages/ 顺序覆盖式落盘并逐阶段 git commit。

用法：
  python3 build-seed.py --out /tmp/seed-taskhub          # 构建含演进历史的 repo
  python3 build-seed.py --verify                          # 构建到临时目录并跑测试

设计（见 docs/cs-skill-e2e-eval-plan.md）：
- seed 以「构建脚本 + 阶段快照」入库，避免嵌套 git repo；每次构建产物确定性一致
  （固定提交日期/作者），支持 e2e runner 的独立 workdir 隔离。
- 每个 stages/NN-name/ 目录只含该阶段新增/修改的文件（覆盖式增量快照）+ COMMIT.txt。
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
STAGES = HERE / "stages"

GIT_ENV_BASE = {
    "GIT_AUTHOR_NAME": "taskhub-dev",
    "GIT_AUTHOR_EMAIL": "dev@taskhub.invalid",
    "GIT_COMMITTER_NAME": "taskhub-dev",
    "GIT_COMMITTER_EMAIL": "dev@taskhub.invalid",
}
# 固定提交日期序列：可复现构建（同输入同 hash）
STAGE_DATES = [
    "2026-03-02T10:17:00+08:00",
    "2026-03-11T15:42:00+08:00",
    "2026-03-25T09:03:00+08:00",
    "2026-04-08T20:31:00+08:00",
    "2026-04-21T11:56:00+08:00",
]


def run(cmd: list[str], cwd: Path, env: dict | None = None) -> None:
    import os
    full_env = {**os.environ, **GIT_ENV_BASE, **(env or {})}
    subprocess.run(cmd, cwd=cwd, check=True, env=full_env,
                   stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)


def build(out: Path) -> None:
    if out.exists() and any(out.iterdir()):
        sys.exit(f"拒绝构建：{out} 已存在且非空")
    out.mkdir(parents=True, exist_ok=True)
    run(["git", "init", "-q", "-b", "main"], out)

    stages = sorted(p for p in STAGES.iterdir() if p.is_dir())
    if len(stages) > len(STAGE_DATES):
        sys.exit("阶段数超过日期序列，请补 STAGE_DATES")
    for i, stage in enumerate(stages):
        message = (stage / "COMMIT.txt").read_text(encoding="utf-8").strip()
        for src in stage.rglob("*"):
            if src.name == "COMMIT.txt" or src.is_dir():
                continue
            dst = out / src.relative_to(stage)
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
        date = STAGE_DATES[i]
        run(["git", "add", "-A"], out)
        run(["git", "commit", "-q", "-m", message], out,
            env={"GIT_AUTHOR_DATE": date, "GIT_COMMITTER_DATE": date})
    print(f"seed 构建完成：{out}（{len(stages)} commits）")


def verify() -> int:
    with tempfile.TemporaryDirectory(prefix="seed-taskhub-") as tmp:
        out = Path(tmp) / "repo"
        build(out)
        r = subprocess.run([sys.executable, "-m", "pytest", "-q"], cwd=out)
        log = subprocess.run(["git", "log", "--oneline"], cwd=out,
                             capture_output=True, text=True)
        print(log.stdout.strip())
        return r.returncode


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--out")
    p.add_argument("--verify", action="store_true")
    args = p.parse_args()
    if args.verify:
        return verify()
    if not args.out:
        p.error("--out 或 --verify 必选其一")
    build(Path(args.out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
