# cs-arch 参考模板

SKILL.md 只保留流程骨架，具体格式 / 覆盖项 / 报告模板都在这里。

---

## 1. 架构文档结构（backfill / update 产出）

### 1.1 frontmatter

```yaml
---
doc_type: architecture
slug: {英文连字符；和文件名一致}
scope: {一句话覆盖范围}
summary: {一句话总结要点}
status: current | draft | outdated
last_reviewed: YYYY-MM-DD
tags: []
depends_on: []   # 其他 architecture doc 的 slug，可选
implements: []   # 承载的 requirement slug 列表，可空——纯基础设施 / 工具层没有对应 req 是正常的
---
```

### 1.2 正文节

```markdown
## 0. 术语

首次引入的专有名词简要定义 + 和相近名词的区分（"本文里 X 指 Y，和代码里的 X' 不是同一个东西"）。没有新术语就省略。

## 1. 定位与受众

- 项目里哪一块（模块 / 子系统 / 跨模块关注点）
- 谁会读（feature-design / issue-analyze / 新人上手）
- 读完能干嘛（定位代码 / 了解对外接口 / 知道约束）

## 2. 结构与交互

- 模块怎么划分、依赖方向
- 对外接口、对内接口
- 跨模块契约（数据格式 / 调用协议 / 状态归属）
- 模块 ≤ 2 或关系线性时不画图；否则建议 Mermaid

每条结构化断言后附 `file:line` 锚点，或在节末"代码锚点"小节集中给。

## 3. 数据与状态

- 关键类型 / 核心数据结构（简述 + 定义位置 file:line）
- 所有权归属（谁写谁读）
- 持久化边界（内存 / 本地 / 数据库 / 外部服务）

## 4. 关键决策

不是决策全文，是**引用**——每条一两行：结论一句话 + 引用（`compound/YYYY-MM-DD-decision-{slug}.md` 或用户原话出处）+ 为什么引用到这份 doc 里。

没有已落档的决策就省略，或记 `TODO: 某决定应沉淀为 decision`。

## 5. 代码锚点

"想看代码从哪看"清单：入口文件 / 关键函数 / 关键类型定义。格式：`{file}:{function/class} — 一行说明`。

## 6. 已知约束 / 边界情况

本模块"不能动 / 动了要小心"的硬约束 + 来源（AGENTS.md / decision / learning 等）。

## 7. 相关文档

依赖的其他 architecture doc / 承载的 requirement / 相关 decision / learning / trick / explore / 使用本模块的代表性 feature design。

## 变更日志（update 模式才有）

- YYYY-MM-DD：{一句话描述}
```

---

## 2. backfill / update 自查清单

每条针对一种 AI 默认会犯的错：

1. **每个结构化断言能不能锚到代码？**——锚不到的删掉或标 `TODO: 待确认`
2. **有没有替用户拍板？**——"关键决策"节是引用已有 decision / 用户原话，还是 AI 编的选型理由？后者一律不许进
3. **有没有变成代码复述？**——每节至少一句"为什么这么分"，没有这句的节基本就是 `ls` 贴文字
4. **术语冲突检查做了吗？**——新引入的架构术语 grep（代码、`architecture/` 下所有文档、`compound/`）。冲突就换名或在第 0 节明确区分
5. **是否和现有 architecture / decision 冲突？**——发现冲突不许"写自己那版"，要么引用要么停下来问用户
6. **单节长度**——超过 1 屏就该砍或拆
7. **update 专项**：本次新加 / 改动的段落都有代码变化作为依据？凭空"加听起来更完整的描述"是飘离实际的开端

---

## 3. check 模式覆盖项

三个子目标各覆盖 6 类。

### 3.1 design-internal（一份 design 内部一致性）

1. **术语一致性**——第 0 节定义的术语后面有没有被同义词替换或语义漂移
2. **需求对齐**——第 1 节摘要自洽，没偏离已确认目标
3. **契约闭环**——第 2 节契约示例在第 3 节有对应改动计划
4. **示例与决策一致**——契约示例行为是否与关键决策矛盾
5. **范围守护**——改动计划没超出"明确不做"
6. **推进可执行性**——推进步骤能验证、依赖前后无矛盾

### 3.2 design-vs-code（design 与代码对得上）

1. **类型一致性**——design 定义的核心类型 / 字段，代码里存在且语义一致
2. **行为一致性**——design 声明的输入→输出对得上代码实际行为
3. **写路径一致性**——design 声明的写入口，代码没有额外旁路写入
4. **边界行为一致性**——design 的异常 / 边界规则代码有实现
5. **改动边界一致性**——代码没越界或漏实现
6. **推进结果一致性**——每步退出信号对应代码状态可验证

### 3.3 architecture-folder-internal（多份文档间一致性）

1. **术语一致性**——同概念称呼统一，无同义词漂移或同名异义
2. **模块边界一致性**——A 说某职责归模块 X，B 是不是也这么说；有没有两份都声称拥有同一块职责
3. **跨文引用有效性**——`see xxx.md` / `定义见 yyy.md` 引用的目标真的存在
4. **接口 / 契约对齐**——多份涉及同一接口 / 类型时签名 / 字段 / 语义一致
5. **依赖关系闭环**——A 声明依赖 B 提供的能力，B 真的暴露了；有没有单向悬空依赖
6. **同类聚合与命名**——同 type 文档遵循 `{type}-{slug}.md`，根目录某 type ≥6 份是否还平铺（参照 `shared-conventions.md`）

---

## 4. check 模式报告模板

```markdown
# 架构一致性检查报告

> 目标: design-internal | design-vs-code | architecture-folder-internal
> 范围: {feature}/{模块}/{章节范围}
> 日期: YYYY-MM-DD
> 结论: pass | pass-with-risk | fail

## 1. 检查摘要

一句话总结。

## 2. 不一致清单

| ID | 严重级别 | 位置 | 现象 | 影响 | 建议修复 |
|---|---|---|---|---|---|
| AC-01 | 高/中/低 | `{文件}:{行号}` 或 `design 第X节` | 描述 | 后果 | 修复建议（不执行） |

## 3. 观察项（范围外，不动手）

读 `architecture/` 时发现的结构性问题：某个 type ≥6 份仍平铺（应触发 `update` 搬迁）；文件名没遵循 `{type}-{slug}.md`；其他顺带看到的不合理点。没有就省略本节。

## 4. 一致性良好项

列 2-5 条检查通过的关键点——只有负面信息的报告让用户失去对系统的整体信心。

## 5. 建议下一步

- **fail**：建议先修哪几条再重跑
- **pass-with-risk**：实现 / 验收阶段重点回归哪些点
- **pass**：可进下一阶段
```

**严重级别**：

- **高**：让实现走错方向，或代码已和 design 实质偏离（漏实现关键契约 / 行为相反 / 术语指代不同的东西）
- **中**：能猜出意图但留有歧义（同义词漂移 / 契约示例和决策表面对得上但细节冲突 / 退出信号说不清）
- **低**：表述别扭或可读性问题，不影响理解

---

## 5. compound 检索命令（backfill / update 用）

```bash
python codestable/tools/search-yaml.py --dir codestable/compound --filter doc_type=decision --filter status=active --query "{模块关键词}"
python codestable/tools/search-yaml.py --dir codestable/compound --filter doc_type=explore --query "{模块关键词}"
python codestable/tools/search-yaml.py --dir codestable/compound --filter doc_type=learning --query "{模块关键词}"
```
