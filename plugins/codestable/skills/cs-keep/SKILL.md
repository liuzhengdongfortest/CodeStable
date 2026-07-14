---
name: cs-keep
description: 项目知识沉淀。触发：用户要沉淀可复用坑、技巧、调研或非 ADR 结论；结构性 ADR 决策走 cs-domain，一两行每次必读规则走 cs-note。
---

# cs-keep

动作前先跑 CodeStable preflight：读 `.codestable/attention.md`（缺失先 `cs-onboard`）；不要用 `AGENTS.md`/`CLAUDE.md` 等外部入口代替它；细则见 `.codestable/reference/execution-conventions.md`。

## Spec

```haskell
data Note = Note { slug :: KebabCase, background :: Text, conclusion :: Text, evidence :: [Evidence] }
data KeepContext = KeepContext { attentionReady :: Bool }
data KeepOutcome = Written Path | NeedsHuman Reason

csKeep :: KeepContext -> Note -> KeepOutcome
csKeep ctx n
  | not (attentionReady ctx)                              = NeedsHuman AttentionMissing
  | validKebabMax 30 (slug n) && not (null (evidence n)) = Written ".codestable/compound/YYYY-MM-DD-{slug}.md"
  | otherwise                                             = NeedsHuman InvalidNote

render :: Note -> Markdown
render = markdown ["背景", "结论", "证据"]  -- 无 frontmatter/tags
```

## Operation

先按 preflight 读取 attention，再用关键词查重；命中相近旧文档时更新或新建由用户原始意图决定，分不清才问。校验 slug、背景、结论和至少一条可追溯证据后写三段 Markdown。写完只报路径，不追问分类或 tags。

未来要找回来直接 `grep -r "关键词" .codestable/compound/`。

## Failure Behavior

attention 缺失、目标与旧沉淀关系不清、结论没有用户素材或可追溯证据时返回 `NeedsHuman`；不得编造证据，也不得把 ADR 或启动必读短规则塞进 compound。
