---
name: cs-onboard
description: 把新仓库或有零散文档的仓库接入 CodeStable 体系，两条路径自动判断：空仓库从零搭骨架，已有文档走审计 + 迁移映射。触发：用户说"在这个项目里用 CodeStable"、"搭 CodeStable 结构"、"初始化 CodeStable"、"迁移到 CodeStable"。
---

# cs-onboard

把一个仓库**接入 CodeStable 工作流体系**——无论它是一张白纸，还是已经有零散文档的仓库。本技能只做两件事：**搭骨架**、**归旧档**。骨架搭好之后各子工作流（feature / issue / compound 等）即可直接在其上运行，不再需要解释目录在哪里。

---

## 两条路径

| 路径 | 适用情况 | 产出 |
|---|---|---|
| **空仓库路径** | 仓库内无任何 spec 类文档，也没有 `codestable/` 目录 | 完整的 `codestable/` 目录骨架 + 必要的骨架文件 |
| **迁移路径** | 仓库内已有零散文档、`docs/` 目录、架构文档、设计稿，或部分 `codestable/` 结构 | 审计报告 + 迁移映射方案（用户逐一确认）+ 落盘 |

启动后**先做一次扫描自动判断**，不要让用户自己选——TA 大概率不知道项目里现在有哪些文档。扫描结果模糊（比如只有一个 README）就明说判断依据并问用户确认。

---

## 涉及的路径

> onboarding 完成后，共享路径与命名约定的权威版本是项目里的 `codestable/reference/shared-conventions.md`——由本技能从技能包里复制过去。下面只列 onboarding 需要创建或检查的骨架文件。

### 标准骨架（目标状态）

onboarding 完成后仓库里应该存在以下骨架：

```
codestable/
├── requirements/               ← 需求聚合根（空目录，.gitkeep）："为什么要有这个能力"（只记现状）
├── architecture/
│   └── ARCHITECTURE.md         ← 架构总入口骨架（首次创建时为占位模板）："用什么结构实现"（只记现状）
├── roadmap/                    ← 规划层聚合根（空目录，.gitkeep）："接下来打算怎么走"，独立于现状档案
├── features/                   ← feature 聚合根（空目录，.gitkeep）
├── issues/                     ← issue 聚合根（空目录，.gitkeep）
├── compound/                   ← 沉淀类统一目录（空目录，.gitkeep）：learning / trick / decision / explore 四种文档按 doc_type + 文件名中间的类型段（YYYY-MM-DD-{doc_type}-{slug}.md）区分
├── tools/                      ← 跨工作流共享的脚本工具（由 onboarding 从技能包释放）
│   ├── search-yaml.py          ← 通用 YAML frontmatter 搜索工具
│   └── validate-yaml.py        ← YAML 语法校验工具
└── reference/                  ← 跨子技能共享的参考文档（由 onboarding 从技能包释放）
    ├── shared-conventions.md   ← 共享元数据口径、checklist 生命周期、阶段收尾推荐
    ├── tools.md                ← 共享脚本用法参考
    └── maintainer-notes.md     ← 断点恢复、扩展点、维护规则
```

`AGENTS.md` 在项目根目录，**不在 `codestable/` 里**。onboarding 会检查它存不存在，不存在时提醒用户但**不代替用户写**——AGENTS.md 的内容高度项目相关，必须由人来填。缺少 `AGENTS.md` 不阻塞 onboarding 完成，但后续 feature / issue / acceptance 阶段启动前用户需要补齐它，或明确接受当前仓库暂时没有项目级硬约束入口。

---

## 启动检查

启动时做下面这些扫描，**先扫再说话**，不要空口问问题：

1. **检查 `codestable/` 目录是否存在**
   - 不存在：空仓库路径候选
   - 存在但不完整：迁移路径（部分补齐）

