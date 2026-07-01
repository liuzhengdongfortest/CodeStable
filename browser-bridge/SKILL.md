---
name: browser-bridge
description: 通过 Chrome 扩展控制真实浏览器：打开网页、执行 JS、抽取 DOM、截图和导出组件证据。触发：browser control、web automation、page scraping。
---

# Browser Bridge

Browser Bridge 通过 Chrome 扩展连接真实浏览器，提供结构化的网页操作和抽取能力。它不把整页原始 HTML 直接塞给模型，而是在浏览器里执行 JavaScript，再返回结构化结果、DOM 变化摘要和短暂出现的提示文本。

## 使用定位

Browser Bridge 是一个独立工具型技能。它适合需要真实浏览器状态、扩展能力、登录态页面、DOM 操作、网页抽取、组件证据或截图的任务。

使用前确认三件事：

- Python 依赖和 Chrome 扩展已经安装；首次安装见 `setup.md`。
- `python <skill-dir>/scripts/browser.py tabs` 能看到浏览器 tab。
- 频繁执行命令时，先启动常驻 master，避免每次 CLI 调用都等待扩展重连。

## 架构

```text
CLI (browser.py)  ->  Python (TMWebDriver)  <-WebSocket->  Chrome 扩展  <-CDP/scripting->  浏览器 Tab
```

- Python WebSocket server 运行在 `ws://127.0.0.1:18765`。
- Chrome 扩展连接到 server，并把命令转发给浏览器 tab。
- JavaScript 在页面上下文中执行；如果 CSP 阻止执行，会回退到 CDP。
- 返回结果是结构化 JSON，不是原始 HTML。

## 常用命令

所有命令第一次调用时都会自动启动 bridge server。CLI 位于：

```text
<skill-dir>/scripts/browser.py
```

频繁操作浏览器时，先单独启动常驻 master：

```bash
python <skill-dir>/scripts/browser_master.py
```

已经知道页面结构时，直接用 `exec`，让 DOM diff 告诉你页面变化：

```bash
python <skill-dir>/scripts/browser.py exec "document.querySelector('.submit-btn').click()"
```

只需要 JS 返回值、不需要 DOM diff 和 toast 捕获时，加 `--no-monitor`：

```bash
python <skill-dir>/scripts/browser.py exec --no-monitor "document.title"
```

页面未知时，先用低 token 的扫描：

```bash
python <skill-dir>/scripts/browser.py scan --text-only
python <skill-dir>/scripts/browser.py scan --size-only
```

SPA 或动态内容要等待目标元素：

```bash
python <skill-dir>/scripts/browser.py scan --text-only --wait ".result-card"
python <skill-dir>/scripts/browser.py exec --wait ".loaded" "return document.querySelector('.loaded').textContent"
```

导航、tab 和截图：

```bash
python <skill-dir>/scripts/browser.py tabs
python <skill-dir>/scripts/browser.py navigate "https://example.com"
python <skill-dir>/scripts/browser.py back
python <skill-dir>/scripts/browser.py screenshot page.png
```

组件还原或 UI 证据需要 `evidence`：

```bash
python <skill-dir>/scripts/browser.py evidence '[data-slot="switch"]' --name Switch --out component-evidence/switch
```

完整 CLI 参数、返回字段和命令清单见 `cli.md`；组件证据细节见 `evidence.md`。

## 使用模式

已知页面结构时，优先 `exec`。不要走 `scan -> 检查 HTML -> exec -> scan` 的高 token 循环；只有页面未知时才先 `scan`。

调研、竞品分析、市场研究或未知页面，先 `scan --text-only` 获取概览，再用 `exec` 和定向 selector 抽取结构化数据。深入链接时用 `navigate`，看完用 `back` 返回。

信息密集页面优先 `scan --text-only`；结构化列表和表格优先 `exec "Array.from(...)"`。

## 进一步参考

- `setup.md`：首次安装、扩展加载和连接验证。
- `cli.md`：完整命令、参数和返回字段。
- `evidence.md`：组件证据命令和输出说明。
- `reference.md`：使用模式、SPA 抽取示例、调研速查表和排障。
- `grok.md`：通过 Browser Bridge 操作 `https://grok.com` 的页面结构、输入提交、响应抽取和超时建议。
