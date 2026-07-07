# cs-issue-e2e-001

这是 `cs-issue` 的 e2e outcome 冒烟评测实验，基于 `experiments/seeds/task-api` 构建出的 taskhub seed。

每个场景包含：

- `bugs/<id>/inject.py`：对好版本 seed 做精准字符串替换，注入一个用户可见 bug。
- `hidden/<id>/test_*.py`：hidden pytest，从 issue 症状视角验证正确行为。
- `fixtures/e2e/<id>.json`：runner 可读取的 e2e fixture 描述。

验证约定：

1. 好版本 + hidden tests 必须绿，证明题目可解。
2. 注入 bug 后 hidden tests 必须红，证明 bug 生效。
3. 注入 bug 后 seed 自带 tests 必须仍绿，证明注入点处于自带测试暗角。