1.5. **检查旧 `easysdd/` 目录是否存在**（2026 年改名遗留）

   CodeStable 的旧名是 easysdd，2026 年整体改名后项目目录从 `easysdd/` 改成 `codestable/`。发现仓库里有 `easysdd/` 目录（而没有 `codestable/`）时**停下来提示用户迁移**：

   > 检测到旧版 `easysdd/` 目录（CodeStable 前身）。建议直接 `git mv easysdd codestable` 把目录名迁过来，原目录下的文件结构完全一致、frontmatter 字段也完全兼容，rename 后直接可用。要我帮你执行吗？

   用户同意 → 执行 `git mv easysdd codestable`，然后继续按"迁移路径"处理（这时候 `codestable/` 已经存在、内容也完整，只需要补齐可能缺失的共享资产 `tools/` 和 `reference/`）。
   用户想保留旧目录不迁 → 告诉他 CodeStable 子技能只读 `codestable/` 路径，旧 `easysdd/` 下的产物不会被读到；继续按空仓库路径走新骨架。

2. **Glob 全仓库的 `.md` 文件**（排除 `node_modules/`、`.git/`），重点看：
   - 根目录下的 `DESIGN.md`、`ARCHITECTURE.md`、`SPEC.md`、`README.md`
   - `docs/`、`doc/`、`design/`、`spec/`、`wiki/` 等目录下的文件
   - 现有 `codestable/` 下已有哪些文件

3. **检查 `AGENTS.md` 是否存在**（根目录）

4. **汇报扫描结论**——一段话说清楚：
   - 找到了哪些可能和 CodeStable 体系相关的文档（列文件路径）
   - 判断走哪条路径，以及判断依据
   - 有哪些不确定项需要用户确认

---

## 空仓库路径

### 适用条件

- 仓库内没有任何 spec 类文档（或只有 `README.md`）
- `codestable/` 目录不存在

### 执行步骤

**步骤 1：和用户确认范围**

说明即将创建的内容（见上面"标准骨架"），问用户：

- 项目名 / 简介（用于填入 `ARCHITECTURE.md` 占位模板）
- `AGENTS.md` 是否已有，没有的话是否现在就填——想现在填就引导他填关键字段；想之后再填就提醒他 feature/issue 工作流启动时会读它

**步骤 2：创建目录骨架**

按下面顺序执行，每步完成后继续，**不等用户逐步确认**——骨架是整体一次性的，逐步确认反而打断节奏：

- `codestable/requirements/.gitkeep`
- `codestable/architecture/ARCHITECTURE.md`（填入占位模板，见同目录 `reference.md`）
- `codestable/roadmap/.gitkeep`
- `codestable/features/.gitkeep`
- `codestable/issues/.gitkeep`
- `codestable/compound/.gitkeep`
- `codestable/tools/`（用 `cp -rf` / `Copy-Item -Recurse -Force` 整目录拷贝本技能包 `cs-onboard/tools/` 下的所有文件，**不要 Read 再 Write**）
- `codestable/reference/`（同上，整目录拷贝本技能包 `cs-onboard/reference/`——这是所有 CodeStable 子技能在运行时共享参考文档的唯一方式）

> **落盘用 shell 命令整目录覆盖**，不要 `Read` 一个文件再 `Write` 一个文件——这两个目录是机器共享资产，Read+Write 链路容易截断大文件、改缩进、吃空行，还慢还费 token。迁移路径步骤 4 里给了具体命令示例，空仓库路径也照着执行。

**步骤 3：AGENTS.md 提醒**

如果根目录没有 `AGENTS.md`：

> `AGENTS.md` 还不存在。它是 CodeStable 所有子工作流的"项目硬约束入口"——记录代码规范、已知坑、禁止事项。建议现在创建一个最小版本。你想现在填，还是之后自己创建？

用户选"现在填"：提供最小模板（见同目录 `reference.md`），引导用户填写关键字段后保存。
用户选"之后"：记录在汇报里，告诉用户"下次触发 feature/issue 工作流前记得补上"。

**步骤 4：验收汇报**

列出建了哪些文件，告诉用户：

> CodeStable 骨架已就绪。现在可以：
> - 开始一个新功能：触发 `cs-feat` 技能
> - 报告一个问题：触发 `cs-issue` 技能
> - 沉淀知识：触发 `cs-learn` 技能

---

## 迁移路径

### 适用条件

