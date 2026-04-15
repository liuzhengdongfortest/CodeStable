---
name: easysdd-libdoc
description: 库 API 参考文档子工作流——为库的公开表面（组件、函数、命令等）逐条目生成参考文档，支持清单追踪和批量生成。触发场景："写 API 文档"、"组件文档"、"libdoc"、"参考文档"、"给每个组件写份文档"、"函数参考"、"接口文档"，或 feature-acceptance 结束后发现新增了库公开接口。
---

# easysdd-libdoc

**库 API 参考文档子工作流** —— 为库的**公开表面**逐条目生成结构化参考文档，带清单追踪，支持单条目和批量两种模式。

> "guidedoc 教你怎么用，libdoc 告诉你每个零件长什么样。"

---

## 一、定位与边界

### 和 guidedoc 的关系

| | guidedoc | libdoc |
|---|---|---|
| 性质 | 任务导向（Tutorial / How-to） | 参考导向（Reference） |
| 回答的问题 | "如何用 X 实现某个目标" | "X 的每个零件长什么样、怎么配" |
| 粒度 | 一个 feature / 一个场景一篇 | 一个条目（组件/函数/命令）一篇 |
| 信息来源 | 方案 doc + 用户知识 | **源码本身**（类型定义、注释、默认值） |
| 数量级 | 几篇到十几篇 | 几十到上百篇 |

两者互补：guide 内引用 libdoc 条目做详细参考（"完整 props 见 xxx"），libdoc 条目的"相关条目"可链接到对应 guide。

### 什么是"条目（entry）"

**条目**是 libdoc 的原子文档单位。具体含义由项目类型决定：

| 项目类型 | 条目粒度 |
|---|---|
| UI 组件库 | 一个组件 = 一个条目 |
| 工具函数库 | 一个模块或函数族 = 一个条目 |
| API Client | 一个 endpoint 族 = 一个条目 |
| CLI 工具 | 一个子命令 = 一个条目 |

用户在初始化阶段确认条目粒度，后续保持一致。

---

## 二、涉及的路径

本技能的产物**不在 `easysdd/` 目录下**——API 参考文档是面向外部读者的可发布产物，不是 spec 工件。

- 条目文档 → `docs/api/{slug}.md`
- 条目清单 → `docs/api/_manifest.yaml`

**路径 `docs/api/` 是默认约定**，如果项目已有其他 API 文档目录约定（`reference/`、`components/`），以项目约定为准——开始工作前先确认。

---

## 三、manifest / 模板 / 源码提取

以下参考材料已拆到 `easysdd-libdoc/reference.md`：

- `_manifest.yaml` 的完整格式与 status 语义
- 条目文档的 YAML frontmatter 和正文模板
- 源码提取清单（接口签名、默认值、导出方式等）

本技能只保留流程约束：libdoc 以源码为事实源，不靠猜，不复制上一个条目改名。

---

## 四、工作流步骤

### Phase 1：初始化 — 扫描与清单

**目标**：产出条目清单，锁定文档范围。

1. **确认项目类型和条目粒度**
   - 询问（或从上下文推断）：这是什么类型的库？条目粒度是什么？
   - 确认输出路径（`docs/api/` 或项目已有约定）

2. **扫描源码目录**
   - 读取 `source_root` 下的文件结构
   - 识别所有公开导出的条目（组件、函数、命令等）
   - 按逻辑分组归类（category）

3. **生成 `_manifest.yaml`**
   - 所有条目初始 status 为 `pending`
   - 落盘后用 `validate-yaml.py --file docs/api/_manifest.yaml --yaml-only` 校验语法
   - 展示清单给用户 review

4. **用户确认范围**
   - 用户可标记某些条目为 `skipped`（内部实现、不需要文档）
   - 用户可调整分类、合并或拆分条目
   - 确认后清单落盘

### Phase 2：生成 — 单条目 or 批量

两种模式，用户选择：

#### 模式 A：单条目模式

适用于：只处理 1-3 个条目，或首次试跑确认质量。

1. 选定条目 → 读取 source_files → 按模板生成文档 → 展示给用户 review → 用户确认后落盘
2. 落盘后用 `validate-yaml.py --file {条目文档路径} --require doc_type --require entry --require status` 校验 frontmatter 语法和必填字段
3. 更新 `_manifest.yaml` 中对应条目 status 为 `current`

#### 模式 B：批量模式

适用于：清单中有大量 `pending` 条目需要处理。

