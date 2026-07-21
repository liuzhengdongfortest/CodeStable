# Code Review Recovery Protocol

本协议只在已有 review lane 为 `failed` / `unavailable`，存在 pending/rejected review decision，
或调用方携带 `ReviewResume` 时加载。正常首次 review 不读取本文件。

## Spec

```haskell
data ReviewDecision
  = SelfReviewDowngradeDecision ExternalRunRef
  | UnavailableSelfReviewDowngradeDecision
  | SkipFailedOcrDecision ExternalRunRef

data ReviewResume
  = ResumeLane LaneName ExternalRunRef LaneResult
  | RetryFailedLane LaneName ExternalRunRef
  | RequestSelfReviewDowngrade ExternalRunRef
  | RequestUnavailableSelfReviewDowngrade
  | ResumeSelfReviewDowngrade ApprovalRef
  | RequestSkipFailedLaneB ExternalRunRef
  | ResumeSkipFailedLaneB ExternalRunRef ApprovalRef

applyReviewResume :: Maybe ReviewResume -> ReviewState -> Either ReviewBlocker ReviewState
applyReviewResume Nothing s = Right s
applyReviewResume (Just (ResumeLane lane ref result)) s
  | pendingLaneRef lane s == Just ref = Right (persistLaneResultAndClearDecision lane ref result s)
  | otherwise                         = Left InvalidReviewResume
applyReviewResume (Just (RetryFailedLane lane ref)) s
  | failedLaneRef lane s == Just ref = Right (persistLaneRetryAndSupersedeDecision lane ref s)
  | otherwise                        = Left InvalidReviewResume
applyReviewResume (Just (RequestSelfReviewDowngrade ref)) s
  | failedLaneRef LaneA s == Just ref
  , not (isExplicit s.agentConfig) = Right (persistPendingReviewDecision (SelfReviewDowngradeDecision ref) s)
  | otherwise                      = Left InvalidReviewResume
applyReviewResume (Just RequestUnavailableSelfReviewDowngrade) s
  | laneAMissing s
  , not (isExplicit s.agentConfig) = Right (persistPendingReviewDecision UnavailableSelfReviewDowngradeDecision s)
  | otherwise                      = Left InvalidReviewResume
applyReviewResume (Just (ResumeSelfReviewDowngrade approvalRef)) s
  | Just decision <- pendingReviewDecision s
  , isSelfReviewDowngradeDecision decision
  , approvalArtifactStatus s approvalRef "code-review-local-only" == Approved
      = Right (persistReviewDowngradeAndClearDecision decision s)
  | Just decision <- pendingReviewDecision s
  , isSelfReviewDowngradeDecision decision
  , approvalArtifactStatus s approvalRef "code-review-local-only" == Rejected
      = Right (persistRejectedReviewDecision decision s)
  | otherwise = Left InvalidReviewResume
applyReviewResume (Just (RequestSkipFailedLaneB ref)) s
  | failedLaneRef LaneB s == Just ref = Right (persistPendingReviewDecision (SkipFailedOcrDecision ref) s)
  | otherwise                        = Left InvalidReviewResume
applyReviewResume (Just (ResumeSkipFailedLaneB failedRef approvalRef)) s
  | pendingReviewDecision s == Just (SkipFailedOcrDecision failedRef)
  , approvalArtifactStatus s approvalRef "code-review-skip-failed-ocr" == Approved
      = Right (persistLaneSkipAndClearDecision LaneB failedRef s)
  | Just decision@(SkipFailedOcrDecision failedRef) <- pendingReviewDecision s
  , approvalArtifactStatus s approvalRef "code-review-skip-failed-ocr" == Rejected
      = Right (persistRejectedReviewDecision decision s)
  | otherwise = Left InvalidReviewResume

isSelfReviewDowngradeDecision :: ReviewDecision -> Bool
isSelfReviewDowngradeDecision (SelfReviewDowngradeDecision _) = True
isSelfReviewDowngradeDecision UnavailableSelfReviewDowngradeDecision = True
isSelfReviewDowngradeDecision _ = False

reviewDecisionCheckpoint :: ReviewDecision -> CheckpointReason
reviewDecisionCheckpoint (SelfReviewDowngradeDecision _) = SelfReviewDowngrade
reviewDecisionCheckpoint UnavailableSelfReviewDowngradeDecision = SelfReviewDowngrade
reviewDecisionCheckpoint (SkipFailedOcrDecision _) = SkipFailedOcr
```

## Decision Lifecycle

- failed lane 的 `Request*` 只接受精确匹配的 run ref；lane A 为 `Unavailable` 时只接受
  `RequestUnavailableSelfReviewDowngrade`，且显式 pin 下拒绝。`persistPendingReviewDecision` 把同
  lane 旧 rejected decision 标为 `superseded` 并清除，再把新命名 decision 写成 `pending`。
- `Resume*` 同时核验 pending decision、失败 ref、同 unit approval ref 和 decision id；`approved`
  执行降级/skip，`rejected` 清除 pending 并持久化 rejected fact，其他值 fail-closed。
- `persistRejectedReviewDecision` 保留原 `Failed ref reason`，让主入口返回 `ReviewWritten Blocked`；
  后续只能重试、修复配置，或在配置变化后发起新的匹配 decision。
- `persistReviewDowngradeAndClearDecision` 在 approved 后把 lane A 置为 `Skipped`，持久化
  `userAcceptedDowngrade = True` 并清除同 lane pending/rejected decision；批准后不得继续命中
  `anyLaneFailed` 或重复降级 checkpoint。
- `persistLaneRetryAndSupersedeDecision` 必须把同 lane 的 pending/rejected decision 标为
  `superseded` 并从 `ReviewState` 清除，再把 lane 置为 `ReadyToLaunch`。
- `persistLaneResultAndClearDecision` 在 lane 进入 `Completed` / `Failed` 时清除同 lane 的旧 decision；
  不得让已完成或正在等待的新 run 被旧 checkpoint guard 吞掉。
- 所有 decision 都使用同 unit `approval-report.md`；self review id 为 `code-review-local-only`，
  OCR skip id 为 `code-review-skip-failed-ocr`。聊天里的同意/拒绝不构成恢复事实。

## Failure Behavior

ref、lane、pending decision、decision id 或 approval path 任一不匹配时返回
`InvalidReviewResume`。owner 明确拒绝不是 invalid resume：必须消费为 rejected fact，再由主入口以
`ReviewWritten Blocked` 报告可恢复选项。
