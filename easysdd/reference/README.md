# easysdd reference

本目录只存放**跨子技能共享**的参考材料。各子技能专属的模板和示例已随技能一起放到对应的子技能目录（`easysdd-{skill}/reference.md`）。

## 当前文件

- `shared-conventions.md`：共享元数据口径、`checklist.yaml` 生命周期、收尾推荐
- `tools.md`：`search-yaml.py` / `validate-yaml.py` 的完整用法
- `maintainer-notes.md`：断点恢复和维护扩展说明

## 子技能专属 reference

各子技能的模板、长示例放在各自目录下的 `reference.md`：

| 子技能目录 | reference 内容 |
|---|---|
| `easysdd-feature-design/reference.md` | `design.md` / `checklist.yaml` 模板与 review 提示 |
| `easysdd-compound/reference.md` | pitfall / knowledge 两条轨道模板 |
| `easysdd-decisions/reference.md` | 决策文档模板与示例 |
| `easysdd-tricks/reference.md` | 技巧文档模板与示例 |
| `easysdd-onboarding/reference.md` | `DESIGN.md` 与 `AGENTS.md` 骨架模板 |
| `easysdd-explore/reference.md` | 探索文档结构、写法说明、路由表 |
| `easysdd-issue-fix/reference.md` | 修复汇报、日志调试、`fix-note.md` 模板 |
| `easysdd-libdoc/reference.md` | manifest、条目文档模板、源码提取清单 |

## 使用规则

- 本目录只放真正跨多个子技能复用的内容
- 子技能专属的模板/示例放进该子技能的 `reference.md`，不放这里
- 新增共享文件时，同时更新本索引和根技能目录安排