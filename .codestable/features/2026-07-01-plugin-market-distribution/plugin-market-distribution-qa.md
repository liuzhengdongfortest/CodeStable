---
doc_type: feature-qa
feature: 2026-07-01-plugin-market-distribution
status: passed
tested: 2026-07-01
round: 1
---

# plugin-market-distribution QA 报告

## 1. Scope And Inputs

- Design: `.codestable/features/2026-07-01-plugin-market-distribution/plugin-market-distribution-design.md`
- Checklist: `.codestable/features/2026-07-01-plugin-market-distribution/plugin-market-distribution-checklist.yaml`
- Review: `.codestable/features/2026-07-01-plugin-market-distribution/plugin-market-distribution-review.md`
- Evidence pack: none
- Gate results: none
- DoD results: none
- Diff basis: `git status --short` + `git diff --cached --stat`
- Baseline dirty files: none；当前 staged 变更均归属本 feature
- Feature type: mixed
- Core evidence gate: 本 feature 改变插件安装 / 分发入口和目录结构，核心路径必须用 CLI / schema / pytest 证明；不涉及浏览器、API、持久化数据迁移或前端用户路径，因此不需要端到端浏览器验证。

## 2. Verification Matrix

| ID | 来源 | 核心性 | 场景 / 风险 | 证据类型 | 命令或动作 | 期望 | 结果 |
|---|---|---|---|---|---|---|---|
| QA-001 | design CMD-001 | core-functional | 插件资产、manifest、目录迁移和排除规则有效 | CLI | `python3 tools/check-plugin-package.py` | exit 0 | pass |
| QA-002 | design CMD-002 | core-functional | 校验器覆盖正常与错误场景 | unit | `python3 -m pytest tests/test_plugin_package.py` | tests pass | pass |
| QA-003 | design CMD-003 | supporting | 既有工具、hooks、reference 路径迁移后仍可用 | regression | `python3 -m pytest tests/` | tests pass | pass |
| QA-004 | design CMD-004 / review focus | core-functional | `skills@latest` 能在隔离副本发现 `cs`，且原工作树状态不变 | CLI smoke | `tmp=$(mktemp -d) ... npx skills@latest add . --list ...` | exit 0，输出包含 `cs` | pass |
| QA-005 | design CMD-005 | supporting | checklist YAML 可解析 | schema | `python3 .codestable/tools/validate-yaml.py --file ... --yaml-only` | exit 0 | pass |
| QA-006 | design CMD-006 | supporting | staged diff 无空白错误 | diff | `git diff --check` | exit 0 | pass |
| QA-007 | design 3.1 / review focus | core-functional | manifest/catalog 字段、版本一致性、非 cs skill 排除 | unit + CLI | `python3 tools/check-plugin-package.py` + `tests/test_plugin_package.py` | schema 与负向用例通过 | pass |
| QA-008 | design 3.2 | non-functional | 根目录无 `cs*` skill 副本、symlink、stub 或 redirect | diff / filesystem | `find . -maxdepth 1 \( -type d -o -type l \) -name 'cs*' -print` | 无输出 | pass |
| QA-009 | attention | non-functional | staged markdown 单文件不超过 300 行 | static | `git diff --cached --name-only -- '*.md' \| xargs wc -l ...` | 最大值 <= 300 | pass |
| QA-010 | cleanliness | non-functional | 无临时缓存、dist、调试残留或方案外文件 | static | `find plugins/codestable ...` + `git diff --cached -G...` | 无阻塞残留 | pass |
| QA-011 | follow-up | core-functional | Codex marketplace metadata 和安装命令可被真实 CLI 接受 | CLI smoke | 临时 `HOME` 下 `codex plugin marketplace add .` + `codex plugin add codestable@codestable` | exit 0 | pass |
| QA-012 | follow-up | core-functional | Claude marketplace / plugin manifest metadata 通过真实 CLI strict 校验 | CLI schema | `claude plugin validate --strict ...` | exit 0 | pass |
| QA-013 | follow-up | non-functional | README 中文 / 英文包含升级命令且不再写 Codex 旧 install 命令 | unit + static | `check-plugin-package.py` + `tests/test_plugin_package.py` | pass | pass |
| QA-014 | follow-up | core-functional | Claude 本地 marketplace 安装和更新命令可执行 | CLI smoke | 临时 `HOME` 下 `claude plugin marketplace add ./` + install + update | exit 0 | pass |

## 3. Command Results

