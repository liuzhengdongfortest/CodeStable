# CodeStable Skill Fixture Patterns

Use this reference when designing decision fixtures for a `cs-*` skill.

Fixtures test whether the agent makes the correct decision after reading the skill. They complement contracts: contracts check text shape; fixtures check behavior.

## Fixture Shape

Use a small YAML or JSON case:

```yaml
name: short-case-name
skill: cs-feat
step: restoreFeatureStage
input:
  args: "--stage qa"
state:
  has_design: true
  design_status: approved
  review_status: passed
  qa_status: missing
expect:
  result_type: RoutedTo
  stage: QA
  must_not_route_to: Implementation
```

Keep one decision per fixture. Do not mix routing, output formatting, and artifact content in the same case.

## Routing Fixture

Use when a skill chooses the next stage from repository facts.

```yaml
name: no-design-routes-to-design
step: restoreWorkflowState
state:
  feature_dir_exists: true
  has_design: false
  has_review: false
expect:
  result_type: RoutedTo
  stage: Design
```

## Human Checkpoint Fixture

Use when the skill must stop for explicit user confirmation.

```yaml
name: review-passed-requires-design-confirmation
step: selectNextAction
state:
  has_design: true
  design_status: draft
  design_review: passed
expect:
  result_type: HumanCheckpoint
  reason: ConfirmDesign
  must_not_route_to: GoalPackage
```

## Forbidden Action Fixture

Use when a dangerous or out-of-scope action must not happen.

```yaml
name: docs-skill-must-not-change-code
step: planAction
input:
  request: "update public docs for the auth API"
expect:
  result_type: RoutedTo
  stage: Docs
  forbidden_actions:
    - edit_source_code
    - git_push
```

## Failure Path Fixture

Use when missing facts should stop the skill.

```yaml
name: ambiguous-feature-target-needs-human
step: restoreFeatureTarget
state:
  matching_features:
    - ".codestable/features/2026-07-01-auth"
    - ".codestable/features/2026-07-03-auth-refresh"
expect:
  result_type: NeedsHuman
  reason_contains: "which feature"
```

## Fastforward Eligibility Fixture

Use when a shortcut mode is allowed only under narrow conditions.

```yaml
name: fastforward-rejects-public-contract-change
step: chooseMode
input:
  args: "--mode fastforward add new public auth API"
state:
  crosses_public_contract: true
expect:
  result_type: RoutedTo
  stage: Design
  must_not_route_to: FastForward
```

## Compatibility Entry Fixture

Use when old skill names remain as shims.

```yaml
name: legacy-qa-entry-routes-to-main-skill
skill: cs-feat-qa
step: entrypoint
input:
  args: ""
expect:
  route_to: cs-feat
  requested_stage: qa
  must_not_define_independent_rules: true
```

## Fixture Selection Checklist

Start with 5 to 8 cases:

- happy path for each major stage;
- one checkpoint case;
- one failure case;
- one forbidden action case;
- one compatibility or fastforward case if applicable.

Add regression fixtures whenever a production failure or user correction reveals a missed branch.
