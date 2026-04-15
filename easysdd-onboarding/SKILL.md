---
name: easysdd-onboarding
description: 将新仓库或有零散文档的仓库接入 easysdd 目录体系。触发场景："在这个项目里用 easysdd"、"搭 easysdd 结构"、"初始化 easysdd"、"迁移到 easysdd"。绿地路径（从零建骨架）或迁移路径（审计已有文档后归位），由用户逐一确认后落盘。
---

# easysdd-onboarding

本技能负责把一个仓库**接入 easysdd 工作流体系**——无论它是一张白纸，还是一个已经有零散文档的仓库。

本技能只做两件事：**搭骨架**、**归旧档**。骨架搭好之后，各子工作流（feature / issue / compound）即可直接在其上运行，不需要再解释目录在哪里。

---

## 一、两条路径

| 路径 | 适用情况 | 产出 |
|---|---|---|
| **绿地路径** | 仓库内无任何 spec 类文档，也没有 `easysdd/` 目录 | 完整的 `easysdd/` 目录骨架 + 必要的骨架文件 |
| **迁移路径** | 仓库内已有零散文档、`docs/` 目录、架构文档、设计稿，或部分 `easysdd/` 结构 | 审计报告 + 迁移映射方案（用户逐一确认）+ 落盘 |

**判断路径**：启动后先做一次扫描，根据结果自动判断——不要让用户自己选。如果扫描结果模糊（比如只有一个 README），明说判断依据并问用户确认。

---

## 二、涉及的路径

> 共享路径与命名约定以根技能 `easysdd` 第二节为准。本节只列 onboarding 需要创建或检查的骨架文件。

### 标准骨架（目标状态）

onboarding 完成后，仓库里应存在以下骨架：

```
easysdd/
├── architecture/
│   └── DESIGN.md               ← 架构总入口骨架（首次创建时为占位模板）
├── features/                   ← feature 聚合根（空目录，.gitkeep）
├── issues/                     ← issue 聚合根（空目录，.gitkeep）
├── learnings/                  ← 知识沉淀目录（空目录，.gitkeep）
├── decisions/                  ← 决策归档目录（空目录，.gitkeep）
├── tricks/                     ← 技巧库目录（空目录，.gitkeep）
├── explores/                   ← 探索归档目录（空目录，.gitkeep）
├── tools/                      ← 跨工作流共享的脚本工具（由 onboarding 从技能包释放）
│   ├── search-yaml.py          ← 通用 YAML frontmatter 搜索工具
│   └── validate-yaml.py        ← YAML 语法校验工具
└── reference/                  ← 共享参考文档目录（由 onboarding 创建空目录或 .gitkeep）
```

> `AGENTS.md` 在项目根目录，不在 `easysdd/` 里。onboarding 会检查它是否存在，不存在时提醒用户，但**不代替用户写它**——AGENTS.md 的内容高度项目相关，必须由人来填。缺少 `AGENTS.md` 不阻塞 onboarding 完成，但后续 feature / issue / acceptance 阶段启动前，用户需要补齐它，或明确接受当前仓库暂时没有项目级硬约束入口。

---

## 三、启动检查

启动时做以下扫描，**先扫再说话**，不要空口问问题：

1. **检查 `easysdd/` 目录是否存在**
   - 不存在：绿地路径候选
   - 存在但不完整：迁移路径（部分补齐）

2. **Glob 全仓库的 `.md` 文件**（排除 `node_modules/`、`.git/`），重点看：
   - 根目录下的 `DESIGN.md`、`ARCHITECTURE.md`、`SPEC.md`、`README.md`
   - `docs/`、`doc/`、`design/`、`spec/`、`wiki/` 等目录下的文件
   - 现有 `easysdd/` 下已有哪些文件

3. **检查 `AGENTS.md` 是否存在**（根目录）

4. **汇报扫描结论**，一段话说清楚：
   - 找到了哪些可能和 easysdd 体系相关的文档（列文件路径）
   - 判断走哪条路径，以及判断依据
   - 有哪些不确定项需要用户确认

---

## 四、绿地路径

### 适用条件

- 仓库内没有任何 spec 类文档（或只有 `README.md`）
- `easysdd/` 目录不存在

### 执行步骤

**步骤 1：和用户确认范围**

说明即将创建的内容（见第二节骨架），问用户：

- 项目名 / 简介（用于填入 `DESIGN.md` 占位模板）
- `AGENTS.md` 是否已有，没有的话是否现在就填（如果用户想现在填，引导他填关键字段；如果想之后再填，提醒他 feature/issue 工作流启动时会读它）

**步骤 2：创建目录骨架**

创建以下内容（顺序执行，每步完成后继续，不等用户逐步确认——骨架是整体一次性的）：

- `easysdd/architecture/DESIGN.md`（填入占位模板，见同目录 `reference.md`）
- `easysdd/features/.gitkeep`
- `easysdd/issues/.gitkeep`
- `easysdd/learnings/.gitkeep`
- `easysdd/decisions/.gitkeep`
- `easysdd/tricks/.gitkeep`
- `easysdd/explores/.gitkeep`
- `easysdd/tools/`（将本技能包 `easysdd-onboarding/tools/` 下的所有文件原样复制过去，不修改内容）
- `easysdd/reference/.gitkeep`

**步骤 3：AGENTS.md 提醒**

如果根目录没有 `AGENTS.md`：

> `AGENTS.md` 还不存在。它是 easysdd 所有子工作流的"项目硬约束入口"——记录代码规范、已知坑、禁止事项。建议现在创建一个最小版本。你想现在填，还是之后自己创建？

