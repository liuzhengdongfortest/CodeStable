# 重构方法库：Architecture Deepening

本文件承接 `methods.md` 的 L3 结构拆分方法，专放 deep-module / seam / interface 相关方法。方法号继续使用 `M-L3-NN`，但不塞回 `methods.md`，避免单文件超过 300 行。

## L3 Architecture Deepening

### M-L3-08 Deepen Module 深化模块

- **适用**：多个 callers 需要理解同一组内部步骤；当前 module interface 几乎和 implementation 一样复杂；测试必须拼内部 helper 才能覆盖真实行为
- **不适用**：只是想换命名 / 分文件；复杂度没有散到 callers；会改变外部可观察行为
- **步骤**：
  1. 列出 callers 必须知道的 internal facts（invariant / ordering / error mode / config）
  2. 设计一个更小的 interface，把这些 facts 收进 module implementation
  3. 用 Parallel Change（M-L1-01）迁移 callers，必要时保留旧 interface 过渡
  4. 在新 interface 上补 characterization / integration-style tests
  5. grep 确认 callers 不再依赖内部 helper / 内部状态
- **风险点**：interface 设计过大变成新 shallow module；迁移期间新旧路径行为不一致
- **验证**：新旧行为测试一致；caller 只依赖目标 interface；旧 internal imports / helper calls 归零
- **前后端**：通用
- **配哪种 scan 项**：shallow module / locality 缺失 / 测试越过 interface

### M-L3-09 Move Seam 移动接缝

- **适用**：当前 seam 放错位置，导致 caller 知道 transport、存储、第三方 client 或内部编排细节
- **不适用**：只有一个实现且没有测试替身 / 生产替换需求；移动 seam 会改变公开契约
- **步骤**：
  1. 标出 seam 泄漏的 facts：哪些 caller 被迫知道内部细节
  2. 选择新 seam，让 caller 和 tests 都穿过同一个 interface
  3. 若跨远程或第三方依赖，定义 port；production adapter 和 test adapter 同时成立才引入 adapter
  4. 逐个迁移 caller，删除旧 seam 上的泄漏依赖
- **风险点**：只有一个 adapter 的假 seam；把业务语义泄漏进 transport adapter
- **验证**：tests 通过新 seam 断言 observable outcome；旧 transport / storage 细节不再出现在 callers
- **前后端**：通用
- **配哪种 scan 项**：seam 泄漏 / 假 boundary / caller 依赖内部实现

### M-L3-10 Collapse Shallow Wrappers 折叠浅包装

- **适用**：一串 wrapper / helper 只转发参数或改名，interface surface 几乎等于 implementation；删除它们不会让复杂度回到 callers
- **不适用**：wrapper 承载稳定领域语义、权限检查、缓存、重试、观测或多 adapter 切换
- **步骤**：
  1. 列出 wrapper 链和每层实际增加的行为
  2. 保留真正承载语义的一层，把纯 pass-through 层 inline 或移动到 deep module 内部
  3. 更新 imports / 调用点，删除空壳 wrapper
  4. grep wrapper 名称和路径确认无残留
- **风险点**：误删未来扩展点；inline 后 caller 暴露过多 implementation detail
- **验证**：行为测试通过；被删除 wrapper 0 引用；callers 没有新增 internal dependency
- **前后端**：通用
- **配哪种 scan 项**：pass-through module / wrapper chain / shallow abstraction

### M-L3-11 Replace Layered Tests with Interface Tests 替换分层测试

- **适用**：测试散在多个 shallow helper 上，重构内部实现就大量失败；真实 bug 出现在 helpers 如何组合而不是单个 helper 内
- **不适用**：helper 本身是稳定公共 interface；缺少能观察行为的上层 interface
- **步骤**：
  1. 找出当前测试绑定的 internal helper / call order / private state
  2. 在目标 module interface 上写 characterization tests，覆盖同一 observable behavior
  3. 确认新测试先能保护当前行为，再删除或降级旧 internal tests
  4. 后续结构调整只保留 interface-level tests 作为行为等价证据
- **风险点**：删除测试过早导致覆盖缺口；新 interface test 太粗，漏掉关键边界
- **验证**：关键行为仍有测试覆盖；旧 internal tests 删除后整体 suite 仍能在行为破坏时失败
- **前后端**：通用
- **配哪种 scan 项**：tests 越过 interface / testability 差 / 重构被内部测试绑死
