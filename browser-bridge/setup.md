# Browser Bridge Setup

## 安装依赖

首次使用前安装依赖：

```bash
pip install bs4 simple-websocket-server bottle requests
```

## 安装 Chrome 扩展

1. 打开 Chrome 的 `chrome://extensions/`。
2. 启用 "Developer mode / 开发者模式"。
3. 点击 "Load unpacked / 加载已解压的扩展程序"，选择 `<skill-dir>/assets/extension/`。
4. 打开任意网页验证：右下角应看到绿色的 `ljq_driver: connected` 标记。

## 验证连接

```bash
python <skill-dir>/scripts/browser.py tabs
```

如果能看到浏览器 tab，说明扩展已经连上本地 bridge server。
