# cs-feedback 报告模板

## `{slug}-report.md`

```markdown
---
doc_type: codestable-feedback
feedback: {YYYY-MM-DD}-{slug}
status: draft
created: {YYYY-MM-DD}
source_providers: [codex, claude]
github_issue: ""
---

# CodeStable Feedback: {title}

## 用户原始反馈

{user_feedback}

## 自动采集范围

- since_days: {N}
- session_filter: {session_filter_or_none}
- evidence: `evidence.json`
- matched_events: {count}

## 失败点清单

| # | 类型 | 相关 skill | 现象 | 证据 |
|---|---|---|---|---|
| 1 | tool-failure / unclear-rule / detour / install | `cs-feat` | {一句话} | {provider/session/timestamp} |

## 关键上下文

{按失败点摘要 evidence 里的 context，不贴完整 transcript。}

## 用户纠正信号

{用户指出 agent 绕路、做错阶段、没有按 skill 行为执行的原话和前后动作。}

## 疑似根因

{规则缺口 / 脚本缺口 / 分发缓存 / agent 执行偏差 / 需要更多样本。}

## 建议修改

- {改哪个 skill / reference / script / test}

## 上报状态

- GitHub issue: {url_or_pending}
- Manual fallback: {command_or_none}
```

## `github-issue.md`

```markdown
## Summary

{一句话说明 CodeStable skill 使用问题。}

## User Feedback

{用户原始反馈}

## Evidence

- Report: `{report_path}`
- Evidence: `{evidence_path}`
- Matched events: {count}

## Suspected Area

- Skill/reference/script: {paths_or_unknown}
- Failure type: {tool-failure|unclear-rule|detour|install|unknown}

## Context

{脱敏后的关键上下文；只放最小必要片段。}

## Expected Behavior

{用户期望或报告推断出的正确行为。}

## Proposed Fix

{建议补规则、脚本或测试。}
```
