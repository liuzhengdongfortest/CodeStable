# Behavioral Verification Contract

本契约只在进入独立 QA 或 Standard accept-inline 时加载。它从用户、调用方或测试人员视角验证候选版本的可观察行为，不审查实现结构或代码质量。

## 输入投影

默认只消费：

- design 第 3 节的行为场景、必跑验证与明确的条件性非阻塞边界；
- checklist 中与行为或交付结果有关的 checks；
- code review 的 `status`、当前 round/scope、`Test And QA Focus` 和 `Residual Risk`；
- 项目已有的用户入口和测试入口，例如命令、API、页面、集成测试或 E2E；
- Goal 模式的 evidence pack 状态、核心证据和 residual-risk 投影。

默认不消费实现源码、完整 diff、implementation 汇报、完整 review narrative 或完整成功日志。`git status --short` 只用于候选范围和 freshness preflight，不用于推断实现正确性。evidence pack 投影为 passed 且无 warning/mismatch 时，不同时展开 raw DoD / gate JSON。

## 验证矩阵

每条矩阵项都必须包含：

| 字段 | 要求 |
|---|---|
| ID / source | 可回指 design 场景、check 或 review risk |
| action | 用户/API/CLI/browser/E2E/test runner 实际执行的动作 |
| expected | 外部可观察的结果或失败语义 |
| evidence kind | 功能、integration、E2E、browser、API、CLI、manual 或合适的 contract test |
| result | pass / fail / blocked |
| evidence locator | 命令与 exit code、测试用例、请求响应、截图或简短观察；不复制完整成功输出 |

先覆盖 core behavior，再补 supporting behavior。功能或 mixed feature 至少有一种能穿过真实入口的行为证据；unit 可支撑边界，但不能用 typecheck / lint / build 代替运行行为。typecheck / lint / build 是 supporting evidence，不能单独证明功能行为。

非功能性 feature 仍从消费者角度验证其契约结果，例如 CLI 输出、schema/快照、package 内容、runtime sync 或文档链接可解析；不以逐文件 diff 复核冒充 QA。纯 human document 且没有可运行承诺时，可以记录无需独立 QA，由 acceptance 核对交付内容。

## 执行顺序

1. 运行最小、最接近用户入口的 core 场景。
2. 运行与失败语义、边界值、集成点有关的 supporting 场景。
3. 覆盖 review 投影里的 QA focus 和 residual risk。
4. 再运行必要的 supporting build/type/lint gate；它们不能抬高缺失的 core behavior 证据。
5. 只保存结果摘要和 evidence locator；长日志保留在原 runner/终端，失败时截取复现所需片段。

优先使用项目现有测试框架和入口。QA 不为验证临时引入框架，也不直接修改测试、配置或实现；需要变更时写 finding 并走现有 qa-fix -> code review -> QA/accept-inline 顺序。

## Verdict 与诊断

- 观察行为与 design 期望不符，或核心行为没有可执行证据且原因属于实现/测试缺口：`failed`。
- 环境、凭证、设备、输入或可观察判据不足，导致核心行为无法执行或判定：`blocked`。
- 核心和阻塞场景均有行为证据且通过：`passed`。
- residual risk 只承载非核心、已明确延期或 design 预先定义的条件性边界，不能承载未运行的核心行为。

只在失败或 blocked 的诊断分支，按 finding 范围读取相关日志、fixture、配置或代码；目的是定位复现条件和归因，不是重新做代码审查。诊断结论仍写成“动作 / 期望 / 观察 / 复现”，不输出逐文件质量 finding。

代码风格、TODO/FIXME、unused import、dead code、架构与可维护性不属于 behavioral verification。它们由 code review、DoD cleanliness 和 acceptance final audit 负责。

## 输出投影

- Goal / 显式独立 QA：写既有 `{slug}-qa.md`。passed 只保存 feature type、core gate、矩阵结果/evidence locator、open findings/residual risk 和 verdict；failed/blocked 保存完整复现细节。
- Standard accept-inline：把同一矩阵和 verdict 直接写入 acceptance 第 3 节与最终审计，不创建 `{slug}-qa.md`。
- 任一路径发现 review round/scope 无法证明覆盖当前候选时，在 terminal QA receipt 或 inline verdict 前返回 `cs-code-review`，不新增 QA status、block kind 或 freshness digest。
