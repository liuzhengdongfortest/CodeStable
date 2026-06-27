---
name: cs-onboard
description: 把仓库接入 CodeStable——搭骨架 + 分发共享资产 + 选变更轴载体（GitHub / 本地）+ 归旧档。两条路径自动判断：空仓库从零搭，已有文档走审计 + 迁移。触发："在这个项目用 CodeStable"、"初始化 / 迁移 CodeStable"。
---

# cs-onboard

把仓库接入 CodeStable 工作流：**搭骨架、分发共享资产、选载体、归旧档**。骨架好了子技能即可运行。本技能只搭环境，不开始干活。

## 启动先扫一次自动判断

不让用户选路径（TA 多半不知道现有哪些文档）。扫：

1. `.codestable/` 在不在 → 不在 = 空仓库；在但不全 = 迁移补齐
2. 旧版目录（`easysdd` / 旧 codestable）→ 提示 `git mv` 到 `.codestable/`，结构兼容
3. Glob 全仓 `.md`（排除 `node_modules/` `.git/`）找零散 spec（`DESIGN/ARCHITECTURE/SPEC/README`、`docs/`）
4. 汇报扫描结论 + 走哪条路径 + 不确定项

迁移详步（审计表 / 逐条对齐 / 处理已有 `.codestable/`）见 `reference.md`。

## 选变更轴载体（onboard 必问一次）

变更轴（issue / epic）落在哪由用户定，写进 `attention.md` 顶部 `载体` 字段：

- `github`：issue / epic 用 GitHub 原生实体；需 `gh` 可用 + 仓库有 remote。**不建**本地 `issues/ epics/`
- `local`：建 `.codestable/{issues,epics}/`，用 md spec + frontmatter status

cs-issue / cs-epic / cs-audit 启动读这字段决定产出形态。

## 标准骨架

```
.codestable/
├── attention.md       启动必读 + 载体字段（最小骨架，实质内容用户后续 cs-note 补）
├── convention.md      体系共识（从技能包分发，勿手改）
├── context/           现状轴（CONTEXT.md / 取舍说明由 cs-context lazy 建）
├── compound/          沉淀（cs-keep）
├── issues/ epics/     仅 local 载体模式建
├── tools/             共享脚本（分发）
└── reference/         共享参考（分发）
```

`context/` 下的 CONTEXT.md / 取舍说明不在骨架里——交给 `cs-context` 首次需要时 lazy 创建。

## 分发共享资产（onboard 唯一强制覆盖）

`convention.md` / `tools/` / `reference/` 是技能包维护的资产，权威源在 `cs-onboard/`，项目里只是副本。**一律 shell 整体覆盖，不要 Read+Write**（会截断 / 改缩进 / 费 token）：

```bash
cp -f  <pkg>/cs-onboard/reference/convention.md  .codestable/convention.md
cp -rf <pkg>/cs-onboard/tools/.                  .codestable/tools/
cp -rf <pkg>/cs-onboard/reference/.              .codestable/reference/
```

覆盖前汇报被覆盖文件；用户明说"我改过请保留"才例外。其他已有文件遵守"不经确认不动"。`<pkg>` 一般是 skill 安装目录，不确定先 `ls` 定位；拷完 `ls` 验证。

## 退出条件

通用骨架见 convention，另加：

- [ ] `context / compound / tools / reference` 存在；local 载体则 `issues / epics` 也在
- [ ] `attention.md` 已建且含 `载体` 字段
- [ ] `convention.md` / `tools/` / `reference/` 已从技能包分发
- [ ] 迁移：每条映射有处理结果，没未经确认就动的文件
- [ ] 验收汇报已给

## 容易踩的坑

- 未确认就移动 / 删除已有文件——迁移核心是用户拍板
- 替用户填 attention.md 实质内容——只给模板
- 重新引入 `AGENTS.md` / `CLAUDE.md` 入口——固定 `.codestable/attention.md`
- 建完骨架立刻开干——onboard 是搭环境
- 共享资产走"不覆盖"保守策略——这三样**必须**覆盖，否则停留旧口径
- Glob 忘了排除 `node_modules/` `.git/`