仓库内有零散的 spec 类文档、设计文档、或部分 `codestable/` 结构。

### 执行步骤

**步骤 1：生成审计报告**

把扫描结果整理成一张映射表，展示给用户：

| 现有文件 | 推测内容类型 | 建议归入 CodeStable 位置 | 置信度 |
|---|---|---|---|
| `docs/DESIGN.md` | 项目架构文档 | `codestable/architecture/ARCHITECTURE.md` | 高 |
| `docs/feature-auth.md` | 某功能的设计稿 | `codestable/features/YYYY-MM-DD-auth/auth-design.md` | 中 |
| `SPEC.md` | 功能需求文档？ | 需用户确认 | 低 |
| ... | ... | ... | ... |

**置信度的含义**：

- **高**：文件内容和目标位置语义明确匹配（比如架构文档放架构目录）
- **中**：可以推断但有歧义（比如一份文档把需求、设计和验收混写在一起）
- **低**：文件内容不明确，或映射到多个位置都合理

**步骤 2：逐条和用户对齐**

对每一条置信度"中"或"低"的映射，用 `AskUserQuestion` 问用户确认：

- **中置信度**：给出推断理由，问"是否按这个方式归位？"
- **低置信度**：描述文件内容，给 2-3 个候选位置让用户单选，并提供"跳过（不迁移）"选项

高置信度的映射不需要逐条问，但要在汇报里列出来，让用户有机会反对。理由是高置信度的判断也可能错，但逐条问会让节奏失控——汇报里列出来等于给了用户一次复审机会但不打断流程。

**步骤 3：处理"中途写了一半"的 CodeStable 文档**

如果 `codestable/` 已部分存在：

- 检查已有目录是否符合命名规范（`YYYY-MM-DD-{slug}` 格式）
- 检查已有文件是否有内容（空文件 vs 有内容）
- 不符合规范但有内容的文件：提示用户，问是否重命名
- 空占位文件（`.gitkeep` 或空 `.md`）：直接补齐，不用问用户

**步骤 4：补齐缺失的骨架**

对照上面的标准骨架，把**用户确认迁移方案后仍然缺失**的目录和文件补齐。已有内容的目录不要覆盖，只补空缺。

**`codestable/tools/` 和 `codestable/reference/` 一律用技能包里的新版本覆盖**——不管项目里的旧版本看起来有没有被改过。

- 这两个目录是**技能包维护的共享资产**，权威源头在 `cs-onboard/tools/` 和 `cs-onboard/reference/`，项目里的只是一份落盘副本
- 技能包升级后（比如修了 bug、加了字段、改了脚本），onboarding 再跑一次的目的之一就是把旧副本刷新到新版本，留着旧版本会让后续子技能按过时口径工作
- 覆盖前在汇报里列出被覆盖的文件清单，让用户知道发生了什么；如果用户明确说过"我改过 tools/xxx.py 请保留"，才例外保留并在汇报里标红

这一条是迁移路径里**唯一强制覆盖**的动作，其他所有已有文件（architecture / features / issues / compound / AGENTS.md 等）仍然遵守"不经用户确认不动"的原则。

**落盘方式：直接用 shell 命令整目录覆盖，不要 Read 一遍再 Write。**

正确做法（一条命令批量覆盖）：

```bash
# macOS / Linux
cp -rf <技能包路径>/cs-onboard/tools/.      codestable/tools/
cp -rf <技能包路径>/cs-onboard/reference/.  codestable/reference/

# Windows PowerShell
Copy-Item -Recurse -Force <技能包路径>\cs-onboard\tools\*      CodeStable\tools\
Copy-Item -Recurse -Force <技能包路径>\cs-onboard\reference\*  CodeStable\reference\
```

错误做法（不要这样做）：

- ❌ 用 Read 工具把技能包里的文件读出来，再用 Write 工具粘到项目里——文件稍大就会截断内容、改动缩进、吃掉空行，而且慢、费 token、容易抄错
- ❌ 一个文件一个文件地 `cp`——多一步就多一个出错点
- ❌ 先比 diff 再决定拷不拷——这两个目录的规则就是"无条件覆盖"，比 diff 是白费力

