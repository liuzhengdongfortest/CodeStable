# EasySDD

> 让 Claude Code 不再每次重启都失忆，也不再一口气写出 800 行你读不懂的代码。

你用 Claude Code 写代码，大概经历过这几件事：给它一个需求，它刷刷写完几百行，你一看——里面起的名字跟你原来代码里的对不上，好几处顺手改了不该动的地方；修一个 bug，现象是没了，但下次遇到类似的问题又得从头查；上周好不容易让它理解的一个项目里的约定，这周新会话里它又忘了。

不是 AI 不行，是你每次都给了它一个空白起点。

**EasySDD 的想法**：开发里反复出现的几类事——加功能、修 bug、把踩过的坑记下来、定一个技术选型、摸一块陌生代码、接手一个新仓库——每一类都配一套固定做法，做完留一份文件。下次再碰到同类的事，AI 和你都能读到上次写的东西，不从零开始。

---

## 为什么是"几类事"而不是一个通用流程

因为不同的事出问题的方式不一样：

- 加新功能的时候，最容易**改着改着改出了范围，或者起的名字跟原来代码里的对不上**
- 修 bug 的时候，最容易"**看着修好了，根本原因还在**"
- 踩的坑不写下来，三周之后的你自己**还会再踩一遍**

一个通用流程要么照顾不全，要么套在每件事上都嫌重。EasySDD 把这些事拆开，每类配一套子技能，各自大小合适。

| 要做的事 | 子技能 | 做完留下的文件 |
|---|---|---|
| 加新功能 | `easysdd-feature` | `design.md` + `acceptance.md` |
| 修 bug | `easysdd-issue` | `report.md` + `analysis.md` + `fix-note.md` |
| 把踩过的坑记下来 | `easysdd-compound` | `learnings/*.md` |
| 写"这种情况这么做"的参考 | `easysdd-tricks` | `tricks/*.md` |
| 定约束、记技术选型 | `easysdd-decisions` | `decisions/*.md` |
| 把一次代码调研存起来 | `easysdd-explore` | `explores/*.md` |
| 写开发者指南 / 用户指南 | `easysdd-guidedoc` | `docs/dev/*.md`、`docs/user/*.md` |
| 写库的 API 参考 | `easysdd-libdoc` | `docs/api/*.md` |
| 检查设计和代码有没有对上 | `easysdd-architecture-check` | 只出检查报告，不存档 |
| 把新仓库接入 EasySDD | `easysdd-onboarding` | `easysdd/` 骨架 |

---

## 一个 feature 流程走下来是什么样

以"加用户登录功能"为例：

1. 你说「做个登录功能」——AI 不会马上写代码，先进 design 阶段，产出一份 `design.md`：里面有个术语表（讲清楚什么叫"用户"、什么叫"会话"，防着跟老代码里的叫法对不上）、接口怎么约定、以及测试里那些"代码上线以后必须永远成立"的条件
2. 你读这份 doc，改到满意，才拍板
3. 进 implement 阶段，AI 按 doc 一步步写——每写完一段停一下让你看，不一口气写完几百行
4. 最后进 acceptance 阶段，对着 doc 核一遍代码真的做到了当初答应的事；然后代码和 doc 一起 commit

最要紧的不是这套流程本身，是**那份 doc 留了下来**——下次谁要改登录模块，能直接读到当时为什么这么设计。

需求特别小的时候可以走 `easysdd-feature-fastforward`——写一份简短方案直接进实现，不做完整的 review。

---

## 装上开始用

EasySDD 是一套 [Claude Code](https://claude.ai/code) 技能集，不需要装别的工具：

```bash
claude skills add liuzhengdongfortest/easysdd
```

在项目里初始化目录：

> 对 Claude 说：「在这个项目里初始化 easysdd」

然后开始第一件事：

> 对 Claude 说：「我要做 X 功能，走 easysdd-feature 流程」
>
> 或者：「这里有个 bug，走 easysdd-issue 流程」

没说清楚用哪个子技能也行，Claude 会从根技能 `easysdd-core` 自己路由到合适的那一个。

---

## 这套东西在赌什么

**一份好方案花 20 分钟写，能省 2 小时的返工和 2 周后的一头雾水。**

每套子流程都尽量短——能快速走完就快速走完，不确定的地方才停下来问你。阶段中间让你看一眼不是走形式，是因为 AI 最容易出事的地方就是一口气写完几百行代码才让你看，等你发现问题想停都停不下来了。

---

## 想看得更深

- 根技能讲解：[`easysdd-core/SKILL.md`](easysdd/SKILL.md)
- 共享约定（目录结构、YAML frontmatter、checklist 怎么用、最后怎么 commit）：[`easysdd-core/reference/shared-conventions.md`](easysdd/reference/shared-conventions.md)
- 项目架构入口：[`easysdd/architecture/DESIGN.md`](easysdd/architecture/DESIGN.md)

---

## License

MIT