用户选"现在填"：提供最小模板（见同目录 `reference.md`），引导用户填写关键字段后保存。  
用户选"之后"：记录在汇报里，告诉用户"下次触发 feature/issue 工作流前记得补上"。

**步骤 4：验收汇报**

列出创建了哪些文件，告诉用户：

> easysdd 骨架已就绪。现在可以：
> - 开始一个新功能：触发 `easysdd-feature` 技能
> - 报告一个问题：触发 `easysdd-issue` 技能
> - 沉淀知识：触发 `easysdd-compound` 技能

---

## 五、迁移路径

### 适用条件

- 仓库内有零散的 spec 类文档、设计文档、或部分 `easysdd/` 结构

### 执行步骤

**步骤 1：生成审计报告**

把扫描结果整理成一张映射表，展示给用户：

| 现有文件 | 推测内容类型 | 建议归入 easysdd 位置 | 置信度 |
|---|---|---|---|
| `docs/DESIGN.md` | 项目架构文档 | `easysdd/architecture/DESIGN.md` | 高 |
| `docs/feature-auth.md` | 某功能的设计稿 | `easysdd/features/YYYY-MM-DD-auth/design.md` | 中 |
| `SPEC.md` | 功能需求文档？ | 需用户确认 | 低 |
| ... | ... | ... | ... |

**置信度说明**：
- **高**：文件内容和目标位置语义明确匹配（比如架构文档放架构目录）
- **中**：可以推断但有歧义（比如一份文档把需求、设计和验收混写在一起）
- **低**：文件内容不明确，或映射到多个位置都合理

**步骤 2：逐条和用户对齐**

对每一条置信度"中"或"低"的映射，用 `AskUserQuestion` 问用户确认：

- **中置信度**：给出推断理由，问"是否按这个方式归位？"
- **低置信度**：描述文件内容，给 2-3 个候选位置让用户单选，并提供"跳过（不迁移）"选项

> 高置信度的映射不需要逐条问，但要在汇报里列出来，让用户有机会反对。

**步骤 3：处理"中途写了一半"的 easysdd 文档**

如果 `easysdd/` 已部分存在：

- 检查已有目录是否符合命名规范（`YYYY-MM-DD-{slug}` 格式）
- 检查已有文件是否有内容（空文件 vs 有内容）
- 不符合规范但有内容的文件：提示用户，问是否重命名
- 空占位文件（`.gitkeep` 或空 `.md`）：直接补齐，不问用户

**步骤 4：补齐缺失的骨架**

对照第二节的标准骨架，把**用户确认迁移方案后仍然缺失**的目录和文件补齐。已有内容的目录不要覆盖，只补空缺。

`easysdd/tools/` 下缺失的工具文件，从本技能包的 `easysdd-onboarding/tools/` 对应补齐；已存在的文件不覆盖（用户可能已经改过）。

**步骤 5：处理不迁移的文件**

用户选择"跳过"的文件：**不移动、不删除、不重命名**，在汇报里标注"保留原位（未纳入 easysdd 体系）"。绝对不允许未经确认就移动或删除任何已有文件。

**步骤 6：AGENTS.md 提醒**（同绿地路径步骤 3）

**步骤 7：验收汇报**

列出：
- 迁移的文件清单（from → to）
- 新创建的骨架文件清单
- 未迁移的文件清单（保留原位）
- 下一步建议

---

## 六、骨架文件模板

`DESIGN.md` 占位模板和 `AGENTS.md` 最小模板已拆到同目录 `reference.md`。本技能正文只保留流程，不再内嵌长模板。

---

## 七、退出条件

- [ ] `easysdd/` 目录骨架完整（九个子目录都存在：`architecture/`、`features/`、`issues/`、`learnings/`、`decisions/`、`tricks/`、`explores/`、`tools/`、`reference/`）
- [ ] `easysdd/architecture/DESIGN.md` 已创建（哪怕是占位内容）
- [ ] 迁移路径：每一条映射都有明确处理结果（迁移 / 保留原位）
- [ ] 迁移路径：没有未经用户确认就移动的文件
- [ ] `AGENTS.md` 状态已明确（存在 / 用户知道需要补）
- [ ] 验收汇报已给出，用户知道下一步该触发哪个子技能

---

## 八、反模式（看到就停）

- ❌ **未经用户确认就移动或删除已有文件**：迁移路径的核心原则是用户拍板，不是 AI 自作主张
- ❌ **替用户填写 AGENTS.md 的实质内容**：AGENTS.md 里的规范和禁忌必须项目 owner 来定，AI 只提供模板和引导
- ❌ **创建骨架后立刻开始某个 feature/issue**：onboarding 的职责是"搭环境"，不是"开始干活"，做完骨架就结束
- ❌ **把 AGENTS.md 创建到 `easysdd/` 里**：AGENTS.md 是根目录文件，不属于 `easysdd/` 下
- ❌ **把低置信度的映射也直接执行**：置信度低 = 必须问，不问直接迁是在替用户做判断
- ❌ **遇到部分存在的 `easysdd/` 结构就全部覆盖重建**：有内容的文件不允许覆盖，只补空缺
- ❌ **Glob 时忘记排除 `node_modules/`、`.git/`**：这会让扫描结果充斥噪声，判断路径会出错

---

## 九、相关文档

- `easysdd/SKILL.md` — easysdd 家族根技能，目录结构的权威定义在那里（第二节）
- `AGENTS.md` — 全项目硬约束入口，onboarding 完成后所有子工作流都会读它
- `easysdd/architecture/DESIGN.md` — onboarding 产出的架构总入口骨架，方案设计阶段会读它
