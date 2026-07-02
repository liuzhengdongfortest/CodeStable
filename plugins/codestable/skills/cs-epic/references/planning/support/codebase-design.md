# Roadmap 内嵌 Codebase Design 检查

本文件是 `cs-epic` planning 阶段的内嵌架构规划检查清单，只用于补强 roadmap 第 3 节模块拆分和第 4 节接口契约。

## 什么时候用

当前 roadmap 涉及以下任一情况时使用：

- 拆出多个 module / 子系统。
- 定义跨模块 interface、共享协议、事件、数据结构或远程调用。
- 计划引入 port / adapter / test double。
- 多个子 feature 会共同遵守同一接口契约。

无跨模块接口时，在第 4 节明确写"本 roadmap 无跨模块接口"，本检查标不适用。

## 模块拆分检查

每个 module 至少回答：

- 职责：它做什么、不做什么。
- Interface：其他 module / feature 必须知道什么才能使用它。
- Depth：它是否把足够多行为藏在小 interface 背后。
- Locality：后续变化和 bug 是否会集中在它内部。
- Deletion test：删掉它后，复杂度会回到多个 callers，还是只是少一层透传。

避免两类拆分：

- **Pass-through module**：只转发调用，没有隐藏复杂度。
- **万能 module**：职责太宽，所有后续 feature 都往里塞。

## 接口契约检查

每个跨模块接口除签名 / 字段 / 错误码外，还要写：

- Interface facts：invariant、ordering、error mode、required configuration、performance constraint。
- Seam placement：seam 放在哪里，为什么 caller 和测试都应穿过这里。
- Dependency strategy：in-process / local-substitutable / remote-owned / true external。
- Adapter：是否有 production + test 两种 adapter；如果只有一个 adapter，说明为什么不是假 seam。
- Test surface：后续 feature-design 应通过哪个 interface 证明行为。

## Dependency strategy

- **in-process**：纯计算或内存状态。优先做 deep module，不引入 adapter。
- **local-substitutable**：有本地替身的依赖，如测试数据库 / in-memory filesystem。测试穿过 module interface。
- **remote-owned**：自有远程服务。在 seam 定义 port，production 用 HTTP/gRPC/queue adapter，测试用 in-memory adapter。
- **true external**：第三方服务。作为 injected port 处理，测试用 mock adapter。

## Design It Twice 触发

如果第 4 节接口会长期约束多个 feature，或者 seam placement 不明显，roadmap 起草时至少比较 2 个候选接口：

- 一个最小 interface：1-3 个入口，最大化 leverage。
- 一个偏扩展 interface：支持更多未来用例。
- 一个偏常见 caller interface：让默认路径最简单。

比较维度固定为 depth、locality、seam placement、dependency strategy。选定方案后，只把 winner 写成正式契约；其余方案可放观察项，不进入 items.yaml。
