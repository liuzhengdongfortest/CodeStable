# Issue Report Protocol

这一阶段做两件事：把用户脑子里的问题落成结构化记录 + 判断走标准路径还是快速通道。

**核心原则：只记现象不记根因**。用户说"我觉得是 XX 组件的问题"——记下"用户怀疑 XX 组件"作为线索，但不顺着聊根因。根因要在阶段 2 通过实际读代码确认，不靠脑子里猜。混进根因猜测的报告会带偏阶段 2，让分析人围着错误线索绕。

## Spec

```haskell
data ReportQuestion = Symptom | Reproduction | ExpectedVsActual | Environment | Severity
data ReportPath = Standard | FastPath
data ReportNext = AnalyzeNext | FixNext
data ReportOutcome
  = RouteFeature | Ask ReportQuestion | ProposeFastPath RootCause FixPlan
  | PersistDraftAndCheckpoint CheckpointReason
  | ReviseAndCheckpoint Feedback CheckpointReason | Blocked Reason
  | PersistAndRoute IssuePath ReportNext

selectPath :: ReportFacts -> ReportOutcome
selectPath facts
  | describesNewCapability facts                    = RouteFeature
  | rootCauseHasFileLine facts
  , fixPoints facts <= 2
  , not (crossModuleRisk facts)                     = ProposeFastPath (rootCause facts) (fixPlan facts)
  | otherwise                                       = Ask Symptom

nextQuestion :: ReportAnswers -> Maybe ReportQuestion
nextQuestion answers = firstMissing [Symptom, Reproduction, ExpectedVsActual, Environment, Severity] answers

advance :: ReportPath -> ReportAnswers -> Maybe CheckpointAnswer -> ReportOutcome
advance _ answers _
  | Just q <- nextQuestion answers  = Ask q
advance Standard _ (Just ApproveCheckpoint) = PersistAndRoute StandardPath AnalyzeNext
advance Standard _ (Just RejectCheckpoint) = Blocked ReportRejected
advance Standard _ (Just (ReviseCheckpoint feedback)) = ReviseAndCheckpoint feedback ConfirmReport
advance Standard _ Nothing          = PersistDraftAndCheckpoint ConfirmReport
advance FastPath _ (Just ApproveCheckpoint) = PersistAndRoute FastPathApproved FixNext
advance FastPath _ (Just RejectCheckpoint)  = PersistAndRoute FastPathRejected AnalyzeNext
advance FastPath _ (Just (ReviseCheckpoint feedback)) = ReviseAndCheckpoint feedback ConfirmFixPlan
advance FastPath _ Nothing          = PersistDraftAndCheckpoint ConfirmFixPlan
```

`PersistDraftAndCheckpoint` 先写 `status: draft` 的 report，并按 approval 约定把同一 decision 写成
pending；fast-track 使用命名决策 `approvals.issue-fast-path`（ref 为
`approval-report.md#issue-fast-path`）。只有持久状态成功后才返回 `HumanCheckpoint`。因此 standard / fast-track 的 owner 回复都能
从仓库恢复，不依赖聊天历史。两条路径共用第一条 `nextQuestion` guard，fast-track 不得绕过五问。
`advance` 的 owner 参数只来自主入口已按同一 `CheckpointReason` 验证的 `ResumeIssueCheckpoint`，不得从聊天文本构造；`ReviseCheckpoint feedback` 先修订 draft 再写新 pending decision，Standard report 的 `RejectCheckpoint` 终止本次 issue，不能重发同一 checkpoint。

> 共享路径与命名约定看 `.codestable/reference/shared-conventions.md` 第 0 节和 `cs-issue` 的"文件放哪儿"。

---

## 启动检查

1. 按 `selectPath` 确认是 bug 并做唯一一次快速通道判定；必须实际读相关代码。
2. 检查 `.codestable/issues/` 是否已有同类目录，有则让用户选择新建或更新。
3. 和用户确定 slug，日期前缀用 `currentDate`；两种路径都创建 issue 目录。

进入 Standard 后不二次改判。`ProposeFastPath` 必须先向用户展示 file:line 根因与小范围方案，
并按 approval 约定写 `approval-report.md#issue-fast-path`；得到 `ConfirmFixPlan` 后把报告写成 `status: confirmed`、
`issue_path: fast-track`，记录 fast-path 已批准再进入 fix。用户拒绝则记录 `Rejected`，把
`issue_path` 写成 `standard`，写 confirmed report 后进入 analyze。普通路径同样写 `standard`。
---

## 必答 5 问

