# Agent 记忆与入口路径速查

执行 `cs-docs-neat` 时按当前实际存在的文件读取。没有独立 memory 的平台就跳过 memory 层，但仍要检查项目根 agent 入口。

## 项目根 agent 入口

| 文件 | 用途 |
|---|---|
| `CLAUDE.md` | Claude Code 项目级指令 |
| `AGENTS.md` | Codex 项目级指令 |
| `AGENTS.override.md` | Codex 同目录 override，存在时必须读 |
| `TEAM_GUIDE.md` / `.agents.md` | 部分团队或工具的 fallback 入口，存在时读 |

这些文件需要同步，但只放 agent 执行需要的规则、命令、红线、文档索引；不要变成项目 changelog。

## Claude Code

| 用途 | 路径 |
|---|---|
| 项目级指令 | 项目根 `CLAUDE.md` |
| 全局指令 | `~/.claude/CLAUDE.md` |
| 项目 memory | `~/.claude/projects/<encoded-project-path>/memory/` |
| memory 索引 | `~/.claude/projects/<...>/memory/MEMORY.md` |

Claude memory 常用 frontmatter：`name`、`description`、`type`。稳定项目事实应毕业到项目文档，memory 留个人偏好或指针。

## OpenAI Codex

| 用途 | 路径 |
|---|---|
| 项目级指令 | 项目根 `AGENTS.md` |
| 项目级 override | `AGENTS.override.md` |
| 全局指令 | `~/.codex/AGENTS.md` 或 `$CODEX_HOME/AGENTS.md` |

Codex 通常没有独立的项目 memory 文件。项目事实不要写进全局 `AGENTS.md`；应写项目根 `AGENTS.md` 或 `.codestable/`。

## OpenCode

| 用途 | 路径 |
|---|---|
| 全局配置 | `~/.config/opencode/` |
| 项目配置 | `.opencode/` |
| 项目 skills | `.opencode/skills/`、`.claude/skills/`、`.codex/skills/` |

若 `.opencode/` 内有项目指令或 memory 类文件，按 agent 入口处理。

## OpenClaw

| 用途 | 路径 |
|---|---|
| 用户级 skills | `~/.openclaw/skills/` |
| 项目级 skills | `.openclaw/skills/` |

OpenClaw 没有统一 memory 约定；发现项目级指令文件时按 agent 入口检查。

## 全局配置边界

`~/.claude/CLAUDE.md`、`~/.codex/AGENTS.md` 等全局配置只有在用户表达了跨项目原则时才改。项目专属事实禁止写全局；把它们迁回项目根或 `.codestable/`。