- `python3 tools/check-plugin-package.py` -> exit 0：`Plugin package check passed.`
- `python3 -m pytest tests/test_plugin_package.py` -> exit 0：13 passed。
- `python3 -m pytest tests/` -> exit 0：77 passed。
- `tmp=$(mktemp -d) && mkdir -p "$tmp/repo" && rsync -a --exclude '.git/' ./ "$tmp/repo/" && before=$(git status --short) && (cd "$tmp/repo" && npx skills@latest add . --list) && after=$(git status --short) && test "$before" = "$after"` -> exit 0：输出 `Found 29 skills`，包含 `cs`；根目录 `browser-bridge` 已删除，列表不再包含它。
- 临时 `HOME` 下 `codex plugin marketplace add --json .` + `codex plugin add --json codestable@codestable` -> exit 0：marketplaceName 为 `codestable`，pluginId 为 `codestable@codestable`，version 为 `0.1.0`。
- 临时 `HOME` 下 `claude plugin validate --strict .claude-plugin/marketplace.json`、`claude plugin validate --strict plugins/codestable`、`claude plugin marketplace add ./`、`claude plugin install codestable@codestable`、`claude plugin marketplace update codestable`、`claude plugin update codestable@codestable` -> exit 0：安装成功，更新返回 already at latest 0.1.0。
- 临时 `HOME` 下 `npx skills@latest add . --skill cs -g -y` -> exit 0：`cs` copied；`npx skills@latest update -g -y` -> exit 0：本地 path 来源无 tracked lock，提示无 global skills tracked。
- `python3 .codestable/tools/validate-yaml.py --file .codestable/features/2026-07-01-plugin-market-distribution/plugin-market-distribution-checklist.yaml --yaml-only` -> exit 0：1 passed, 0 failed。
- `git diff --check` -> exit 0：无输出。
- `find . -maxdepth 1 \( -type d -o -type l \) -name 'cs*' -print` -> exit 0：无输出。
- `find plugins/codestable ...` 缓存 / dist / pyc 扫描 -> exit 0：无输出。
- `git diff --cached -G'(TODO|FIXME|XXX|console\.log|console\.error|print\(|fmt\.Println)' --name-only` -> exit 0：命中 design 清洁度规则文本和 `check-plugin-package.py` 的 CLI `print(...)` 正常输出，不是调试残留。

## 4. Scenario Results

- [x] QA-001 插件资产校验：pass
  - Evidence: `check-plugin-package.py` exit 0。
- [x] QA-002 校验器正反向用例：pass
  - Evidence: `tests/test_plugin_package.py` 13 passed，覆盖缺 VERSION、缺 changelog 版本段、manifest 不合法、根目录残留、根目录 standalone skill、非 cs skill、缓存排除、version mismatch、catalog/source 错误和 README 命令。
- [x] QA-003 迁移后既有工具回归：pass
  - Evidence: `python3 -m pytest tests/` 77 passed。
- [x] QA-004 `skills@latest` 兼容发现：pass
  - Evidence: 隔离副本运行 `npx skills@latest add . --list` exit 0，输出包含 `cs`，原工作树状态前后一致。
- [x] QA-005 checklist YAML：pass
  - Evidence: `validate-yaml.py` 1 passed。
- [x] QA-006 diff 空白：pass
  - Evidence: `git diff --check` exit 0。
- [x] QA-007 manifest/catalog 字段与版本一致性：pass
  - Evidence: `check-plugin-package.py` 和 `tests/test_plugin_package.py` 共同覆盖。
- [x] QA-008 根目录无 `cs*` 残留：pass
  - Evidence: 根目录 `find` 无输出，git diff 显示 `cs` / `cs-*` 为 rename 到 `plugins/codestable/skills/`。
- [x] QA-009 markdown 行数约束：pass
  - Evidence: staged markdown 最大 300 行，`README.md` 286 行，`README.en.md` 271 行。
- [x] QA-010 清洁度：pass
  - Evidence: 无缓存 / dist / pyc；命中的 `TODO/FIXME` 与 `print(...)` 均为规则或 CLI 正常输出。
- [x] QA-011 Codex 真实 CLI 本地试装：pass
  - Evidence: 临时 `HOME` 下 marketplace add 和 `codestable@codestable` add 均 exit 0。
- [x] QA-012 Claude strict manifest 校验：pass
  - Evidence: marketplace 和 plugin manifest strict validate 均 exit 0。
- [x] QA-013 README 升级说明：pass
  - Evidence: 校验器和单测覆盖 Codex / Claude / `skills` CLI 升级命令，禁止旧 `codex plugin install codestable` 和未限定 marketplace 的 `/plugin update codestable`。
- [x] QA-014 Claude 本地安装 / 更新：pass
  - Evidence: 临时 `HOME` 下 marketplace add、install、marketplace update、plugin update 均 exit 0；更新命令必须使用 `codestable@codestable`。

## 5. Findings

### failed

none

### blocked

none

### residual-risk

- 未执行远端 GitHub marketplace add / upgrade；当前分支尚未发布。本轮 QA 已验证 Codex 本地 marketplace 试装、Claude strict schema / 本地安装更新和 `skills@latest` 真实发现路径。
- Codex 本地 path marketplace 执行 `codex plugin marketplace upgrade codestable` 会返回非 Git marketplace 错误；README 的 Codex upgrade 命令只适用于 Git marketplace 来源。`skills` CLI 本地 path 安装也没有上游 lock，GitHub 来源升级需发布后复核。
- 根目录独立 skill 已删除；若后续出现带 `SKILL.md` 的根目录 skill，`check-plugin-package` 会失败。

## 6. Cleanliness

- Debug output: pass
- Temporary TODO/FIXME/XXX: pass
- Commented-out code: pass
- Unused imports / dead code from this feature: pass
- Out-of-scope files: pass

## 7. Verdict

- Status: passed
- Next: `cs-feat-accept`
