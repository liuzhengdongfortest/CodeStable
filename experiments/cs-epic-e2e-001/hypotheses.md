# Hypotheses — cs-epic-e2e-001（拆解覆盖度，预注册于任何运行前）

## 背景
cs-issue/cs-feat 的 outcome 评测显示：现代模型在合成任务上实现/修复能力天花板，skill 可测增益在过程契约。cs-epic 的独特价值主张是**大需求拆解的系统级完整性**——本实验测：给大需求，cs-epic 的系统化拆解流程能否比裸 agent 减少"漏掉整个子系统"。这是 e2e 系列首个**最可能在结果层出现正增益**的实验（大需求认知负荷高，裸 agent 更易漏边角子系统）。

## 评测
生成型（api harness 产 roadmap 文本，不跑真仓库）。3 个 taskhub 大需求（e01 通知/e02 审计权限/e03 批量迁移），各 7 条必需子任务（4 obvious + 3 edge）。双向自证：资深拆解 7/7、草率拆解 4/7（漏全部 edge）。baseline=cs-epic vs bare=通用工程师一句指令。planted_defect（token recall，measured 下界；预检自匹配 1.0、判别 0.57 验锚健康）+ recall_judge（opus 独立 judge，语义主判）。sonnet+haiku × k3 = 9/格。inject_context 提供 taskhub 现状。

## H4（主假设）
baseline 覆盖率 > bare，**增益集中在 edge 项**（obvious 两组预计天花板，edge 是判别面）。分析必须按 fixture `_meta` 的 obvious/edge 标注**拆开算 recall**——总 recall 会被 obvious 天花板稀释。若 edge 覆盖 baseline 显著 > bare → design/planning 的系统化拆解真减少漏项（结果层正增益）。

## 诚实 caveats
1. 出题者偏差：edge 项 = 出题者认知的"该想到但易漏"边界，可能利于系统化流程。L2 对照对两组同等作用，相对差仍有效。
2. planted_defect token 匹配脆——recall_judge（opus）为语义主判，两者背离时以 judge 为准并记录。
3. 生成型只测"拆解方案文本覆盖"，不测拆解可执行性/依赖正确性（后者需全程 e2e，路 B/P3）。
4. n=3×k3=9/格，[underpowered]；跨 2 模型 × 3 需求聚合到可用功效。
