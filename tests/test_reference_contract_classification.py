import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "plugins/codestable/skills"

HASKELL_BLOCK_RE = re.compile(r"```haskell\n(.*?)\n```", re.DOTALL)
TYPE_SURFACE_RE = re.compile(
    r"(?m)^(?:data\s+[A-Z][A-Za-z0-9_]*|[a-z][A-Za-z0-9_']*\s*::)"
)
DECISION_SURFACE_RE = re.compile(
    r"(?m)^(?!(?:data|type|newtype)\b)[a-z][A-Za-z0-9_']*"
    r"(?:\s+[^=\n]+)?\s*=|^\s*\|[^=\n]+="
)

HASKELL_CONTRACT_REFERENCES = {
    "cs-code-review/references/independent-review/protocol.md",
    "cs-docs/references/api/protocol.md",
    "cs-docs/references/tutorial/protocol.md",
    "cs-epic/references/goal/protocol.md",
    "cs-epic/references/goal/support/protocol-audit.md",
    "cs-epic/references/goal/support/protocol-feature-loop.md",
    "cs-epic/references/goal/support/protocol-gates.md",
    "cs-epic/references/goal/support/protocol.md",
    "cs-epic/references/planning/protocol.md",
    "cs-epic/references/review/protocol.md",
    "cs-feat/references/acceptance/protocol.md",
    "cs-feat/references/acceptance/reference.md",
    "cs-feat/references/design-review/protocol.md",
    "cs-feat/references/design/protocol.md",
    "cs-feat/references/fastforward/protocol.md",
    "cs-feat/references/goal/protocol.md",
    "cs-feat/references/implementation/protocol.md",
    "cs-feat/references/qa/protocol.md",
    "cs-issue/references/analyze/protocol.md",
    "cs-issue/references/fix/protocol.md",
    "cs-issue/references/report/protocol.md",
    "cs-onboard/references/agent-conventions.md",
    "cs-onboard/references/approval-conventions.md",
    "cs-onboard/references/execution-conventions.md",
    "cs-onboard/references/goal-conventions.md",
    "cs-onboard/references/maintainer-notes.md",
    "cs-onboard/references/shared-conventions.md",
    "cs-onboard/references/system-overview.md",
    "cs-refactor/references/fastforward/protocol.md",
    "cs-refactor/references/library/refusal-routing.md",
    "cs-refactor/references/standard/protocol.md",
}

STRUCTURED_REFERENCES = {
    "cs-audit/reference.md",
    "cs-brainstorm/reference.md",
    "cs-code-review/references/report-template.md",
    "cs-docs-neat/references/agent-paths.md",
    "cs-docs-neat/references/sync-matrix.md",
    "cs-docs/references/api/reference.md",
    "cs-epic/references/goal/support/goal-command-template.md",
    "cs-epic/references/planning/support/codebase-design.md",
    "cs-epic/references/planning/reference.md",
    "cs-feat/references/design/reference.md",
    "cs-feat/references/design/support/codebase-design.md",
    "cs-feat/references/design/support/intent-template.md",
    "cs-feat/references/implementation/support/reference.md",
    "cs-feat/references/implementation/support/tdd.md",
    "cs-feat/references/qa/behavioral-verification.md",
    "cs-feedback/references/report-template.md",
    "cs-goal/reference.md",
    "cs-issue/references/fix/reference.md",
    "cs-onboard/references/code-dimensions.md",
    "cs-onboard/references/artifact-conventions.md",
    "cs-onboard/reference.md",
    "cs-onboard/references/requirement-example.md",
    "cs-onboard/references/solution-depth-conventions.md",
    "cs-onboard/references/spec-governance-tools.md",
    "cs-onboard/references/tools-context.md",
    "cs-onboard/references/tools.md",
    "cs-refactor/references/library/methods-architecture.md",
    "cs-refactor/references/library/methods-l4.md",
    "cs-refactor/references/library/methods.md",
    "cs-refactor/references/library/scan-checklist-format.md",
}


def test_every_reference_markdown_has_an_explicit_representation_class() -> None:
    discovered = {
        path.relative_to(SKILLS).as_posix()
        for path in SKILLS.rglob("*.md")
        if path.name != "SKILL.md"
    }
    classified = HASKELL_CONTRACT_REFERENCES | STRUCTURED_REFERENCES

    assert HASKELL_CONTRACT_REFERENCES.isdisjoint(STRUCTURED_REFERENCES)
    assert discovered == classified


def test_haskell_contract_references_contain_executable_contracts() -> None:
    for relative_path in sorted(HASKELL_CONTRACT_REFERENCES):
        text = (SKILLS / relative_path).read_text(encoding="utf-8")
        blocks = HASKELL_BLOCK_RE.findall(text)
        assert blocks, relative_path
        contract = "\n".join(blocks)
        assert TYPE_SURFACE_RE.search(contract), f"{relative_path}: 缺类型/签名边界"
        assert DECISION_SURFACE_RE.search(contract), f"{relative_path}: 缺决策方程"

    for relative_path in sorted(STRUCTURED_REFERENCES):
        text = (SKILLS / relative_path).read_text(encoding="utf-8")
        assert "```haskell" not in text, relative_path


def test_decision_surface_does_not_treat_data_declaration_as_equation() -> None:
    assert not DECISION_SURFACE_RE.search("data Outcome = Run Step | Blocked Reason")
    assert DECISION_SURFACE_RE.search("advance QA (Failed _) = Remediate Implementation Review")
