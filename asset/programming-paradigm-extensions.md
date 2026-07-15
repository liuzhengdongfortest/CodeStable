# 编程通用范式：扩展模型与参数设计

> [返回核心模型](programming-paradigm.md) · [继续阅读编写与重构规则](programming-paradigm-practices.md)

## 第二部分：扩展模型

### 5. 按注册发现，不按分支选择

当系统需要支持多个可选功能（插件、特性开关、商业分级）时：

```
// ❌ 分支选择：调用点知道所有实现，改一个加一个都要改调用点
if feature == "A": do_a()
elif feature == "B": do_b()
elif feature == "C": do_c()

// ✅ 注册发现：调用点只知道契约，实现自己注册进来
for feature in registry.discover(FeatureContract):
    if feature.enabled():
        feature.apply(ctx)
```

核心转变：**"要不要做"的判断从调用点移到注册点**。调用点只剩遍历，没有分支。功能增减靠改注册表（配置文件、目录扫描、包管理），不靠改代码。

不同语言的注册机制不同，但原理一致：
- Java：ServiceLoader / Spring Bean
- Rust：trait object + inventory crate / 编译期 feature flag
- Python：entry_points / 插件目录扫描
- TypeScript：依赖注入容器 / 动态 import
- Go：init() 注册 + 全局 registry map

### 6. 契约 + 缺省行为

可选功能的契约（接口/trait/protocol）应该提供**有意义的缺省行为**，而不是强制所有实现者处理每一个方法。

```
trait OrderFeature:
    fn apply(ctx)              // 必须实现
    fn enabled() -> bool:      // 缺省：启用
        return true
    fn order() -> int:         // 缺省：居中
        return 100
```

这使得：
- 新增一个特性只需实现核心方法，其余走缺省
- 关闭特性时用缺省的空实现顶替（Null Object），调用代码不改

**Null Object 原则：缺席也是一种存在。** 当一个功能被裁剪时，不是"不调用它"，而是"调用一个什么都不做的实现"。这让编排层永远保持一致的结构。

### 6.1 契约的稳定性设计

注册机制的稳定性完全取决于契约（接口/trait/protocol）的稳定性。接口的稳定性不靠"不变"来保证，靠**"变了也不破坏"**来保证。

**接口变化的三种情况及应对**：

| 变化类型 | 应对手段 | 风险 |
|----------|----------|------|
| 加新方法 | 给缺省实现，老注册者不受影响 | 低 |
| 改现有方法签名 | 接口定"厚"了，需要重新审视抽象 | 高 |
| 接口职责变了 | 版本化接口 + 适配器 | 高，但可控 |

**接口厚度的谱系**：

接口参数越具体，越容易因业务演化而变：

```
最厚（最容易变）
│  fn score(order, customer, rules) -> RiskScore     // 参数多且具体
│  fn apply(ctx: &mut OrderCtx)                      // 只依赖一个 Context
│  fn handle(event: Event) -> Vec<Event>             // 事件驱动，最松耦合
最薄（最不容易变）
```

**核心原则：接口的参数应该是"稳定的名词"，不是"易变的结构"。**

**三个稳定性挡板**：

1. **新方法给缺省实现**——加方法永远不破坏现有注册者
2. **Context 设扩展区**——核心字段强类型，新增字段走扩展区（如 HashMap），等稳定后再提升为核心字段
3. **大版本变更用适配器**——老实现通过适配器在新接口上运行，新老共存

```
// Context 扩展区示例（伪代码）
struct OrderCtx:
    order: Order              // 核心字段，稳定
    customer: Customer        // 核心字段，稳定
    extensions: Map<String, Any>  // 扩展区，新字段先落在这里

    fn get_ext<T>(key) -> Option<T>
    fn set_ext<T>(key, val)
```

**选型指导**：

| 场景 | 推荐方案 |
|------|----------|
| 团队内部、变化可控 | 方法接口 + Context（含扩展区） |
| 跨团队/跨组织插件 | 版本化接口 + 适配器 |
| 高度动态、无法预知未来 | 事件/消息契约 |

**不要为了还没发生的变化提前设计兼容层**——大多数项目从"方法接口 + Context 扩展区"开始就够了。需要插件体系时再引入版本化接口或事件契约。

### 7. 编排层的 Workflow 拓扑

当业务流程超出线性 pipeline（需要分支、并行、汇合）时，拓扑需要升级：

| 复杂度 | 拓扑模型 | 适用场景 |
|--------|----------|----------|
| 顺序 | Pipeline（列表遍历） | 步骤固定、无条件分支 |
| 分支 | Router（路由表/条件边） | 有 if/else 但无并行 |
| 并行 | DAG（有向无环图） | 多条支线可同时执行 |
| 循环 | 状态机 | 审批打回、重试、长等待 |

**拓扑结构本身应该是数据，不是控制流。** 分支是图的属性，不是代码里的 if/else。这样拓扑可以被配置、可视化、动态修改。

但要注意：**当分支逻辑简单时（2-3 个 if），直接写代码比建图清晰**。不要为了架构正确性牺牲可读性——5 行 if/else 好过 200 行图引擎。

---

## 第三部分：参数设计

### 8. 参数打包的判断框架

函数参数是散着传还是打包成结构体/对象，不应由参数个数决定，而由以下维度判断：

**维度一：概念内聚性（最重要）**

这些参数是不是"一件事"的不同侧面？如果它们总是一起出现、一起变化（Data Clump），就该打包。

```
// 2 个参数但概念上是整体 → 该打包
fn ship(address: String, zip: String)     // ❌
fn ship(address: Address)                 // ✅

// 5 个参数但各自独立 → 不用打包
fn transfer(from: Account, to: Account, amount: Money, reason: String, when: Instant)  // ✅
```

**维度二：一致性约束**

参数之间有约束关系（from < to、lat/lng 配对）→ 必须封装，否则约束泄漏到所有调用者。

**维度三：抽象层级一致**

参数应在同一抽象层级。高层概念和低层细节并存时，细节该被封装进高层结构。

**维度四：变化频率**

同一个函数签名改过 3 次参数 → 这里需要一个结构体。

**数字参考（启发式）**：
- 1-3 个：散着传，除非概念上强内聚
- 4-5 个：检查有无 Data Clump
- 6+：几乎肯定有东西该打包
- 10+：函数职责可能过重

### 9. 值对象先行

从需求中提取类型时，**值对象（Value Object）比实体（Entity）更优先**。

- **实体**：有唯一标识、有生命周期、会被修改（Order, User, Account）
- **值对象**：无 ID、表达度量或描述、不可变（Money, Address, TimeRange, Email）

值对象是消除参数散乱的第一工具——它们把原本散着传的基本类型打包成有语义的整体，带上自己的校验规则和行为。

```
// 散着传：调用者必须自己确保 amount > 0 且 currency 合法
fn charge(amount: f64, currency: String)

// 值对象：Money 的构造函数保证了合法性
fn charge(amount: Money)
```

---