1. **先出样板**：从清单中选 2-3 个有代表性的条目（不同 category），按单条目模式生成
2. **用户确认质量标准**：review 这 2-3 篇样板，确认模板、详略度、风格符合预期
3. **批量生成**：对剩余 `pending` 条目，逐条走"读源码 → 提取 → 生成"流程
   - 可使用 subagent 并行加速，每个 subagent 处理一个条目
   - 每个条目生成后 status 先标为 `draft`
4. **整体 review**：批量完成后，展示生成概况（条目数、跳过数、待确认数），用户做整体 review
   - 整体 review 前，先用 `validate-yaml.py --dir docs/api --require doc_type --require entry --require status` 批量校验所有生成文件的 frontmatter，有报错先修再 review
5. **确认落定**：用户确认后，批量将 status 从 `draft` 改为 `current`

**批量模式约束**：

- 即使批量生成，每个条目仍然独立读源码、独立生成——不允许复制上一个条目的内容然后改名
- 样板确认步骤不可跳过——先出 2-3 篇让用户看满意了再铺开
- 生成过程中发现某条目源码结构特殊（如动态导出、代码生成），暂时标为 `skipped` 并记 note，不要硬猜

### Phase 3：增量更新

适用于：代码变更后需要同步文档。

1. 用 `search-yaml.py` 搜 `docs/api/` 下 `status=outdated` 的条目，或手动对比 `_manifest.yaml`
2. 对 outdated 条目：重新读源码 → 对比已有文档 → 增量更新变化部分
3. 更新后用 `validate-yaml.py --file {条目文档路径}` 校验，确认 frontmatter 未被破坏
4. 更新后 status 改为 `current`，`last_reviewed` 填当天日期

---

## 五、与其他工作流的关系

| 来源工作流 | 关系说明 |
|---|---|
| `easysdd-feature-acceptance` | 验收结束后若新增/修改了库公开接口 → 推送"需要更新 libdoc 吗？" |
| `easysdd-guidedoc` | guide 内引用 libdoc 条目做详细参考；libdoc 条目的"相关条目"可链接到对应 guide |
| `easysdd-architecture-check` | 接口变更但 libdoc 未同步 → 标记对应条目 `status=outdated` |
| `easysdd-feature-design` | 方案 doc 第 2 节（接口契约）可作为 libdoc 条目的补充信息来源（但以源码为准） |
| `easysdd-tricks` | libdoc "注意事项"与 tricks 目录已有记录重合时，可交叉引用而不重复写 |

---

## 六、退出条件

### Phase 1 退出条件

- [ ] `_manifest.yaml` 已生成并落盘
- [ ] 用户已确认条目范围（包括 skipped 条目的理由）
- [ ] 条目粒度和输出路径已确认

### Phase 2 退出条件（单条目）

- [ ] 条目文档已按模板生成，包含完整 YAML frontmatter
- [ ] API 参考节信息来源于源码提取（非编造）
- [ ] 用户已 review 并确认
- [ ] `_manifest.yaml` 中对应条目 status 已更新

### Phase 2 退出条件（批量）

- [ ] 样板条目（2-3 篇）已获用户确认
- [ ] 所有 pending 条目已生成或标记 skipped
- [ ] 用户已做整体 review
- [ ] `_manifest.yaml` 所有条目 status 已同步

### Phase 3 退出条件

- [ ] outdated 条目已全部更新或确认不需更新
- [ ] `_manifest.yaml` 无残留 outdated 条目（除非用户明确暂缓）

---

## 七、反模式（看到就停）

- ❌ 没扫清单就直接写文档 —— 可能遗漏条目或重复写
- ❌ 没读源码就写 API 参考 —— libdoc 的核心价值是准确反映源码，不是编故事
- ❌ 复制上一个条目文档改改名字就算下一个 —— 每个条目必须独立读源码生成
- ❌ 批量模式跳过样板确认步骤 —— 50 篇全白写因为用户想要的风格不一样
- ❌ 把 spec 信息（不变量、测试约束）写进 libdoc —— 那属于 `easysdd/` 目录
- ❌ libdoc 和 guidedoc 内容高度重叠 —— libdoc 是零件参考，guidedoc 是使用教程，重叠说明其中一份定位有误
- ❌ `_manifest.yaml` 里直接删除行 —— 改 status 为 `skipped` 并写 note
- ❌ 源码接口不存在却在文档里写了 —— 以源码为事实源，不编造
