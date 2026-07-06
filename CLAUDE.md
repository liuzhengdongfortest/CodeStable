# Claude Rules

## 核心原则

言简意赅。先读仓库事实、现有 skill 文档和 ADR，再修改规则；只把可复用且能验证的做法写进规则文件。

## 语言与文档

- 默认用中文写面向人的回复、报告和文档；代码、命令、路径、协议字段、YAML/JSON key 保持原格式。
- 单个 Markdown 文件不得超过 300 行；超过必须拆分。
- 增加或更新 skill 时，同步检查相关 skill、README/reference、测试和 ADR 中的表述。
- `AGENTS.md`/`CLAUDE.md` 只写 agent 行为规则；不要替代 `.codestable/attention.md`、design、checklist、ADR 等项目事实载体。

## Skill 边界

- 不同 skill 之间不要相互耦合；A skill 在非必须情况下不要读取或依赖 B skill 的内部文件。
- skill 是独立安装单元，运行时每个 skill 只能稳定看到自己包内文件；不要在 SKILL.md 中写 `B-skill/reference/xxx.md` 这类 sibling 引用。
- 跨 skill 共享的参考文档必须走项目层：由 `cs-onboard` 复制到项目 `.codestable/reference/`，其他 skill 用项目相对路径 `.codestable/reference/xxx.md` 读取。
- 要改共享口径时，改 `plugins/codestable/skills/cs-onboard/references/` 下的模板，并同步项目副本、相关 skill 文案和测试。

## CodeStable Runtime

- 新版 CodeStable 工具、gate、doctor、workflow-next、DoD runner 等入口必须从 `<cs-onboard skill 目录>/tools/` 调用。
- 不要新增 `python .codestable/tools/...` 作为新版入口；`.codestable/tools/` 只作 legacy compatibility。
- 保留老项目里的 `.codestable/tools/`、旧 worktree/branch 文档或 hooks；除非用户明确要求，不要默认删除或覆盖。
- CodeStable skills 不拥有默认 worktree/branch 策略；是否创建 worktree、如何命名分支、如何 merge，应由宿主、owner 或未来独立 skill 决定。

## 验证

- skill/runtime 改动完成前至少运行相关 pytest 与 `git diff --check`。
- runtime sync 或 health 行为变化时，运行 `codestable-runtime-sync.py --check --json`，确认 `tool_runtime: skill-global`、managed paths 和 missing paths 符合预期。
