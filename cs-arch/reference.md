# cs-arch 参考模板

本文件提供 `cs-arch` 使用的详细模板和清单。SKILL.md 只保留流程骨架，具体格式、覆盖项、报告模板都在这里。

---

## 1. 架构文档结构（new / update 模式产出）

### 1.1 frontmatter

```yaml
---
doc_type: architecture
slug: {英文描述，连字符分隔；和文件名一致}
scope: {一句话说清楚这份 doc 覆盖的范围}
summary: {一句话总结这块架构的要点}
status: current | draft | outdated
last_reviewed: YYYY-MM-DD
tags: []
depends_on: []   # 其他 architecture doc 的 slug，可选
implements: []   # 这块架构承载的 requirement slug 列表（`codestable/requirements/` 下），可空——纯基础设施 / 工具层没有对应 requirement 是正常的
---
```

### 1.2 正文节

```markdown
## 0. 术语

本文里首次引入的专有名词简要定义，外加和相近名词的区分（"本文里 X 指 Y，和代码里的 X' 不是同一个东西"）。没有新术语就省略本节。

## 1. 定位与受众

- 本 doc 描述的是项目里哪一块（模块 / 子系统 / 跨模块关注点）
- 谁会读这份 doc（feature-design / issue-analyze / 新人上手……）
- 读完能干嘛（定位到对应代码 / 了解对外接口 / 知道约束）

## 2. 结构与交互

- 模块怎么划分、依赖方向
- 对外接口（别人怎么用这块）、对内接口（这块怎么用别人）
- 跨模块契约（数据格式 / 调用协议 / 状态归属）
- 模块 ≤ 2 或关系线性时不画图；否则建议 Mermaid

每条结构化断言后附 `file:line` 锚点，或在节末尾的"代码锚点"小节集中给。

## 3. 数据与状态

- 关键类型 / 核心数据结构（简述 + 定义位置 file:line）
- 所有权归属（谁写、谁读）
- 持久化边界（内存 / 本地 / 数据库 / 外部服务）

## 4. 关键决策

不是决策全文，是**引用**——每条一两行：

- 结论一句话
- 引用：`codestable/compound/YYYY-MM-DD-decision-{slug}.md` 或用户原话出处
- 为什么引用到这份架构 doc 里（和本模块的关系）

没有已落档的决策就省略本节，或记 `TODO: 某决定应沉淀为 decision`。

## 5. 代码锚点

集中列一份"想看代码从哪看"的清单：

- 入口文件 / 关键函数 / 关键类型定义
- 格式：`{file}:{function/class} — 一行说明`

## 6. 已知约束 / 边界情况

本模块现在有哪些"不能动 / 动了要小心"的硬约束，以及它们的来源（AGENTS.md / decision / learning 等项目里记载硬约束的位置）。

## 7. 相关文档

- 依赖的其他 architecture doc
- 承载的 requirement（对应 frontmatter `implements`）
- 相关 decision / learning / trick / explore 的链接
- 使用本模块的代表性 feature design

## 变更日志（update 模式才有）

- YYYY-MM-DD：{一句话描述}
```

---

## 2. new / update 自查清单

用户 review 前，自己先把下面这组检查过一遍。每一条都针对一种 AI 默认会犯的错：

1. **每个结构化断言能不能锚到代码？**——"A 模块通过 X 调用 B"、"Y 持有 Z 的状态"、"所有写入经 W"——每一条在文档的"代码锚点"节或节内注释里能不能给出 `file:line` 支撑？锚不到的断言要么删掉、要么标 `TODO: 待确认` 交给用户。
2. **有没有替用户拍板？**——"关键决策"节里的条目是"引用已有 decision + 简述原文结论" / "引用用户素材里用户说过的原话"，还是 AI 自己编的选型理由？后者一律不许进文档——停下来问用户。
3. **有没有变成代码复述？**——每节至少一句话说"为什么这么分"，没有这一句的节基本就是 `ls` 贴文字。
4. **术语冲突检查做了吗？**——新引入的架构术语做一遍 grep（代码、`codestable/architecture/` 下所有文档、`codestable/compound/`）。冲突了就换名字或在第 0 节明确"本文里 X 指 Y，和代码里的 X' 不是一个东西"。
5. **是否和现有 architecture / decision 冲突？**——写的过程中如果发现和某条 decision 或其他架构文档描述的事实对不上，不许"写自己的那版"，要么引用那条、要么停下来问用户"是不是那条也该更新了"。
6. **单节长度**——每节超过 1 屏就该砍或拆。架构文档是给人快速定位的，不是用来读一遍的。
7. **update 模式专项**：本次新加 / 改动的段落是否都有对应的代码变化作为依据？纯凭空"加一句听起来更完整的描述"是内容飘离实际的开端。

