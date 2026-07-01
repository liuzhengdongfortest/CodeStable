# Feature Design 内嵌 Codebase Design 检查

这份 reference 是 `cs-feat-design` 的内嵌设计检查，不是独立 skill 入口。不要切换到全局 `codebase-design` skill；只在当前 feature design 里补强 module interface 质量。

## 什么时候用

当前 feature 出现任一信号时使用：

- 新增或改变 module interface。
- 新增 seam、port、adapter、第三方 client、测试替身。
- 把逻辑从 callers 移到新 module，或从一个胖文件拆出 module。
- 需要说明为什么测试应穿过某个 public interface。

纯文案、样式、配置值、小型内部修复，没有 interface / seam 变化时写"不适用"即可。

## 词汇

- **Module**：有 interface 和 implementation 的东西，可以是函数、类、包、目录或跨层 slice。
- **Interface**：caller 正确使用 module 必须知道的一切，不只是类型签名；还包括 invariant、调用顺序、错误语义、配置和性能约束。
- **Seam**：不在该处编辑也能改变行为的位置，通常是 module interface 所在位置。
- **Adapter**：在 seam 上满足 interface 的具体实现，例如 production HTTP adapter、test in-memory adapter。
- **Depth**：interface 给 caller 的 leverage。小 interface 隐藏大量行为就是 deep；大 interface 只透传少量逻辑就是 shallow。
- **Locality**：变化、bug、知识、验证是否集中在 module implementation 内，而不是散到 callers。

## 写进 design 的格式

在第 2.1 名词层或第 2.5 结构健康度里补一段：

```markdown
##### Interface 设计检查
- Module：{名称；现状 / 新增 / 改造}
- Interface：{caller 必须知道的签名、invariant、ordering、error mode、配置}
- Seam：{seam 放在哪里；caller 和测试为什么应穿过这里}
- Depth / locality：{复杂度藏在 implementation 内，还是会散到 callers；deletion test 结论}
- Dependency strategy：{in-process / local-substitutable / remote-owned / true external}
- Adapter：{无 / production + test adapters / mock external；若只有一个 adapter，说明为什么不是假 seam}
- Test surface：{哪些验收场景可以通过这个 interface 观察}
```

## 判据

- **Deletion test**：删掉这个 module 后，如果复杂度只是消失，它可能只是 pass-through；如果复杂度会重新散到多个 callers，module 有价值。
- **Interface is the test surface**：测试应该穿过同一个 interface 观察行为；如果必须测试 interface 后面的内部状态，module 形状可能错了。
- **一个 adapter 是假 seam 风险**：只有 production + test 或其他真实替换需求时，adapter seam 才成立。单 adapter 通常只是间接层。
- **Dependency category**：
  - in-process：纯计算 / 内存状态，优先直接 deepen，不需要 adapter。
  - local-substitutable：有本地替身，如测试数据库 / in-memory FS，测试穿过 module interface。
  - remote-owned：自有远程服务，在 seam 定义 port，production 用 HTTP/gRPC/queue adapter，测试用 in-memory adapter。
  - true external：第三方服务，把 external dependency 作为 injected port，测试用 mock adapter。

## Design It Twice 触发

如果 interface 影响多个 callers、长期公共契约、或你能想到两种以上合理 seam placement，先不要只写第一个方案。给用户列出 2-3 个候选 interface，按 depth、locality、seam placement 比较，并给出倾向。

这一步只影响 design；不要在 feature design 阶段启动实现，也不要把备选方案都写进 checklist。
