---
name: cs-onboard
description: 把新仓库或有零散文档的仓库接入 CodeStable 体系，两条路径自动判断：空仓库从零搭骨架，已有文档走审计 + 迁移映射。触发：用户说"在这个项目里用 CodeStable"、"搭 CodeStable 结构"、"初始化 CodeStable"、"迁移到 CodeStable"。
---

# cs-onboard

把仓库**接入 CodeStable 工作流体系**——白纸或已有零散文档的都行。本技能只做两件事：**搭骨架**、**归旧档**。骨架搭好后子工作流（feature / issue / compound 等）即可直接运行。

---

## 两条路径

| 路径 | 适用 | 产出 |
|---|---|---|
| **空仓库** | 仓库内无 spec 类文档，也没有 `codestable/` | 完整骨架 + 必要骨架文件 |
| **迁移** | 仓库内有零散文档 / `docs/` / 部分 `codestable/` 结构 | 审计报告 + 迁移映射方案（用户逐条确认）+ 落盘 |

启动后**先扫一次自动判断**，不要让用户选——TA 大概率不知道项目里现有哪些文档。扫描结果模糊（如只有 README）就明说判断依据并问用户。

---

## 标准骨架（目标状态）

> 共享路径与命名约定的权威版本是项目里的 `codestable/reference/shared-conventions.md`——本技能从技能包复制过去。下面只列 onboarding 创建 / 检查的骨架文件。

```
codestable/
├── requirements/               需求聚合根（空目录 .gitkeep）
├── architecture/
│   └── ARCHITECTURE.md         架构总入口（首次创建为占位模板）
├── roadmap/                    规划层聚合根
├── features/                   feature 聚合根
├── issues/                     issue 聚合根
├── compound/                   沉淀类统一目录（learning / trick / decision / explore）
├── tools/                      跨工作流共享脚本（onboarding 释放）
│   ├── search-yaml.py
│   └── validate-yaml.py
└── reference/                  跨子技能共享参考（onboarding 释放）
    ├── shared-conventions.md
    ├── tools.md
    └── maintainer-notes.md
```

**项目硬约束文件**（`AGENTS.md` / `CLAUDE.md` / 其他 AI 工具约定的常驻上下文文件，下统称"约束文件"）在项目根目录，**不在 `codestable/` 里**。onboarding 检查存不存在，不存在时**问用户建哪个**（不预设默认——AI 工具自己注入提示词会告诉模型该读哪个，偏好留给用户）；建好后**不代写实质内容**——内容高度项目相关。缺它不阻塞 onboarding 完成，但 feature / issue / acceptance 启动前要补齐或明确接受暂无项目级硬约束入口。

---

## 启动检查

**先扫再说话**：

1. **检查 `codestable/`**：不存在 → 空仓库候选；存在但不完整 → 迁移（部分补齐）
2. **检查旧 `easysdd/`**（2026 年改名遗留）——CodeStable 旧名 easysdd，2026 改名后目录从 `easysdd/` 改到 `codestable/`。仓库有 `easysdd/`（无 `codestable/`）时停下来：

   > 检测到旧版 `easysdd/`（CodeStable 前身）。建议直接 `git mv easysdd codestable`，结构 / frontmatter 完全兼容，rename 后即用。要我执行吗？

   同意 → `git mv easysdd codestable`，按迁移路径走（这时只需补齐可能缺失的 `tools/` 和 `reference/`）。想保留旧目录 → 告诉他子技能只读 `codestable/`，旧目录不会被读；按空仓库路径走新骨架

3. **Glob 全仓库 `.md`**（排除 `node_modules/` `.git/`）：根目录 `DESIGN.md` / `ARCHITECTURE.md` / `SPEC.md` / `README.md`；`docs/` `doc/` `design/` `spec/` `wiki/`；现有 `codestable/` 下文件
4. **检查项目硬约束文件**（根目录的 `AGENTS.md` / `CLAUDE.md` 等，任一存在即视为已有）
5. **汇报扫描结论**：找到的相关文档（列路径）+ 走哪条路径 + 判断依据 + 不确定项

---

## 空仓库路径

**步骤 1：和用户确认范围**

- 项目名 / 简介（用于填 `ARCHITECTURE.md` 占位）
- 项目硬约束文件是否已有（`AGENTS.md` / `CLAUDE.md` 等），没有的话现在建哪个 / 之后再说

**步骤 2：创建目录骨架**

按下面顺序执行，**不等用户逐步确认**——骨架是整体一次性的：

- `codestable/{requirements,roadmap,features,issues,compound}/.gitkeep`
- `codestable/architecture/ARCHITECTURE.md`（占位模板见同目录 `reference.md`）
- `codestable/tools/`（用 `cp -rf` / `Copy-Item -Recurse -Force` 整目录拷贝技能包 `cs-onboard/tools/`，**不要 Read 再 Write**）
- `codestable/reference/`（同上）

> **落盘用 shell 整目录覆盖**，不要 Read 再 Write——这两个目录是机器共享资产，Read+Write 会截断大文件、改缩进、吃空行，还慢费 token。具体命令见迁移路径步骤 4。

**步骤 3：项目硬约束文件提醒**

`AGENTS.md` / `CLAUDE.md` 都不存在时：

> 项目根还没有 AI 常驻上下文文件——它是 CodeStable 子工作流的"项目硬约束入口"，记录代码规范、已知坑、禁止事项。要建哪个？`AGENTS.md`（社区通用，多 AI 工具会读）/ `CLAUDE.md`（Claude Code 专属）/ 其他文件名（如 `.cursorrules`）/ 之后自己建？

**不预设默认**——用户答了再建。建哪个文件名，里面用同一份最小模板（见 `reference.md`）引导填写。之后 → 记入汇报，告诉用户"下次触发 feature/issue 前补上"。