---

## 3. check 模式覆盖项

三个子目标各自至少覆盖下面 6 类。

### 3.1 design-internal（一份 feature design 内部一致性）

1. **术语一致性**——第 0 节定义的术语后面有没有被同义词替换或语义漂移
2. **需求对齐**——第 1 节摘要是否自洽，是否偏离已确认目标
3. **契约闭环**——第 2 节的契约示例是否在第 3 节有对应的改动计划
4. **示例与决策一致**——第 2 节契约示例的行为是否与第 1 节关键决策矛盾
5. **范围守护**——第 3 节改动计划有没有超出第 1 节"明确不做"
6. **推进可执行性**——第 3 节推进步骤能否验证、依赖前后是否矛盾

### 3.2 design-vs-code（一份 feature design 与代码对得上）

1. **类型一致性**——design 第 2 节定义的核心类型 / 字段，代码里存在且语义一致吗
2. **行为一致性**——design 第 2 节声明的输入→输出，代码实际行为对得上吗
3. **写路径一致性**——design 声明的写入口，代码有没有冒出额外的旁路写入
4. **边界行为一致性**——design 第 1 节的异常 / 边界规则，代码有没有实现
5. **改动边界一致性**——design 第 3 节声明的改动范围，代码有没有越界或漏实现
6. **推进结果一致性**——design 第 3 节每步的退出信号，对应代码状态可验证吗

### 3.3 architecture-folder-internal（`codestable/architecture/` 下多份文档之间一致性）

1. **术语一致性**——多份文档对同一概念的称呼是否统一，有没有同义词漂移或同名异义
2. **模块边界一致性**——A 文档说某职责归模块 X，B 文档里是不是也这么说；有没有两份文档都声称自己拥有同一块职责
3. **跨文引用有效性**——文档里 `see xxx.md` / `定义见 yyy.md` 这类引用，目标文件和目标小节真的存在吗
4. **接口 / 契约对齐**——多份文档涉及同一接口 / 类型时，签名、字段、语义是否一致
5. **依赖关系闭环**——A 文档声明依赖 B 提供的能力，B 文档里真的暴露了该能力吗；有没有单向悬空依赖
6. **同类聚合与命名**——同 type 文档是否遵循 `{type}-{slug}.md`，根目录某 type 已 ≥6 份是否还在平铺（参照 `codestable/reference/shared-conventions.md`）

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

读 `codestable/architecture/` 时若发现下列结构性问题，列在这里交给用户决定是否另起工作流处理：

- 某个 type 在根目录已 ≥6 份仍平铺（违反 shared-conventions 的同类聚合规则，应触发 `cs-arch` 的 `update` 模式搬迁）
- 文件名没遵循 `{type}-{slug}.md`，未来无法聚合
- 其他和本次检查目标无关、但顺带看到的不合理点

没有就省略本节。

## 4. 一致性良好项

列 2-5 条检查通过的关键点——只有负面信息的报告会让用户失去对系统的整体信心。

## 5. 建议下一步

- **fail**：建议先修哪几条再重跑本技能
- **pass-with-risk**：实现 / 验收阶段重点回归哪些点
- **pass**：可进入下一阶段
```

### 严重级别怎么定

- **高**：会让实现走错方向，或代码已和 design 实质偏离（漏实现关键契约、行为相反、术语指代不同的东西）
- **中**：能猜出意图但留有歧义，下游容易误读（同义词漂移、契约示例和决策表面对得上但细节冲突、退出信号说不清楚）
- **低**：表述别扭或可读性问题，不影响理解（顺序欠妥、措辞可优化）

---

## 5. compound 检索命令（new / update 用）

```bash
python codestable/tools/search-yaml.py --dir codestable/compound --filter doc_type=decision --filter status=active --query "{模块关键词}"
python codestable/tools/search-yaml.py --dir codestable/compound --filter doc_type=explore --query "{模块关键词}"
python codestable/tools/search-yaml.py --dir codestable/compound --filter doc_type=learning --query "{模块关键词}"
```
