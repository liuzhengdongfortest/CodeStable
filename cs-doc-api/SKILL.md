---
name: cs-doc-api
description: 给库的公开表面（组件 / 函数 / 命令）逐条目生成参考文档，带清单追踪，支持单条目和批量。信息源是源码本身（与 doc-tutorial 任务导向不同）。触发：用户说"写 API 文档"、"组件文档"、"doc-api"，或收尾发现新增公开接口。
---

# cs-doc-api

遵循 `.codestable/convention.md`。

doc-tutorial 教"怎么用 X 做 Y"，doc-api 告诉你"X 每个零件长什么样、怎么配"。doc-api 写错就是错——信息源是源码，类型 / 默认值 / 签名都有唯一答案。**核心：不靠猜、不复制改名、每个条目独立读源码。**

## 条目粒度

| 项目类型 | 一个条目 |
|---|---|
| UI 组件库 | 一个组件 |
| 工具函数库 | 一个模块 / 函数族 |
| API Client | 一个 endpoint 族 |
| CLI | 一个子命令 |

初始化定下粒度后保持一致——变来变去清单和搜索都会乱。

## 路径

产物**不在 `.codestable/` 下**：条目 `docs/api/{slug}.md`，清单 `docs/api/manifest.yaml`。项目有别的约定从项目。manifest 格式 / 条目模板 / 源码提取清单见 `reference.md`。

## 工作流

**Phase 1 初始化**：确认类型 + 粒度 + 路径 → 扫源码识别公开导出分组 → 生成 manifest.yaml（全 `pending`，`validate-yaml.py` 校验）→ 用户确认范围（可标 `skipped`）

**Phase 2 生成**

- *单条目*（1-3 个或试跑）：读源码 → 按模板生成 → review → 落盘校验 → manifest 标 `current`
- *批量*（大量 pending）：① 先出 2-3 个代表样板（`draft`）② 用户确认风格（**不可跳**，否则全白写）③ 剩余逐条读源码生成（可 subagent 并行，`draft`）④ 整体 review + 批量校验 ⑤ 确认后一起转 `current`

**Phase 3 增量**：代码变后——`search-yaml.py` 搜 `outdated` / 对比 `last_scanned` 后变更文件 / 按最久没复核排序 → 重读源码增量更新 → 校验 → `current` + `last_reviewed`

**批量硬规则**：每条独立读源码不复制改名（相似接口常有微妙差异）；样板确认不可跳；动态导出 / 代码生成标 `skipped` 加 note（硬猜的文档比没有更害）。

## 退出条件

- Phase 1：manifest 落盘 + 范围确认（含 skipped 理由）
- Phase 2：frontmatter 完整 + API 节来自源码提取非编造 + 批量样板已确认 + manifest status 同步
- Phase 3：outdated 全更新或确认暂缓

## 坑

- 没读源码就写（核心价值是准确反映源码）
- 复制上一个改名（漏微妙差异）
- 批量跳样板确认（全白写）
- 把 spec 信息写进 doc-api（不变量 / 测试约束 → context）
- manifest 直接删行（改 `status: skipped` + note）
- 源码没有的接口写进文档（以源码为事实源）
