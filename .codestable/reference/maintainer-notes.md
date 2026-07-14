# CodeStable 维护者说明

本文件由 `cs-onboard` 复制到项目的 `.codestable/reference/maintainer-notes.md`。维护 CodeStable 技能家族时需要反复查阅、但不适合放在各子技能正文里的说明。

---

## 1. 断点恢复

AI 对话随时可能中断（token 超限、网络断开、用户换设备）。各阶段发现自己不是从零开始时，必须优先检查已有产物的完成度，从上次停下的地方继续：

```haskell
resume :: Stage -> ArtifactState -> ResumeOutcome
resume Brainstorm artifact = AskResumeOrRestart (lastCompletedTopic artifact)
resume Design artifact     = ContinueAt (firstIncompleteSection artifact)
resume Implementation c    = ContinueAt (firstPendingStep c)
resume Acceptance artifact = ContinueAt (firstIncompleteSection artifact)
resume IssueAnalyze a      = ContinueAt (firstIncompleteOf 5 a)
resume IssueFix state
  | codeChanged state && not (fixNoteExists state) = VerifyThenWriteFixNote
  | otherwise                                      = ContinueAt (persistedStage state)
```

恢复时先向用户简短汇报："检测到上次工作到 X 阶段，我从 Y 继续"。

---

## 2. 扩展点

### 新增子工作流

新工作流定型后，在 `cs-onboard` skill 内 `references/system-overview.md` 的技能分类和场景路由中加一段索引，并登记新的目录位置。

### 跨阶段新约束

如果发现某条规则适用于所有阶段（例如所有 spec doc 都必须补某个字段），优先写进共享 reference（`shared-conventions.md` 或 `system-overview.md`），不要只改一个子技能。

### 新模板 / 新产物类型

如果引入新的 spec 产物（例如风险评估表、回滚预案），先在 `shared-conventions.md` 登记路径，再在对应阶段技能里引用。

### 共享术语表

如果 CodeStable 自己形成了稳定共享术语，应优先沉淀成共享 reference，而不是散落在多个子技能里重复定义。

### 跨工作流状态一览

目前查看"项目当前有几个 feature 在进行中、几个 issue 未关闭"仍需要手动查询。未来如要补 `status.py` 或 `.codestable/STATUS.md`，先在 `shared-conventions.md` 登记方向，再实现。

---

## 3. 维护规则

- 每次扩展都要同步更新 `system-overview.md` 索引和相关子技能
- 不允许只在某个子技能里加东西而不在 `system-overview.md` 登记
- 共享说明优先放 `.codestable/reference/`，不要散落在各子技能里

---

## 4. 发版前走链路审查

多层协议体系的主要缺陷形态是**跨层语义冲突**：每个文件单独读都对，agent 沿链路组合执行时才矛盾（例如阶段协议要求"停等用户"而 goal 协议要求"长程不停"）。结构不变量交给 `tests/test_skill_entry_simplification.py`，但测试只锁已知规则；改动主入口或阶段协议后，发版前必须人工走一遍主链路：

1. 以陌生 agent 视角沿 `cs-feat`（design → design-review → 用户 gate → goal 包 → driver 派发 → impl → code review → QA → accept）和 `cs-epic` 全链路读文档，每一步问：下一步是否唯一确定？停等语义、状态字段、reference 加载时机、handoff 条件在相邻两层是否一致？
2. 重点扫三类冲突源：普通模式 vs goal 模式的停点、SKILL.md 状态机 vs 深层协议、主入口 vs 共享 conventions。
3. 发现的每条冲突修复后，问"哪个测试能锁住它"，能锁的补进测试。
