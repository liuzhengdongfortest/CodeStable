---
name: easysdd-architecture-check
description: 做一次架构体检，三选一：查一份 design 自己是否前后自洽（术语、契约、推进步骤之间不打架）；查 design 和代码是否对得上（承诺了的东西代码真的做到了）；查 `easysdd/architecture/` 下多份架构文档之间是否自洽（术语、模块边界、跨文引用不打架）。本技能只出问题清单和修复建议，不动手改东西。每次只锁定一个目标，不允许"顺手把另一项也查了"。触发场景：用户说"做架构检查"、"design 内部一致吗"、"方案和代码对得上吗"、"architecture 文件夹里几份文档有没有打架"，或 implement / acceptance 阶段想先做一次体检再继续。
---

# easysdd-architecture-check

design 写得越久，矛盾越容易藏在细节里——第 0 节定义的术语在第 3 节被悄悄换成了同义词；第 2 节的契约示例和第 1 节的关键决策对不上；声明"不做"的事情在推进步骤里悄悄出现了。代码一旦落地，"我以为方案是这样写的"和"代码实际是这样的"也会慢慢分叉。

本技能就是给这种时候做一次定向体检——只看不改，把不和谐点说清楚，让用户决定要不要改、怎么改。

---

## 适用场景

- 一份 design 要进入实现前，先确认它内部自洽
- feature 接近验收，确认代码和 design 对得上
- 改了一轮 design 后，确认新内容没和旧约定打架

不适用：

- 用户希望直接修复 → 转 `easysdd-feature-implement` 或 `easysdd-issue-fix`
- 用户希望做拍板决策 → 转 `easysdd-decisions`
- 用户还没有 design → 先转 `easysdd-feature-design`

---

## 单目标规则

每次只检查一个目标，三选一：

- `design-internal`：一份 feature design 文档内部一致性
- `design-vs-code`：一份 feature design 与代码的一致性
- `architecture-folder-internal`：`easysdd/architecture/` 下多份架构文档之间的一致性

为什么不允许一次查多个？三类检查的视角和读取材料完全不同——同时做会导致每边都做不深，问题也容易混在一起说不清是谁的责任。用户提多个目标就让 TA 选一个，其余留到下次。

> 共享路径与命名约定看 `easysdd/reference/shared-conventions.md`。

---

## 工作流

### Phase 1：锁定检查目标

确认三件事：

- 当前检查目标（`design-internal` / `design-vs-code` / `architecture-folder-internal`）
- 检查对象：feature 名（前两种目标）或 architecture 子范围（第三种目标，比如"全部"/"某个 type"/"某几份文档"）
- 检查范围（哪一节、哪个模块、哪几份文档）

范围太大就让用户收敛——把一堆文档全查一遍出来的报告读起来反而抓不到重点。`architecture-folder-internal` 默认只查用户点名的那几份文档或某个 type 下的同类文档，不主动扩到全文件夹。

### Phase 2：读取材料

共同必读：

- `AGENTS.md`
- `easysdd/reference/shared-conventions.md`

`design-internal` / `design-vs-code` 额外读：

- 方案 doc 全文
- 架构中心目录相关文档（如 DESIGN.md）

`design-vs-code` 再额外读：

- 与 design 第 2/3 节直接对应的代码文件

`architecture-folder-internal` 额外读：

- 用户圈定的那几份 `easysdd/architecture/**/*.md`（或某个 type 下的全部同类文档）
- `easysdd/architecture/` 的索引文件（如存在）
- 被文档内互相引用到的其他架构文档（顺藤摸到为止，不扩展到代码）

### Phase 3：执行检查

#### 目标 A：design-internal

至少覆盖这 6 类：

1. 术语一致性——第 0 节定义的术语后面有没有被同义词替换或语义漂移
2. 需求对齐——第 1 节摘要是否自洽，是否偏离已确认目标
3. 契约闭环——第 2 节的契约示例是否在第 3 节有对应的改动计划
4. 示例与决策一致——第 2 节契约示例的行为是否与第 1 节关键决策矛盾
5. 范围守护——第 3 节改动计划有没有超出第 1 节"明确不做"
6. 推进可执行性——第 3 节推进步骤能否验证、依赖前后是否矛盾

#### 目标 B：design-vs-code

至少覆盖这 6 类：

