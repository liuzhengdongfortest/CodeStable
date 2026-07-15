# release stage 协议

把收敛的实验结论固化回被测 skill，打版本，跑回归。**两步走**，绕开 knowledge-extractor 与 CS 包结构的冲突。

## 前置

- optimize 已收敛（`iteration-N.md` 显示 standard 或 meta-focused），或明确以 practical 停止且 owner 接受。
- 有胜出 variant（`experiments/{skill}-{NNN}/variants/iter-{n}.md`）。

## 1. 抽取草稿（BAIME knowledge-extractor）

通过 Task subagent 调 `knowledge-extractor`，把收敛实验抽成 skill 草稿：

```
knowledge-extractor(experiment_dir=experiments/{skill}-{NNN}, skill_name={skill})
→ .claude/skills/{skill}/   # gitignored 暂存区（草稿源，勿直接 commit）
```

**禁止** extractor 直接写 `plugins/codestable/skills/`——它的单数 `reference/`、`inventory/`、`README.md`、可能超 300 行会被 `tools/check-plugin-package.py` fail。

## 2. 适配成 CS 合规结构

```bash
python3 {skill_dir}/scripts/adapt_extracted_skill.py --draft .claude/skills/{skill} --target {skill}
```

翻译：去 emoji；SKILL.md ≤300 行（超则溢出到 `references/overview/protocol.md`）；单数 `reference/<x>.md` → 复数 `references/<x>/protocol.md`；`templates/`、`examples/` → `references/<name>/support/`；丢 `README.md`、`inventory/`；保留 `scripts/`。

产物落 `plugins/codestable/skills/{skill}/`。人工过一遍：胜出 variant 的关键改进（措辞/结构）确已并入 SKILL.md，并按 `[measured: evidence_pointer]` 标注被实验证实的声明。

## 3. 回归电池

```bash
python3 {skill_dir}/scripts/regression.py --experiment experiments/{skill}-{NNN} --record-baseline   # 首次
python3 {skill_dir}/scripts/regression.py --experiment experiments/{skill}-{NNN} --candidate iter-{n} --n 5
```

判据：`improved`=candidate CI 下界 > baseline CI 上界；`regressed`=candidate CI 上界 < baseline CI 下界（**阻断 release**）；`inconclusive`=需更多样本或此 release 非提升。仅 `regressed` 阻断。

## 4. 打版本

```bash
python3 {skill_dir}/scripts/bump_version.py --to X.Y.Z --note "……"
```

同步 VERSION + codex/claude plugin.json + 两个 marketplace.json + CHANGELOG。

## 5. 校验

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q tests -rs
PYTHONDONTWRITEBYTECODE=1 python3 tools/check-plugin-package.py --root . --json
PYTHONDONTWRITEBYTECODE=1 python3 plugins/codestable/skills/cs-onboard/tools/codestable-runtime-sync.py --root . --source-skill-dir plugins/codestable/skills/cs-onboard --check --json
PYTHONDONTWRITEBYTECODE=1 python3 plugins/codestable/skills/cs-onboard/tools/codestable-doctor.py --root . --json
git diff --check
```

模板或 gate 变更时，先按 `cs-onboard` managed-assets 规则完成 runtime sync，再跑上面的 `--check`；任一 JSON gate 的 `ok` 非 true 都阻断发布。

## 退出条件

- [ ] 草稿经 adapt 落 `plugins/`，`check-plugin-package.py` 通过。
- [ ] 回归判定非 `regressed`。
- [ ] 版本 5 处一致 + CHANGELOG 有段。
- [ ] 被实验证实的 skill 声明按 `[measured: evidence_pointer]` 标注。
- [ ] 全量 pytest、package、runtime sync check、doctor 与 `git diff --check` 全部通过。
