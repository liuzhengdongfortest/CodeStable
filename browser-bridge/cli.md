# Browser Bridge CLI

完整 CLI 位于：

```text
<skill-dir>/scripts/browser.py
```

下面的 `<skill-dir>` 指包含 `SKILL.md` 的目录。

## 常驻 master

如果直接反复调用 `browser.py exec ...`，每个短命 CLI 进程都可能重新启动 bridge server，并等待 Chrome 扩展重连，通常会多出数秒冷启动时间。频繁操作浏览器时，先单独启动：

```bash
python <skill-dir>/scripts/browser_master.py
```

保持这个进程运行。之后正常使用 `browser.py exec`、`scan`、`tabs` 等命令，它们会自动通过 `http://127.0.0.1:18766/link` 转发到常驻 master。

只需要 JS 返回值、不需要 DOM diff 和 toast 捕获时，给 `exec` 加 `--no-monitor`：

```bash
python <skill-dir>/scripts/browser.py exec --no-monitor "document.title"
```

## exec

在浏览器里执行 JavaScript。直接写 JavaScript 查询或操作 DOM。系统会捕获返回值、DOM 变化和执行期间出现的短暂文本，例如 toast、通知、loading 文案。

```bash
python <skill-dir>/scripts/browser.py exec "<javascript>"
```

参数：

- `--tab <id>`：指定 tab。
- `--no-monitor`：跳过 DOM diff，更快。
- `--wait <selector>`：执行前等待 CSS selector 出现，适合 SPA。
- `--wait-ms <ms>`：`--wait` 的最长等待时间，默认 `10000`。
- `--timeout <s>`：执行超时秒数，默认 `15`。

示例：

```bash
python <skill-dir>/scripts/browser.py exec "document.title"
python <skill-dir>/scripts/browser.py exec "document.querySelector('.submit-btn').click()"
python <skill-dir>/scripts/browser.py exec "Array.from(document.querySelectorAll('.item')).map(e=>({name:e.querySelector('.name')?.textContent,price:e.querySelector('.price')?.textContent}))"
python <skill-dir>/scripts/browser.py exec "const e=document.querySelector('#email');e.value='u@x.com';e.dispatchEvent(new Event('input',{bubbles:true}))"
python <skill-dir>/scripts/browser.py exec "window.scrollBy(0,800)"
python <skill-dir>/scripts/browser.py exec --wait ".loaded" "return document.querySelector('.loaded').textContent"
python <skill-dir>/scripts/browser.py exec --timeout 30 "await fetch('/api/slow'); return 'done'"
```

返回字段：

- `status`：`success` 或 `failed`。
- `js_return`：JavaScript 返回值；DOM 元素会被智能处理成 `outerHTML`。
- `diff`：DOM 变化摘要，说明哪些元素出现或改变。
- `transients`：执行期间短暂出现的文本，例如 toast 或 loading。
- `newTabs`：执行期间打开的新 tab。
- `tab_id`：执行所在 tab ID。
- `error`：失败时的错误信息。
- `reloaded`：执行期间页面是否发生 reload。
- `suggestion`：页面无明显变化时给出的提示。

## scan

获取简化后的页面内容。HTML 会经过空间和语义简化：移除 sidebar、浮动广告、被遮挡元素、不可见内容；重复列表截断到 3 项；删除非语义属性。

```bash
python <skill-dir>/scripts/browser.py scan
python <skill-dir>/scripts/browser.py scan --tabs-only
python <skill-dir>/scripts/browser.py scan --text-only
python <skill-dir>/scripts/browser.py scan --size-only
python <skill-dir>/scripts/browser.py scan --tab <id>
python <skill-dir>/scripts/browser.py scan --wait ".result-card"
```

返回字段：

- `status`：`success` 或 `error`。
- `html`：简化 HTML；`tabs-only` 或 `size-only` 时不会返回。
- `url` / `tab_id`：当前 tab 信息。
- `sessions`：所有 tab 的 id、url、title 列表。
- `size`：内容字符数，仅 `size-only` 返回。
- `msg`：失败时的错误信息。

## tab 和导航

列出所有浏览器 tab：

```bash
python <skill-dir>/scripts/browser.py tabs
```

打开 URL：

```bash
python <skill-dir>/scripts/browser.py navigate "https://example.com"
python <skill-dir>/scripts/browser.py navigate "https://example.com" --no-wait
```

后退、前进、重载：

```bash
python <skill-dir>/scripts/browser.py back
python <skill-dir>/scripts/browser.py forward
python <skill-dir>/scripts/browser.py reload
```

打开、关闭、切换 tab：

```bash
python <skill-dir>/scripts/browser.py newtab
python <skill-dir>/scripts/browser.py newtab "https://example.com"
python <skill-dir>/scripts/browser.py close
python <skill-dir>/scripts/browser.py close <tab_id>
python <skill-dir>/scripts/browser.py switch "github"
```

多个 tab 同时匹配时，默认选择第一个。需要精确选择时，先用 `tabs` 查看所有 tab 的 ID。

## screenshot

通过 Chrome DevTools Protocol 截取当前 tab 的 PNG 图。

```bash
python <skill-dir>/scripts/browser.py screenshot
python <skill-dir>/scripts/browser.py screenshot page.png
```

返回：

```json
{"status":"success","filepath":"/tmp/screenshot_1714650000.png"}
```

## evidence

导出渲染后的组件证据。对于 switch、slider、tabs、select、menu、dialog、command input、date picker、chart 等小而细节敏感的组件，仅靠截图不可靠。`evidence` 会从真实浏览器 tab 中捕获渲染后的组件结构。

```bash
python <skill-dir>/scripts/browser.py evidence 'button[role="switch"]' --name Switch --out component-evidence/switch
python <skill-dir>/scripts/browser.py evidence '[data-slot="switch"]' --name Switch --index 0 --depth 4
python <skill-dir>/scripts/browser.py evidence '.tabs-root' --name Tabs --wait '.tabs-root' --wait-ms 8000
```

完整参数、输出文件和使用约束见 `evidence.md`。
