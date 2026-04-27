---
name: cs-refactor-ff
description: refactor 流程的超轻量通道——直接识别 1-3 条低风险优化、一次确认、原地改、跑测试自证。触发：用户说"快速重构"、"小重构"、"简单优化下 XX 函数"、"别那么多步骤"，且改动在单函数 / 单组件局部、有测试可自证。
---

# cs-refactor-ff

用户说"优化一下这个函数"而改动明显很小（单函数变长、组件里抽个 composable、一段重复代码合并）时走完整三阶段太重。fastforward 让 AI 像平时一样直接改但守住底线——行为等价、引用经典方法、跑测试自证。

很轻：没有 scan 清单、没有 design doc、没有 checklist，改完一句话汇报就行。

---

## 入场 3 条硬检查（不过就退完整流程）

任一不过就退到 `cs-refactor`：

1. **行为真的不变吗？** 用户描述夹带"顺便支持 X / 改成 Y"——这是行为改动不是 refactor，让用户拆出去走 feature / issue
2. **范围真的小吗？** 超过 1 个文件 / 单文件超过 100 行改动 / 预计改动点超过 3 处——退完整流程
3. **有测试能自证吗？** 目标代码有覆盖（单测 / 集成测 / 类型检查能抓到）——没测试就退完整流程，或先做一个 characterization test 再回来

完整 scan 阶段是 7 条入场检查，这里压成最关键 3 条——剩下 4 条（跨模块 / 全口味 / 生成代码 / 扫不完）在"范围真的小吗"里已被隐含排除。

---

## 用经典方法不发挥

fastforward 不读完整方法库，但要守住"**每一处改动都能对应到一个经典重构方法**"。AI 心里想不出"我这步是 Extract Function / Memoization / Guard Clauses / ..." 里的哪一个 → 这次不是简单重构退完整流程查方法库。

常用方法（覆盖 fastforward 80% 场景）：

- **Extract Function**：> 5 行、内聚、能命名的片段 → 抽出独立函数
- **Extract Variable**：复杂表达式 → 命名变量或 query
- **Guard Clauses**：开头多层嵌套 if 检查 → 提前 return 拉平
- **Decompose Conditional**：复杂 if 条件 → 命名为布尔函数
- **Extract Composable / hook**：组件里封闭的状态 + 副作用 → 独立 composable / hook
- **Memoization**：重复计算 → computed / useMemo
- **Cancellation**：副作用缺 cleanup → 加 onUnmounted / useEffect return

想做的动作不在这几种里、不是开箱即用的经典方法（涉及 Parallel Change / Strangler Fig / 分层纠偏）→ 退完整流程。

---

## 流程

### 1. 一次对齐

一句话回用户：**"我打算做 {方法名}，动 {具体文件/函数}，改动点 {N} 处，预计影响 {范围}。确认就开干。"**

确认就下一步。用户说"还有个 X 要改"——评估 X 是否破坏入场 3 条，破坏了就退完整流程。

### 2. 改

按经典方法步骤改。不产出 design doc / checklist，代码直接落盘。

### 3. 自证

- 跑测试（单元 / 集成 / 类型检查 / lint）
- grep 检查旧引用是否清理干净（做了 Extract / Inline 这类）
- 改了前端状态逻辑跑类型检查 + 已有测试；**不做 UI 目视验证**——要 UI 目视就不该走 fastforward

### 4. 一句话汇报

```
✓ 已完成。方法：{方法名}。改动：{文件路径:行号范围}。验证：{跑了什么测试 / 通过情况}。
```

有偏离 / apply 过程中发现想再改点别的 → **停下问用户不发挥**。

---

## 文件产出

默认**不建 `codestable/refactors/` 目录**——fastforward 的价值就在不留存档。

例外：用户明确"这次要留个记录" → 建 `codestable/refactors/{YYYY-MM-DD}-{slug}/{slug}-refactor-note.md`，内容就是上面那句汇报 + 一段"做了什么 / 为什么"。不写 design / checklist。

---

## 什么时候跳出 fastforward

改到一半出现以下任一，**停下告诉用户"比预期复杂，建议切回完整流程"**：

- 改动点从 3 个涨到 5+
- 发现要动的文件不止 1 个
- 冒出一个不在常用方法清单里的动作
- 发现没有测试能覆盖
- 用户追加"顺便改一下 X"带入行为改动
- 改完 AI 自证失败且不是简单修正能搞定

切回：触发 `cs-refactor` 从 scan 开始。已改的部分要么提交保留、要么 `git restore` 回到干净状态再扫。

---

## 不做什么

- **不写 scan / design / checklist** —— 写了就违背 fastforward 存在的理由
- **不跨多文件改** —— 跨文件就不是"小重构"
- **不做需要 HUMAN 目视的改动** —— 前端渲染 / 交互 / 性能感知要人看的走完整流程
- **不碰公开接口** —— 改公开接口要走 Parallel Change，不是 fastforward 能做的

---

## 容易踩的坑

- **把"小"判断得太宽**：用户说"小重构"但实际动 3 个文件——AI 要老实说"这不算小"
- **跳过入场 3 条检查就开干**：这个技能的意义就在这 3 条
- **自证偷懒**：只跑类型检查不跑单元测试，或完全不 grep 旧引用
- **改中发挥**：看到邻居代码也"顺手改改"——fastforward 范围在确认那一刻就锁死
- **行为改动伪装成重构**：加新参数、改返回值格式——这是行为改动伪装不了

---

## 相关

- `cs-refactor/SKILL.md` — 完整 refactor 流程
- `cs-refactor/reference/methods.md` — 完整方法库
- `codestable/reference/system-overview.md` — CodeStable 体系总览
