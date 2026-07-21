# Docs Focused Edit Protocol

`FocusedEdit` 只处理已是 `current`、源码事实未漂移、目标路径明确的小范围文字修订。它不新建
文档、不调整读者定位、不重组 API manifest，也不借“小改”更新公开契约。

## Spec

```haskell
data FocusedEditStep = VerifyFacts | DraftPatch | PersistPatch
data FocusedEditOutcome
  = RunFocusedEdit FocusedEditStep | Checkpoint CheckpointReason
  | Route Stage | NeedsHuman Reason | Complete

focusedApprovalGate :: DocsState -> EditIntent -> Maybe CheckpointReason
focusedApprovalGate s intent
  | not (overwriteApproved s)                     = Just ConfirmOverwrite
  | changesPublicContract intent
  , not (contractWordingApproved s)               = Just ConfirmContractWording
  | otherwise                                     = Nothing

advanceFocusedEdit :: DocsState -> EditIntent -> FocusedEditOutcome
advanceFocusedEdit s intent
  | isNothing s.targetDoc                         = NeedsHuman "which document?"
  | not (focusedEditStateValid s) || s.codeDrift == Drifted
                                                    = Route (fullDocsStage s intent)
  | not (focusedEditIntentValid s intent)         = Route (fullDocsStage s intent)
  | Just reason <- focusedApprovalGate s intent   = Checkpoint reason
  | not (sourceFactsVerified s intent)            = RunFocusedEdit VerifyFacts
  | not (focusedDraftPersisted s intent)          = RunFocusedEdit DraftPatch
  | not (ownerApproved s)                         = Checkpoint ReviewDraft
  | not (focusedPatchCurrent s intent)            = RunFocusedEdit PersistPatch
  | otherwise                                     = Complete

focusedEditStateValid :: DocsState -> Bool
focusedEditStateValid s = s.docStatus == Current ||
  (s.docStatus == Draft && s.workflowStage == Just FocusedEdit)

focusedEditIntentValid :: DocsState -> EditIntent -> Bool
focusedEditIntentValid s intent = smallEdit intent || s.workflowStage == Just FocusedEdit
```

`fullDocsStage` 依据目标文档的既有类型返回 `ApiStage` 或 `TutorialStage`；不能判定时返回
`NeedsHuman "which reader?"`。`overwriteApproved`、`ownerApproved` 与
`contractWordingApproved` 只消费主入口已验证并持久化的 `ResumeDocsCheckpoint`，聊天中的口头
同意不能替代。

## 执行规则

1. 读取目标文档、用户点名段落，以及支撑该段表述的源码/spec；记录明确的事实来源。
2. 只生成目标段落的最小 patch，保持原有 `doc_type`、读者、目录结构和 manifest 归属。
3. `DraftPatch` 把目标文档标为 `status: draft`、`workflow_stage: focused-edit` 后进入
   `ReviewDraft`；`persistDocsDecision ReviewDraft ApproveDocs` 保留该临时 stage，用户批准后仍由主入口路由回本协议执行 `PersistPatch`，恢复
   `status: current`、删除临时 `workflow_stage` 并更新 `last_reviewed`（字段存在时）。
4. 一旦发现代码漂移、API 条目增删、结构重组、读者定位变化或多文件同步需求，停止
   FocusedEdit，回到对应 tutorial/api protocol；全局同步仍转 `cs-docs-neat`。

## 退出条件

- 目标文件和改动段落唯一明确，diff 只包含已批准的小范围文字修订。
- 每项新表述都能追溯到当前源码或项目事实，公开契约措辞已通过对应 checkpoint。
- 文档最终为 `status: current`，且没有遗留 manifest、README 或全局入口同步工作。