**步骤 4：验收汇报**

列建了哪些文件：

> CodeStable 骨架已就绪。现在可以：开始新功能 `cs-feat` / 报告问题 `cs-issue` / 沉淀知识 `cs-learn`

---

## 迁移路径

**步骤 1：生成审计报告**

| 现有文件 | 推测内容类型 | 建议归入 CodeStable | 置信度 |
|---|---|---|---|
| `docs/DESIGN.md` | 项目架构 | `codestable/architecture/ARCHITECTURE.md` | 高 |
| `docs/feature-auth.md` | 功能设计稿 | `codestable/features/YYYY-MM-DD-auth/auth-design.md` | 中 |
| `SPEC.md` | 功能需求？ | 需用户确认 | 低 |

**置信度**：高 = 语义明确匹配；中 = 可推断有歧义；低 = 不明确或映射多个位置都合理。

**步骤 2：逐条对齐**

中 / 低置信度的用 `AskUserQuestion` 问：

- 中：给推断理由，问"按这个方式归位？"
- 低：描述文件内容，给 2-3 个候选位置 + "跳过"

高置信度不逐条问但要在汇报里列，给用户复审机会——逐条问会让节奏失控。

**步骤 3：处理已部分存在的 codestable/**

- 命名不符规范（`YYYY-MM-DD-{slug}` 格式）但有内容 → 提示用户问是否重命名
- 空占位（`.gitkeep` / 空 `.md`）→ 直接补齐不问

**步骤 4：补齐缺失骨架**

对照标准骨架补齐**用户确认后仍缺失**的目录 / 文件。已有内容不覆盖。

**`codestable/tools/` 和 `codestable/reference/` 一律用技能包新版本覆盖**——这两个目录是技能包维护的共享资产，权威源在 `cs-onboard/tools/` 和 `cs-onboard/reference/`，项目里的只是落盘副本。技能包升级后再跑 onboarding 的目的之一就是刷新副本，留旧版本会让子技能按过时口径工作。

覆盖前在汇报列出被覆盖文件让用户知道；用户明确说"我改过 tools/xxx.py 请保留"才例外保留并标红。这是迁移路径**唯一强制覆盖**的动作，其他已有文件遵守"不经确认不动"。

**落盘命令**：

```bash
# macOS / Linux
cp -rf <技能包路径>/cs-onboard/tools/.      codestable/tools/
cp -rf <技能包路径>/cs-onboard/reference/.  codestable/reference/

# Windows PowerShell
Copy-Item -Recurse -Force <技能包路径>\cs-onboard\tools\*      CodeStable\tools\
Copy-Item -Recurse -Force <技能包路径>\cs-onboard\reference\*  CodeStable\reference\
```

不要：Read+Write 手工搬（截断 / 改缩进）、一个个 cp（多步骤多出错）、先比 diff（规则就是无条件覆盖）。

技能包路径一般是 skill 安装目录（`~/.claude/skills/cs-onboard/` 或插件目录）。不确定先 `ls` 定位。拷完 `ls codestable/tools/ codestable/reference/` 验证。

**步骤 5：处理不迁移的文件**

用户选"跳过"的文件：**不移动 / 不删除 / 不重命名**，汇报标"保留原位（未纳入 CodeStable）"。**绝不允许未经确认就动**——onboarding 只允许 AI 整理不允许替用户做删除决定。

**步骤 6：项目硬约束文件提醒**（同空仓库路径步骤 3）

**步骤 7：验收汇报**

列：迁移文件清单（from → to）、新建骨架、未迁移文件（保留原位）、下一步建议。

---

## 骨架文件模板

`ARCHITECTURE.md` 占位模板和项目硬约束文件最小模板见同目录 `reference.md`。

---

## 退出条件

- [ ] `codestable/` 八个子目录都存在
- [ ] `codestable/tools/` 和 `codestable/reference/` 已从技能包复制
- [ ] `codestable/architecture/ARCHITECTURE.md` 已建
- [ ] 迁移路径：每条映射都有明确处理结果（迁移 / 保留原位）
- [ ] 迁移路径：没有未经确认就移动的文件
- [ ] 项目硬约束文件状态已明确（`AGENTS.md` / `CLAUDE.md` 任一存在，或用户已选定建哪个 / 知道需要补）
- [ ] 验收汇报已给出

---

## 容易踩的坑

- **未经确认就移动 / 删除已有文件**——迁移核心原则是用户拍板
- **替用户填硬约束文件实质内容**——必须项目 owner 来定，AI 只提供模板
- **预设默认建 `AGENTS.md`**——必须问用户选哪个，AI 工具自己会注入提示词决定该读哪个
- **建完骨架立刻开始 feature/issue**——onboarding 是"搭环境"不是"开始干活"
- **把硬约束文件建到 `codestable/` 里**——它是根目录文件
- **低置信度直接执行**——低 = 必须问
- **`codestable/tools/` 和 `codestable/reference/` 走"不覆盖"保守策略**——这两个**必须**用技能包新版本覆盖，否则升级后用户停留在过时口径
- **用 Read + Write 手工搬**——必须 `cp -rf` / `Copy-Item -Recurse -Force` 整目录覆盖
- **Glob 时忘记排除 `node_modules/` `.git/`**——会让扫描结果充斥噪声

---

## 相关文档

- `codestable/reference/system-overview.md` — CodeStable 体系总览
- `codestable/reference/shared-conventions.md` — 目录结构和共享口径的权威版本
- 项目硬约束入口（`AGENTS.md` / `CLAUDE.md` / 等）— 全项目级 AI 常驻上下文
- `codestable/architecture/ARCHITECTURE.md` — 架构总入口骨架
