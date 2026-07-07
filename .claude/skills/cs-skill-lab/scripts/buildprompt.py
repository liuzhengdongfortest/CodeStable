#!/usr/bin/env python3
"""buildPrompt：把「被测 SKILL.md 快照 + fixture 任务」组装成喂给 harness/model 的 prompt。

这是绕开「cs skill 无法无头执行」的桥接点：被测 skill 以快照文本注入，不读宿主已装版本。
按 fixture.task["kind"] 分派（review / fix / audit），支撑自举扩容。
"""

from __future__ import annotations

from _model import Fixture

_INTRO = (
    "你在扮演一个 CodeStable skill。下面是该 skill 的完整 SKILL.md 指令（权威、需严格遵循）。"
    "请**仅**依据这些指令处理随后的任务，产出该 skill 规定的结构化结果。\n"
)


def build_prompt(fixture: Fixture, variant_text: str) -> str:
    kind = (fixture.task or {}).get("kind", "review")
    builder = _BUILDERS.get(kind, build_review_prompt)
    return builder(fixture, variant_text)


def build_review_prompt(fixture: Fixture, variant_text: str) -> str:
    task = fixture.task or {}
    diff = task.get("diff", "")
    spec = task.get("spec", "")
    parts = [
        _INTRO,
        "===== SKILL.md 开始 =====",
        variant_text.strip(),
        "===== SKILL.md 结束 =====\n",
        "## 待审查改动",
    ]
    if spec:
        parts += ["\n### 来源 spec", spec.strip()]
    parts += [
        "\n### diff / 代码",
        "```diff",
        diff.strip(),
        "```",
        "\n## 输出要求",
        "按该 skill 的 review 契约输出。**Findings** 一节逐条列出你发现的问题，"
        "每条以 `- [file:line] 简述` 开头，按 severity 分组（blocking/important/nit）。"
        "只要真实存在的问题，不要臆造。",
    ]
    return "\n".join(parts)


def build_fix_prompt(fixture: Fixture, variant_text: str) -> str:
    task = fixture.task or {}
    parts = [
        _INTRO,
        "===== SKILL.md 开始 =====",
        variant_text.strip(),
        "===== SKILL.md 结束 =====\n",
        "## 待修复问题",
        task.get("spec", "").strip(),
        "\n### 相关代码",
        "```",
        task.get("diff", "").strip(),
        "```",
        "\n## 输出要求",
        "按该 skill 的 fix 契约给出根因、修复方案与验证方式。",
    ]
    return "\n".join(parts)


def build_design_prompt(fixture: Fixture, variant_text: str) -> str:
    """design 生成型（如 cs-feat 的 design 阶段）：给需求，要求产出一份 design。

    注意：离线 mock harness 不产 design（无信号）；本 kind 的有效评测需真实 harness。
    """
    task = fixture.task or {}
    parts = [
        _INTRO,
        "===== SKILL.md 开始 =====",
        variant_text.strip(),
        "===== SKILL.md 结束 =====\n",
        "## 需求",
        task.get("spec", "").strip(),
    ]
    if task.get("context"):
        parts += ["\n### 背景", str(task["context"]).strip()]
    parts += [
        "\n## 输出要求",
        "按该 skill 的 design 契约产出一份 design：明确验收标准、必须处理的边界/异常、范围边界（做什么/不做什么）、"
        "DoD 契约与验证方式。逐条列出你识别到的**必须覆盖的关注点**（`- 关注点：…`），不要遗漏隐含需求。",
    ]
    return "\n".join(parts)


def build_docs_prompt(fixture: Fixture, variant_text: str) -> str:
    """docs 生成型（如 cs-docs 的 tutorial/API reference）：给文档任务，要求产出文档。

    离线 mock 不产文档（无信号）；有效评测需真实 harness。
    """
    task = fixture.task or {}
    parts = [
        _INTRO,
        "===== SKILL.md 开始 =====",
        variant_text.strip(),
        "===== SKILL.md 结束 =====\n",
        "## 文档任务",
        task.get("spec", "").strip(),
    ]
    if task.get("audience"):
        parts += [f"\n受众：{task['audience']}"]
    parts += [
        "\n## 输出要求",
        "按该 skill 的文档契约产出文档，并逐条列出你**覆盖到的关键要素**（`- 要素：…`）："
        "必要的参数/返回/错误、前置条件、可运行示例、边界与常见坑，不要遗漏。",
    ]
    return "\n".join(parts)


def build_audit_prompt(fixture: Fixture, variant_text: str) -> str:
    task = fixture.task or {}
    parts = [
        _INTRO,
        "===== SKILL.md 开始 =====",
        variant_text.strip(),
        "===== SKILL.md 结束 =====\n",
        "## 待审计代码",
        "```",
        task.get("diff", "").strip(),
        "```",
        "\n## 输出要求",
        "按该 skill 的 audit 契约列出发现，逐条 `- [file:line] 简述`。",
    ]
    return "\n".join(parts)


_BUILDERS = {
    "review": build_review_prompt,
    "fix": build_fix_prompt,
    "audit": build_audit_prompt,
    "design": build_design_prompt,
    "docs": build_docs_prompt,
}