1. 类型一致性——design 第 2 节定义的核心类型/字段，代码里存在且语义一致吗
2. 行为一致性——design 第 2 节声明的输入→输出，代码实际行为对得上吗
3. 写路径一致性——design 声明的写入口，代码有没有冒出额外的旁路写入
4. 边界行为一致性——design 第 1 节的异常/边界规则，代码有没有实现
5. 改动边界一致性——design 第 3 节声明的改动范围，代码有没有越界或漏实现
6. 推进结果一致性——design 第 3 节每步的退出信号，对应代码状态可验证吗

#### 目标 C：architecture-folder-internal

至少覆盖这 6 类：

1. 术语一致性——多份文档对同一概念的称呼是否统一，有没有同义词漂移或同名异义
2. 模块边界一致性——A 文档说某职责归模块 X，B 文档里是不是也这么说；有没有两份文档都声称自己拥有同一块职责
3. 跨文引用有效性——文档里 `see xxx.md` / `定义见 yyy.md` 这类引用，目标文件和目标小节真的存在吗
4. 接口/契约对齐——多份文档涉及同一接口/类型时，签名、字段、语义是否一致
5. 依赖关系闭环——A 文档声明依赖 B 提供的能力，B 文档里真的暴露了该能力吗；有没有单向悬空依赖
6. 同类聚合与命名——同 type 文档是否遵循 `{type}-{slug}.md`，根目录某 type 已 ≥6 份是否还在平铺（参照 `easysdd/reference/shared-conventions.md`）

### Phase 4：输出检查报告

报告格式：

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

读 `easysdd/architecture/` 时若发现下列结构性问题，列在这里交给用户决定是否另起工作流处理：

- 某个 type 在根目录已 ≥6 份仍平铺（违反 `easysdd/reference/shared-conventions.md` 的同类聚合规则，应触发 `easysdd-architecture-gen` 搬迁）
- 文件名没遵循 `{type}-{slug}.md`，未来无法聚合
- 其他和本次检查目标无关、但顺带看到的不合理点

没有就省略本节。

## 4. 一致性良好项

列 2-5 条检查通过的关键点——只有负面信息的报告会让用户失去对系统的整体信心。

## 5. 建议下一步

- fail：建议先修哪几条再重跑本技能
- pass-with-risk：实现/验收阶段重点回归哪些点
- pass：可进入下一阶段
```

严重级别怎么定：

- **高**：会让实现走错方向，或代码已和 design 实质偏离（漏实现关键契约、行为相反、术语指代不同的东西）
- **中**：能猜出意图但留有歧义，下游容易误读（同义词漂移、契约示例和决策表面对得上但细节冲突、退出信号说不清楚）
- **低**：表述别扭或可读性问题，不影响理解（顺序欠妥、措辞可优化）

报告给用户后等用户确认结论——是否接受、要不要本技能再补一类检查、还是直接进入用户自己决定的下一步。本技能不替用户拍板。

---

## 硬性边界

1. **只检查，不修复**——禁止改 design / 代码 / 配置
2. **单目标**——一次只能锁定 design-internal / design-vs-code / architecture-folder-internal 三者之一
3. **证据化**——每条不一致都要有可定位位置（文件:行号 或 design 节）
4. **可执行建议**——具体到"改哪里、怎么改"，但不落盘
5. **不发散**——发现范围外问题只记为"观察项"，不展开深挖

为什么不允许直接修？把检查和修复分开做，用户才能看到完整的不一致清单后整体决定优先级——一边查一边改会让用户失去这层判断机会。

---

## 退出条件

- [ ] 已锁定单一检查目标
- [ ] 已完成对应目标的检查项覆盖
- [ ] 报告含不一致清单 + 修复建议
- [ ] 报告未包含任何实际修复动作
- [ ] 用户确认本轮检查结论

---

## 容易踩的坑

- ❌ 一次同时做多个目标（design-internal / design-vs-code / architecture-folder-internal 只能选一个）
- ❌ `architecture-folder-internal` 顺手读代码去验证——那是 `design-vs-code` 的事
- ❌ 发现问题就顺手改代码或文档
- ❌ 只说"这里不太对"，不给证据位置
- ❌ 建议过于抽象（"优化一下架构"）
- ❌ 从一个目标无限扩展到全仓库审计
