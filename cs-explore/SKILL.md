---
name: cs-explore
description: 对仓库做定向代码探索并把"提问→读代码→得结论"沉淀为可检索证据，三种类型 question / module-overview / spike。触发：用户说"先 explore 一下"、"这个仓库里 X 怎么实现"、"快速熟悉这个模块"、"把探索结果存档"。
---

# cs-explore

同一个问题第一次花两小时查代码，第二次应该五分钟内找到答案——前提是第一次做完留下证据化的记录。cs-explore 把"提问 → 读代码 → 得结论"沉淀成可检索的探索文档。

---

## 适用场景

- 新人入仓快速理解模块边界 / 调用链 / 入口
- 用户提具体问题但暂时不要求直接产出方案 / 修复
- feature-design / issue-analyze / issue-fix 前先补一轮证据化探索
- 技术方向还在讨论，需要轻量 spike（只探索不拍板）

本技能只负责"看到了什么"的证据化记录。用户意图是别的（拍板 / 处方 / 修 bug）让用户按场景选对应子技能。

> 共享路径与命名约定看 `codestable/reference/shared-conventions.md`。产物写入 `codestable/compound/`，命名 `YYYY-MM-DD-explore-{slug}.md`，frontmatter 带 `doc_type: explore`。

---

## 三种探索类型

frontmatter 的 `type` 字段：

| 类型 | 适用情境 |
|---|---|
| `question` | 围绕一个具体问题查代码并给结论 |
| `module-overview` | 快速梳理某模块结构 / 边界 / 入口 / 依赖 |
| `spike` | 对多个可能方向做轻量技术探查（不做最终决策） |

---

## 文档格式

frontmatter / 正文结构 / 各节写法说明和示例见同目录 `reference.md`。流程约束：

- **速答必须先于证据出现**——读者打开先看到结论再决定要不要往下看证据
- 结论必须可回溯到证据，不允许纯猜测
- 证据不足时 `confidence` 必须降为 `medium` 或 `low`
- 旧探索过期：旧文档标 `outdated`，新增当前版本

---

## 工作流阶段

### Phase 1：收敛探索问题

最多两个问题：

1. "你最想先回答的一个问题是什么？"
2. "希望聚焦哪个模块 / 目录？"

用户描述已清楚直接进 Phase 1.5。

### Phase 1.5：查重叠与意图分流（必做）

按 `shared-conventions.md` §6 第 5/6 条执行：

- 含"更新 / 复查 / 某次 explore / 这个模块之前探过"或指向某份旧 explore → 走**更新或 supersede**。explore 特性：**代码已变导致旧结论失效**时旧文档 `status: outdated` + 新建一份（supersede）；只补证据 / 收紧结论但核心结论未变时走"更新已有"
- 否则用搜索工具按关键词 / 模块查一遍，命中相近旧 explore 时先读它，能直接回答就告诉用户"已有一份在 {路径}，复用还是重探一遍？"

**更新路径**：读旧文档 → 按 Phase 2 补证据 → 改写速答节 → 写回原文件 + `updated: YYYY-MM-DD`。

### Phase 2：证据化探索

- 用 Glob / Grep / Read **真实读代码**不靠猜
- 边读边积累证据；**同步思考每条证据支撑哪个结论**——不支撑任何结论的证据不记录
- 关键证据 3-8 条，每条都标注 `文件:行号`
- 多模块协作或 `module-overview` / `spike` 类型 → 准备一张 Mermaid 图放在速答节里
- 形成初步结论后主动检查：已有证据能否说服持怀疑态度的人？够了就停不必扩大搜索

为什么"够了就停"：探索不是穷举，是建立到"读者能信"为止的证据链。继续扩大只会让文档变长而不变可信。

### Phase 3：起草与确认

- **先写速答节，再回填关键证据**——这个顺序很重要：先有结论再回头看证据是否真支持，能逼你检查每条证据的实际效力
- AI 一次性起草完整文档，用户 review 后确认
- 有修改按反馈修订后再落盘

### Phase 4：归档

- 新建：写入 `codestable/compound/YYYY-MM-DD-explore-{slug}.md`，frontmatter 带 `doc_type: explore`
- 更新：写回 Phase 1.5 定位的原文件 + `updated: YYYY-MM-DD`
- supersede：按 `shared-conventions.md` §6 第 5 条；旧文档 `status: outdated` + `superseded-by`

### Phase 5：给出下一步建议

证据收齐后一句话提示下一步方向（"要不要基于这份 explore 去设计方案"）。用户说"不用"就跳过——下一步由用户自己决定。

---

## 搜索工具

> 完整语法见 `codestable/reference/tools.md`。

```bash
# 按类型筛选
python codestable/tools/search-yaml.py --dir codestable/compound --filter doc_type=explore --filter type=module-overview --filter status=active

# 归档后查重叠
python codestable/tools/search-yaml.py --dir codestable/compound --filter doc_type=explore --query "{关键词}" --json
```

---

## 退出条件

- [ ] 已明确探索问题与范围
- [ ] 速答节给出核心结论（结论前置）
- [ ] 关键证据 3-8 条，每条标 file:line 并说明支撑哪个结论
- [ ] 多模块或 module-overview / spike 类型时速答节有 Mermaid 图
- [ ] 文档已归档到 `compound/`
- [ ] 已给出后续建议

---

## 守护规则

> 归档类共享规则见 `shared-conventions.md` 第 6 节。本技能特有反模式：

- 不读代码直接给结论
- 证据只写"看起来像"不写 file:line
- 结论写在证据之后——速答节必须在关键证据节之前
- 证据节比速答节长数倍——精简证据，不支撑结论的删掉
- 跨模块流程没 Mermaid 图，只靠文字描述
- 提前拍板——explore 只记"看到了什么"不下"以后应该怎么做"
- 直接给处方没证据链——每条结论必须回溯到 file:line
- 历史 explore 已过期却继续引用，不做 `status` 标注
- 读写非 `doc_type=explore` 的文档——本技能只负责 explore
