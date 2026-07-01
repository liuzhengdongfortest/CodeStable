---
doc_type: feature-design-review
feature: 2026-07-01-plugin-market-distribution
status: passed
reviewed: 2026-07-01
round: 5
---

# plugin-market-distribution feature design 审查报告

## 1. Scope And Inputs

- Design: `.codestable/features/2026-07-01-plugin-market-distribution/plugin-market-distribution-design.md`
- Checklist: `.codestable/features/2026-07-01-plugin-market-distribution/plugin-market-distribution-checklist.yaml`
- Intent / brainstorm: none
- Roadmap: none
- Related docs: `.codestable/requirements/plugin-market-distribution.md`、`.codestable/requirements/VISION.md`
- Code facts checked: README / README.en.md、CLAUDE.md、`.gitignore`、`tests/`、`cs-onboard/`、现有根目录 `cs*` skill、`skills@1.5.14` CLI 发现逻辑

### Independent Review

- Status: completed
- Detection: paseo
- Provider / agent: providers.audit=claude/opus / 03643853-dec2-4bc0-af14-155e5947e316
- Raw output: Paseo notification；round 4 的 FDR-001 到 FDR-004 全部关闭，唯一 nit 为 `.gitignore` 措辞精确化
- Merge policy: 已逐条本地核验；唯一 nit 已吸收进 design/checklist；外部平台真实兼容性保留为 residual-risk
- Gate effect: none

## 2. Design Summary

- Goal: 把仓库重组为 `plugins/codestable/` 插件实体，`plugins/codestable/skills/` 成为唯一 `cs*` skill 源。
- Key contracts: Codex manifest `skills=./skills/`；Claude catalog `source=./plugins/codestable`；`skills` CLI 通过根 `.claude-plugin/marketplace.json` 发现插件实体下的 `skills/`。
- Steps: 5 步；覆盖目录迁移、manifest / 版本、gitignore 护栏、校验器、README / CLAUDE / 测试路径引用接入。
- Checks: 20 条；覆盖单一源码目录、三类安装入口、version 路径、gitignore、排除规则、README/CLAUDE 边界、既有测试回归和失败语义。
- Baseline / validation: `check-plugin-package`、新增 plugin pytest、全量既有 pytest、隔离 `skills@latest --list`、YAML 校验、`git diff --check`。

## 3. Findings

### blocking

none

### important

none

### nit

none

### suggestion

none

### learning

- `.codestable/tools/validate-yaml.py` 是本仓库已 onboard 后的运行时副本，适合本 feature 的设计阶段校验；裸环境没有该副本不是本 feature 的目标面。
- `skills@latest add . --list` 的隔离验证只声明保护原工作树，不声明覆盖 HOME 级缓存副作用；实现 / QA 阶段仍需按命令实跑确认。

### praise

- 迁移无损策略已经从结构校验扩展到全量既有测试回归，覆盖 `cs-onboard` 的 tools / reference / hooks 实际耦合点。
- CMD-004 用临时副本执行并比较原工作树 `git status --short`，把“无副作用”变成了可证伪命令。
- 单一 canonical skill 目录避免了旧方案的双份 skill diff 和漂移风险。

## 4. User Review Focus

- 用户需要重点拍板：是否批准本 design 进入 implementation。
- implement 需要重点遵守：用 `git mv` 做目录迁移；不补根 symlink / stub / redirect；同步 README / README.en.md / CLAUDE.md / tests / 工具脚本的路径型引用；保留 `.gitignore` 既有忽略项。
- code review / QA / acceptance 需要重点复核：全量 `pytest tests/`、隔离 `skills@latest --list`、Claude / Codex / `skills` CLI 三入口试装或 schema 事实。

## 5. Evidence Confidence Ledger

| Check | Verdict | Evidence Class | Basis | Follow-up |
|---|---|---|---|---|
| Acceptance Coverage Matrix | pass | E | design 已覆盖三入口、迁移无损、README 边界、gitignore 与排除规则 | none |
| DoD Contract | pass | E | DoD 已含 plugin 测试、全量 pytest、隔离 skills CLI、YAML 校验、diff check | none |
| Steps and checks traceability | pass | E | checklist 5 steps / 20 checks 均可追溯到 design 风险或契约 | none |
| Roadmap contract compliance | n/a | E | 本 feature 非 roadmap 起头 | none |
| Module interface design | pass | C | design 2.1 已定义校验器 seam / depth / test surface | none |
| Validation and artifacts | pass | C | 本地 YAML / diff check 通过，平台兼容性留给实现期验证 | none |

Summary: E=4, C=2, H=0, H-only core checks=none。

## 6. Residual Risk

- Claude 是否接受 `plugins/codestable/skills/` 而非 `.claude/skills/`，仍需实现阶段本地试装或文档事实确认；失败时回 design review。
- Codex catalog / plugin manifest schema 字段能否被当前 Codex 实际接受，仍需实现阶段对照官方文档或试装验证。
- CMD-004 的无写入断言保护原工作树，不覆盖 HOME 级缓存；QA 阶段需要关注命令实际行为。

## 7. Verdict

- Status: passed
- Next: 交给用户整体 review / approval；用户批准后进入 implementation。
