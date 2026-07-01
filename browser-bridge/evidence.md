# Browser Bridge Evidence

`evidence` 导出渲染后的组件证据。对于 switch、slider、tabs、select、menu、dialog、command input、date picker、chart 等小而细节敏感的组件，仅靠截图不可靠。它会从真实浏览器 tab 中捕获组件结构、样式、尺寸和截图。

## 命令

```bash
python <skill-dir>/scripts/browser.py evidence 'button[role="switch"]' --name Switch --out component-evidence/switch
python <skill-dir>/scripts/browser.py evidence '[data-slot="switch"]' --name Switch --index 0 --depth 4
python <skill-dir>/scripts/browser.py evidence '.tabs-root' --name Tabs --wait '.tabs-root' --wait-ms 8000
```

## 参数

- `--name <name>`：组件名，用于 metadata 和输出目录。
- `--out <dir>`：输出目录，默认 `component-evidence/<name>`。
- `--index <n>`：selector 匹配序号，默认 `0`。
- `--depth <n>`：后代结构深度，默认 `4`。
- `--tab <id>`：指定 tab。
- `--wait <selector>` / `--wait-ms <ms>`：等待 SPA 渲染组件。
- `--all-styles`：捕获全部 computed styles，而不是精简后的 UI 样式集合。

## 输出文件

```text
component-evidence/<name>/
  README.md
  metadata.json
  dom.html
  attributes.json
  class-list.txt
  box-model.json
  computed-styles.json
  anatomy.json
  screenshot.png
  page.png
```

## 使用约束

把这些证据当作组件结构的权威来源。把组件翻译成源码时，保留有意义的 `role`、`aria-*`、`data-state`、`data-size`、`data-slot`、尺寸、transform 和状态类名。

`evidence` 不可用时，先向调用方索取复制出来的 rendered DOM、class list 或源码，再把细节敏感组件标为已验证。
