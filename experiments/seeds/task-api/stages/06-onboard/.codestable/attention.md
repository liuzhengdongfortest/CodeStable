# Attention

启动必读（taskhub）：

- 报告语言：中文；代码、命令、路径、字段保持原文。
- 本仓库为精简 onboard：未安装 CodeStable runtime 工具（无 runtime-manifest），
  跳过 runtime 资产恢复，按各 skill 文本流程执行即可。
- 测试命令：`python3 -m pytest tests -q`（提交前必须全绿）。
- 产物目录约定：issue 走 `.codestable/issues/YYYY-MM-DD-{slug}/`，feature 走
  `.codestable/features/YYYY-MM-DD-{slug}/`。
- 陷阱：项目零第三方依赖（仅 stdlib）；不要引入外部包。HTTP 层 JSON 键为
  camelCase，内部字段为 snake_case，改动时保持两侧映射一致。
