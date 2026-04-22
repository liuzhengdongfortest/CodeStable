# cs-roadmap 参考模板

本文件提供 `cs-roadmap` 使用的主文档和 items.yaml 参考格式。SKILL.md 只保留流程骨架，具体格式在这里。

---

## 1. 主文档 `{slug}-roadmap.md`

### 1.1 frontmatter

```yaml
---
doc_type: roadmap
slug: permission-system
status: active          # active | paused | completed
created: YYYY-MM-DD
last_reviewed: YYYY-MM-DD
tags: [permission, auth]
related_requirements: []    # 相关 req slug 列表，可空
related_architecture: []    # 相关 architecture doc slug 列表，可空
---
```

字段说明：

- `status`：`active` 进行中 / `paused` 暂停 / `completed` 所有条目 done 或 dropped
- `related_requirements`：本大需求涉及的 req slug，帮助读者跳转到"为什么要有这个能力"
- `related_architecture`：会被改到的 architecture doc slug，帮助读者理解"改了会触碰到哪些现状"

### 1.2 正文节

```markdown
# {大需求标题——直接说是什么，不玩比喻}

## 1. 背景

一两段讲这块大需求是什么、为什么要做。对象是"新加入这个项目、想知道接下来几个月在忙什么"的人。

## 2. 范围与明确不做

### 本 roadmap 覆盖

- 能力 A
- 能力 B
- 能力 C

### 明确不做（本 roadmap 不覆盖）

- 能力 X（理由）
- 能力 Y（理由或指向另一份 roadmap / req）

## 3. 子 feature 清单

按依赖和推进顺序排列。每条对应 items.yaml 里一个条目，两份保持同步。

1. **{子 feature slug}** — {一句话描述}
   - 依赖：{前置 slug 列表 / 无}
   - 状态：{planned | in-progress | done | dropped}
   - 对应 feature：{YYYY-MM-DD-{slug} / 未启动}
   - 备注：{可选，说明为什么这条排在这里}

2. **{子 feature slug}** — ...

**最小闭环**：第 {N} 条 `{slug}` 做完后，{描述能端到端跑通的最窄路径}。

## 4. 排期思路

一段短的，讲拆分逻辑和优先级判断：

- 为什么这样拆（按模块 / 按用户价值 / 按风险 / 按依赖）
- 第一条为什么选它作为最小闭环
- 中间有没有卡点（需要前置架构改动 / 外部依赖 / 设计决策）

## 5. 观察项

起草或刷新过程中发现、但本 roadmap 不处理的事情，交给用户决定：

- 发现 `codestable/architecture/X.md` 里对 Y 的描述已经过时，建议另起 architecture update
- 发现 requirement-Z 的边界和本 roadmap 第 3 条冲突，建议先对齐 req
- ...

## 6. 变更日志（update 模式才有）

- YYYY-MM-DD：{一句话描述本次改动}
```

---

## 2. items.yaml 格式

```yaml
roadmap: permission-system
created: YYYY-MM-DD

items:
  - slug: permission-rbac-core
    description: 基础 RBAC 模型和数据表，提供角色/权限两张表和最小查询 API
    depends_on: []
    status: planned             # planned | in-progress | done | dropped
    feature: null               # 启动 feature 后填 YYYY-MM-DD-{slug}，未启动写 null
    minimal_loop: true          # 只有一条标 true，即"最小闭环"那条
    notes: null                 # 可选：备注、特殊约束、drop 理由

  - slug: permission-admin-ui
    description: 管理员配置角色和权限的页面
    depends_on: [permission-rbac-core]
    status: planned
    feature: null
    minimal_loop: false
    notes: null
```

### 字段规则

- `slug`：子 feature 的 slug，小写字母 / 数字 / 连字符；将来 feature 目录命名为 `YYYY-MM-DD-{slug}`
- `description`：一句话，能独立讲清楚这条做什么
- `depends_on`：前置 slug 列表。空数组表示无依赖。必须指向同 roadmap 里的其他条目
- `status`：`planned`（未启动）/ `in-progress`（feature 已 design）/ `done`（feature 验收完成）/ `dropped`（确定不做了）
- `feature`：启动后填 feature 目录名（`YYYY-MM-DD-{slug}`），用于 acceptance 反查
- `minimal_loop`：全表只有一条为 `true`，标记"最小闭环"那条
- `notes`：备注。drop 的条目必须在这里写理由

### 状态机

```
planned  → in-progress  （feature-design 启动时由 design 技能改）
in-progress → done      （feature-acceptance 完成时由 acceptance 技能改）
planned  → dropped      （用户决定不做，roadmap update 模式改）
done     （终态）
dropped  （终态，不删除条目，保留历史）
```

**不合法的跃迁**：从 `done` 回 `in-progress`（要改需求回退走新的 feature）；从 `dropped` 回 `planned`（要恢复重新加一条 slug 略改）。

### 校验

```bash
python codestable/tools/validate-yaml.py --file codestable/roadmap/{slug}/{slug}-items.yaml --yaml-only
```

---

## 3. 拆解 checklist（起草时对自己提问）

起草子 feature 清单时逐条问自己：

- [ ] 这条能独立走完一次 feature 流程（design / implement / acceptance）吗？走不通就继续拆或合并
- [ ] 这条做完后能单独验证吗？能不能写出一句"完成后 {具体可观测现象}"
- [ ] 这条的 slug 和 `codestable/features/` 下已有目录冲突吗？grep 过了吗
- [ ] 依赖关系讲得清具体理由吗？"B 需要 A 提供的 {具体产物}" 这种
- [ ] 最小闭环那条真是"最窄的端到端路径"吗？还是只是"最容易的一条"
- [ ] 有没有条目其实应该是 requirement 变化而不是 feature？（比如"把 XX 能力的边界改一下"）那种转 `cs-req`

---

## 4. review 提示

> roadmap 已起草完成，请整体 review：
> 1. 拆解粒度合不合适？每条是不是都能独立做成一个 feature？
> 2. 依赖关系对吗？有没有漏的前置或多余的依赖？
> 3. 最小闭环选得对吗？第一条做完真能端到端演示点什么吗？
> 4. "明确不做"有没有遗漏？有没有你其实想做但被我漏掉的？
> 5. 排期顺序符合你的产品优先级吗？
>
> 有修改意见直接说，确认后我落盘 roadmap 目录和 items.yaml。