按顺序逐个问，**不一次抛 5 个**——一次抛多个用户只回最容易的，深的就漏了。每问做一次模糊度检查，不通过继续追问。

### 1. 问题是什么？看到的现象？

期待具体的异常表现："点击提交按钮后弹出了空白弹窗" 比 "提交功能有问题" 有用一百倍。

模糊信号："有时候会出错"、"感觉不对" → 追问"具体什么时候"、"具体什么不对"。

红线：**不要让用户描述根因**。出现"应该是因为 XXX"——记现象，根因留给阶段 2。

### 2. 怎么复现？

期待最小复现步骤：进入 XX 页面 → 输入 YY → 点击 ZZ → 看到问题现象。

模糊信号："不稳定复现"、"有时候能有时候不能" → 追问复现频率和条件差异。确实不稳定就写明已知触发条件和复现率。

"无法复现"也是有效回答——写"目前无法稳定复现，只在 X 情况下观察到一次"，别勉强凑步骤。

### 3. 期望行为 vs 实际行为

期待两句话：
- **期望**：我以为做了 A 之后应该发生 B
- **实际**：但实际发生了 C

**不要合并成一句**。合在一句"按钮没正常工作"里分析的人不知道"正常"长什么样。

### 4. 环境信息

最低采集：**在哪个模块 / 功能区域发现的**、**相关文件或函数（用户知道的话）**。

可选：操作系统、浏览器版本、运行环境（dev / prod）、最近有没有改过相关代码。

用户说"不知道在哪个文件"——写"待定"，阶段 2 分析时查。

### 5. 严重程度与优先级

- **P0 阻塞**：核心功能完全失效，影响所有用户，必须立刻修
- **P1 严重**：核心功能受损有绕过方法，尽快修
- **P2 中等**：非核心功能或影响少数用户，计划内修
- **P3 轻微**：UI 瑕疵 / 边界情况 / 有更好实现，按空闲修

用户不确定就帮他推荐一个但让用户拍板。

---

## 问题报告模板

```markdown
---
doc_type: issue-report
issue: {issue 目录名}
status: draft
issue_path: undecided # undecided | standard | fast-track
severity: P0 | P1 | P2 | P3
summary: {问题现象一句话}
tags: []
---

# {问题简述} Issue Report

## 1. 问题现象

{用户描述的具体异常表现，纯现象描述，不含根因推测}

## 2. 复现步骤

1. {步骤 1}
2. {步骤 2}
3. 观察到：{问题现象}

复现频率：{稳定 / 概率（约 X%） / 暂无法稳定}

## 3. 期望 vs 实际

**期望行为**：{做了 A 应该发生 B}

**实际行为**：{但实际发生了 C}

## 4. 环境信息

- 涉及模块 / 功能：{模块名或功能描述}
- 相关文件 / 函数：{已知 file:line 或"待定"}
- 运行环境：{dev / staging / prod / 不确定}
- 其他上下文：{OS、浏览器、最近改动等，没有写"无"}

## 5. 严重程度

**{P0 / P1 / P2 / P3}** — {一句话理由}

## 备注

{可选：截图描述、日志片段等}
```

---

## 退出条件

- [ ] frontmatter 完整（`doc_type=issue-report` / `issue` 一致 / `issue_path` 合法 / `severity` 和 `summary` 非空 / `tags` ≥ 1）
- [ ] 5 问都有具体答案（环境中相关文件可"待定"）
- [ ] 问题现象是纯现象描述，没混入根因推测
- [ ] 期望 vs 实际显式分开写
- [ ] 复现步骤可执行（"无法稳定复现"也有说明）
- [ ] 用户明确说"report 可以了，进下一步"
- [ ] frontmatter `status: confirmed`

---

## 退出后

按 confirmed report 的 `issue_path` 给出唯一下一步：

- `standard`：告诉用户“问题报告已就绪。下一步阶段 2 根因分析，进入 `cs-issue` analyze 阶段。”别自己顺手开始分析根因，阶段间的人工 checkpoint 是硬约束。
- `fast-track`：确认同 unit `approval-report.md#issue-fast-path` 已批准后，告诉用户“问题报告与小范围修复方案已确认。跳过 analysis，进入 `cs-issue` fix 阶段。”不得再无条件指向 analyze。

---

## 容易踩的坑

- 用户说"可能是 XX 的问题"你顺着聊根因——错，那是阶段 2
- 复现步骤太模糊（"在用户界面操作一下"）就放行——逼出可执行步骤
- 期望和实际混在一段话里——必须显式分开
- 严重程度留空——给默认值或写"无"
- 一口气把 5 问列成清单丢给用户填——逐题对话否则深的全漏
