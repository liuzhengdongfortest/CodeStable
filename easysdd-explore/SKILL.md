---
name: easysdd-explore
description: 探索归档子工作流——对仓库做定向代码探索并把结果归档，供后续 design/analyze/fix 复用。触发场景："先 explore 一下"、"这个仓库里 X 怎么实现"、"快速熟悉这个模块"、"把探索结果存档"。
---

# easysdd-explore

**探索归档子工作流** —— 把一次"提问 -> 读代码 -> 得结论"的过程沉淀为可检索证据，减少重复探索。

> "同一个问题第一次花 2 小时查代码，第二次应该 5 分钟内找到答案。"

---

## 一、适用场景

- 新人入仓，需要快速理解模块边界、调用链、入口文件
- 用户提出一个具体问题，但暂时不要求直接产出方案/修复
- feature-design / issue-analyze / issue-fix 前，先补一轮证据化探索
- 技术方向还在讨论，需要先做轻量 spike（只探索，不拍板）

不适用场景：

- 已经是明确的拍板动作（该用 `easysdd-decisions`）
- 已经是可复用处方总结（该用 `easysdd-tricks`）
- 已经在做 BUG 修复并且根因明确（直接走 `easysdd-issue-fix`）

---

## 二、涉及的路径

本技能在正文里用自然语言术语引用路径（**探索归档目录**），具体目录位置见主技能 `easysdd` 第二节"目录安排"。

**文件命名**：`YYYY-MM-DD-{slug}.md`（日期取归档当天，slug 为英文小写 + 连字符）。

---

## 三、三种探索文档类型

每条探索文档归属以下三类之一，在 YAML frontmatter 的 `type` 字段标注：

| 类型 | 适用情境 | 产出 |
|---|---|---|
| `question` | 围绕一个问题查代码并给结论 | `explores/YYYY-MM-DD-{slug}.md` |
| `module-overview` | 快速梳理某模块结构、边界、入口与依赖 | `explores/YYYY-MM-DD-{slug}.md` |
| `spike` | 对多个可能方向做轻量技术探查（不做最终决策） | `explores/YYYY-MM-DD-{slug}.md` |

---

## 四、文档格式

### YAML frontmatter

```yaml
---
type: question | module-overview | spike
date: YYYY-MM-DD
slug: {英文描述，连字符分隔}
topic: {一句话描述探索问题}
scope: {探索范围，如 auth module / cache pipeline / api layer}
keywords: []
status: active | outdated
confidence: high | medium | low
---
```

### 正文结构

```markdown
## 问题与范围

这次探索想回答什么问题，明确看哪些范围，不看哪些范围。

## 证据

| 位置 | 证据说明 |
|---|---|
| `{文件}:{行号}` | 这里看到的事实 |
| `{文件}:{行号}` | ... |

## 结论

基于证据得到的结论。若有多个结论，按 1/2/3 列出。

## 未决问题

还不确定的点、需要用户补充的信息或需要运行时验证的点。

## 后续建议

下一步建议走哪个工作流（feature-design / issue-analyze / issue-fix / decisions / tricks）。

## 相关文档

可选。关联的 features/issues/decisions/tricks/learnings/explores。
```

规则：

- 结论必须可回溯到证据，不允许"纯猜测结论"
- 如果证据不足，`confidence` 必须是 `medium` 或 `low`
- 当代码变更导致旧探索不再成立时，将旧文档 `status` 标为 `outdated`，并新增一条当前版本的探索文档

---

## 五、工作流阶段

### Phase 1：收敛探索问题

最多问用户两个问题：

1. "你最想先回答的一个问题是什么？"
2. "希望聚焦哪个模块/目录？"

如果用户描述已清楚，直接进入 Phase 2。

### Phase 2：证据化探索

- 用 Glob/Grep/Read 真实读代码，不靠猜
- 记录关键证据（文件 + 行号 + 事实）
- 给出结论时标注置信度（`high`/`medium`/`low`）

### Phase 3：草稿确认

- AI 一次性起草完整 explore 文档
- 用户 review 后确认
- 有修改则按反馈修订后再落盘

### Phase 4：归档

- 写入探索归档目录，命名 `YYYY-MM-DD-{slug}.md`
- 归档后用搜索工具查有无语义重叠的历史探索
- 若存在冲突或过期记录，提示用户将旧文档标为 `outdated`

### Phase 5：向后续工作流回传

根据探索结论建议下一步：

- 需求清晰但未落方案 -> `easysdd-feature-design`
- 需求已有方案 -> `easysdd-feature-implement`
- 问题已成型但根因未明 -> `easysdd-issue-analyze`
- 根因明确且用户确认 -> `easysdd-issue-fix`
- 形成长期规范拍板 -> `easysdd-decisions`
- 沉淀通用做法 -> `easysdd-tricks`

---

## 六、搜索工具

`tools/search-yaml.py` 是通用 YAML frontmatter 搜索工具（路径见主技能 `easysdd` 第二节）。

```bash
# 全文检索 explore
python tools/search-yaml.py --dir easysdd/explores --query "auth flow"

# 按类型
python tools/search-yaml.py --dir easysdd/explores --filter type=module-overview

# 只看当前有效探索记录
python tools/search-yaml.py --dir easysdd/explores --filter status=active

# 按关键词
python tools/search-yaml.py --dir easysdd/explores --filter keywords~=cache

# JSON 输出（给 AI 解析）
python tools/search-yaml.py --dir easysdd/explores --query "retry" --json
```

---

## 七、与其他工作流的关系

- `easysdd-feature-design` 开始前：先搜索 explores，复用调用链与模块边界证据
- `easysdd-issue-analyze` 开始前：先搜索 explores，减少重复定位
- `easysdd-issue-fix` 开始前：搜索 explores，确认修复点与历史证据一致
- `easysdd-explore` vs `easysdd-tricks`：explore 记录"看到了什么"，tricks 记录"推荐怎么做"
- `easysdd-explore` vs `easysdd-decisions`：explore 是输入，decisions 是拍板

---

## 八、退出条件

- [ ] 已明确探索问题与范围
- [ ] 证据节包含可回溯的文件:行号
- [ ] 结论与证据一致，并给出置信度
- [ ] 文档已归档到探索归档目录
- [ ] 已给出下一步建议（路由到哪个子工作流）

---

## 九、反模式（看到就停）

- ❌ 不读代码直接给结论
- ❌ 证据只写"看起来像"，不写文件:行号
- ❌ 把 explore 文档写成 decisions（提前拍板）
- ❌ 把 explore 文档写成 tricks（直接给处方但没有证据链）
- ❌ 历史 explore 已过期却继续引用，不做 `status` 标注