技能包路径一般就是当前 skill 的安装目录（比如 `~/.claude/skills/cs-onboard/` 或插件目录下的对应位置）。不确定就先 `ls` 定位一下，再执行拷贝。拷完跑一次 `ls codestable/tools/ codestable/reference/` 验证文件都在。

**步骤 5：处理不迁移的文件**

用户选择"跳过"的文件：**不移动、不删除、不重命名**，在汇报里标注"保留原位（未纳入 CodeStable 体系）"。绝对不允许未经确认就移动或删除任何已有文件——理由很简单：onboarding 的入口只允许 AI 整理而不允许 AI 替用户做删除决定，删错了恢复成本极高。

**步骤 6：AGENTS.md 提醒**（同空仓库路径步骤 3）

**步骤 7：验收汇报**

列出：

- 迁移的文件清单（from → to）
- 新创建的骨架文件清单
- 未迁移的文件清单（保留原位）
- 下一步建议

---

## 骨架文件模板

`ARCHITECTURE.md` 占位模板和 `AGENTS.md` 最小模板已拆到同目录 `reference.md`。本技能正文只保留流程，不再内嵌长模板。

---

## 退出条件

- [ ] `codestable/` 目录骨架完整（八个子目录都存在：`requirements/`、`architecture/`、`roadmap/`、`features/`、`issues/`、`compound/`、`tools/`、`reference/`）
- [ ] `codestable/tools/` 和 `codestable/reference/` 下的共享脚本和参考文档已从本技能包复制过去（子技能在运行时必须能读到这些文件）
- [ ] `codestable/architecture/ARCHITECTURE.md` 已建（哪怕是占位内容）
- [ ] 迁移路径：每一条映射都有明确处理结果（迁移 / 保留原位）
- [ ] 迁移路径：没有未经用户确认就移动的文件
- [ ] `AGENTS.md` 状态已明确（存在 / 用户知道需要补）
- [ ] 验收汇报已给出，用户知道下一步该触发哪个子技能

---

## 容易踩的坑

- **未经用户确认就移动或删除已有文件**——迁移路径的核心原则是用户拍板，不是 AI 自作主张
- **替用户填写 AGENTS.md 的实质内容**——AGENTS.md 里的规范和禁忌必须项目 owner 来定，AI 只提供模板和引导
- **建完骨架后立刻开始某个 feature/issue**——onboarding 的职责是"搭环境"，不是"开始干活"，做完骨架就结束
- **把 AGENTS.md 建到 `codestable/` 里**——AGENTS.md 是根目录文件，不属于 `codestable/` 下
- **把低置信度的映射也直接执行**——置信度低 = 必须问，不问直接迁是在替用户做判断
- **遇到部分存在的 `codestable/` 结构就全部覆盖重建**——除 `tools/` 和 `reference/` 外，有内容的文件不允许覆盖，只补空缺
- **对 `codestable/tools/` 和 `codestable/reference/` 也走"不覆盖"保守策略**——正好相反，这两个目录必须用技能包里的新版本覆盖旧版本，否则技能升级后用户项目会停留在过时脚本和过时口径上
- **用 Read + Write 手工"搬运"文件内容**——必须用 `cp -rf` / `Copy-Item -Recurse -Force` 整目录覆盖。Read+Write 会截断长文件、吃掉空行、改缩进，而且一个个搬容易漏、容易慢、容易费 token
- **Glob 时忘记排除 `node_modules/`、`.git/`**——这会让扫描结果充斥噪声，判断路径会出错

---

## 相关文档

- `codestable/reference/system-overview.md` — CodeStable 体系总览和场景路由(由 onboarding 从技能包 reference/ 一次性复制到项目)
- `codestable/reference/shared-conventions.md` — onboarding 落盘后，目录结构和共享口径的权威版本在这里
- `AGENTS.md` — 全项目硬约束入口，onboarding 完成后所有子工作流都会读它
- `codestable/architecture/ARCHITECTURE.md` — onboarding 产出的架构总入口骨架，方案设计阶段会读它
