# cs-feat-e2e-001

这是 `cs-feat` 的 e2e outcome 评测实验。场景使用 taskhub seed，给 agent 一个 feature 需求，
并用 hidden tests 分别评估显式需求与隐含边界。

约定：

- `test_fXX_explicit.py` 只测用户需求明说的行为。
- `test_fXX_implicit.py` 只测未明说但专业实现应处理的边界。
- fixture 中 `artifact_glob` 指向 `.codestable/features/**/*design*`，用于判定 design 产物。
- hidden tests 只断言用户可见行为，不锁定实现函数名。
