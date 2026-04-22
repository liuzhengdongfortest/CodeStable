---
name: cs-refactor-ff
description: refactor 流程的超轻量通道——改动明显小到不值得走完整 scan → design → apply 三阶段时用。AI 直接识别 1-3 条低风险优化点、和用户一次确认、按经典方法原地改、跑测试自证。不写 scan 清单、不写 design、不拆多步 HUMAN 验证。触发场景：用户说"快速重构"、"小重构"、"简单优化下 XX 函数"、"直接改"、"别那么多步骤"，且改动范围明显在单函数 / 单组件局部、有测试可自证。
---

# cs-refactor-ff

用户说"优化一下这个函数"而改动明显很小（单个函数变长了、一个组件里抽个 composable、一段重复代码合并）时，走完整三阶段太重。fastforward 做一件事：让 AI 像平时一样直接改，但守住 refactor 的底线——行为等价、引用经典方法、跑测试自证。

所以这个技能非常轻。没有 scan 清单、没有 design doc、没有 checklist，改完一句话汇报就行。

---

## 入场 3 条硬检查（不过就退出到完整流程）

开写前问自己 3 件事，任一不过就退到 `cs-refactor` 走完整流程：

1. **行为真的不变吗？** 用户描述里夹带了"顺便支持 X / 改成 Y"——这是行为改动，不是 refactor，让用户拆出去走 feature / issue
2. **范围真的小吗？** 超过 1 个文件、或单文件超过 100 行改动、或预计改动点超过 3 处——退到完整流程
3. **有测试能自证吗？** 目标代码有覆盖它的测试（单测 / 集成测 / 类型检查能抓到）——没测试就退到完整流程，或先做一个 characterization test 再回来

入场硬检查的 scan 阶段完整版是 7 条，这里压缩成最关键的 3 条——剩下 4 条（跨模块、全口味、生成代码、扫不完）在"范围真的小吗"里已经被隐含排除了。

---

## 用经典方法，不发挥

fastforward 不读完整方法库，但要守住："每一处改动都能对应到一个经典重构方法"。AI 心里想不出"我这步是 Extract Function / Memoization / Guard Clauses / ..."里的哪一个，就说明这次改动不是简单重构，退到完整流程去查方法库。

常用的几种（覆盖 fastforward 80% 场景）：

- **提取函数**（Extract Function）：一段 > 5 行、内聚、能命名的片段 → 抽出独立函数
- **提取变量**（Extract Variable）：复杂表达式 → 命名变量或 query
- **守卫语句**（Guard Clauses）：开头多层嵌套 if 检查 → 提前 return 拉平
- **分解条件**（Decompose Conditional）：复杂 if 条件 → 命名为布尔函数
- **抽 composable / hook**（Extract Composable）：组件里封闭的状态 + 副作用 → 独立 composable / hook
- **记忆化**（Memoization）：重复计算 → computed / useMemo
- **守卫清理**（Cancellation）：副作用缺 cleanup → 加 onUnmounted / useEffect return

想做的动作不在这几种里也不是开箱即用的经典方法（如涉及 Parallel Change / Strangler Fig / 分层纠偏）——退到完整流程。

---

## 流程

### 1. 一次对齐

收到请求后，一句话回用户：**"我打算做 {方法名}，动 {具体文件/函数}，改动点 {N} 处，预计影响 {范围}。确认就开干。"**

用户确认就下一步。用户说"还有个 X 要改"——评估这个 X 是否破坏入场 3 条检查，破坏了就退到完整流程。

### 2. 改

按经典方法的步骤改。不产出 design doc、不产出 checklist。代码改动直接落盘。

### 3. 自证

- 跑测试（单元 / 集成 / 类型检查 / lint）
- grep 检查旧引用是否清理干净（如果做了 Extract Function / Inline Function 这类）
- 如果改了前端状态逻辑，跑类型检查 + 已有测试；**不做 UI 目视验证**——要 UI 目视就不该走 fastforward

### 4. 一句话汇报

格式：

```
✓ 已完成。方法：{方法名}。改动：{文件路径:行号范围}。验证：{跑了什么测试 / 通过情况}。
```

有偏离、或 apply 过程中发现想再改点别的——**停下问用户，不要发挥**。

---

## 文件产出

默认**不在 `codestable/refactors/` 下建目录**——fastforward 的价值就在不留存档。

例外：用户明确说"这次小重构要留个记录"——建一个 `codestable/refactors/{YYYY-MM-DD}-{slug}/{slug}-refactor-note.md`，内容就是上面那句汇报再加一段"做了什么 / 为什么"。不写 design，不写 checklist。

---

## 什么时候跳出 fastforward

改到一半出现下面任一情况，**停下来告诉用户"比预期复杂，建议切回完整 refactor 流程"**：

- 改动点从 3 个涨到 5+
- 发现要动的文件不止 1 个
- 冒出一个不在常用方法清单里的动作
- 发现没有测试能覆盖改动
- 用户追加 "顺便改一下 X" 带入行为改动
- 改完 AI 自证失败（测试挂了）且不是简单修正能搞定

切回方式：触发 `cs-refactor`，从 scan 阶段开始。已改的部分要么提交保留、要么 `git restore` 回到干净状态再扫，看用户决定。

---

## 不做什么

- **不写 scan 清单 / design doc / checklist** —— 写了就违背 fastforward 存在的理由
- **不跨多文件改** —— 跨文件就不是"小重构"
- **不做需要 HUMAN 目视的改动** —— 前端渲染 / 交互 / 性能感知要人看的，走完整流程
- **不碰公开接口** —— 改了公开接口要走 Parallel Change，Parallel Change 不是 fastforward 能做的

---

## 容易踩的坑

- **把"小"判断得太宽**：用户说"小重构"但实际要动 3 个文件——AI 要老实说"这不算小，建议走完整流程"
- **跳过入场 3 条检查就开干**：这个技能的意义就在这 3 条
- **自证偷懒**：只跑类型检查不跑单元测试，或完全不 grep 旧引用
- **改中发挥**：看到邻居代码也"顺手改改"——fastforward 的范围在确认那一刻就锁死，后续不扩
- **行为改动伪装成重构**：加个新参数、改返回值格式——这是行为改动，伪装不了

---

## 相关

- `cs-refactor/SKILL.md` — 完整 refactor 流程，复杂时切过来
- `cs-refactor/reference/methods.md` — 完整方法库（fastforward 用户想查也可以翻，但执行不依赖它）
- `codestable/reference/system-overview.md` — CodeStable 体系总览
