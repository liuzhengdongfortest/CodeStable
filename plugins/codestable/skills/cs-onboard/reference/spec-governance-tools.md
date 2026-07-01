# Spec Governance Tools

This file documents project-runtime helpers copied by `cs-onboard` into
`.codestable/reference/`. The source tool is:

```bash
python3 .codestable/tools/codestable-spec-governance.py --root . --json <command>
```

## Commands

### `route`

Select candidate long-lived specs before design, roadmap, requirement, or
acceptance work:

```bash
python3 .codestable/tools/codestable-spec-governance.py --root . --json route \
  --query "source scout query coverage before crawl"
```

The JSON reports `selected_specs`, `excluded_specs`,
`clarification_required`, and `allowed_to_skip_requirement_delta`.

No selected spec is an owner clarification state unless the query matches an
explicit local-skip pattern such as a frontend-only display tweak. It must not be
treated as permission to skip requirement review.

### `clarify`

Append an owner clarification to an existing spec file without rewriting the
whole document:

```bash
python3 .codestable/tools/codestable-spec-governance.py --root . --json clarify \
  --file .codestable/requirements/source-discovery.md \
  --question "Which source field is canonical?" \
  --answer "Use retrieved_at plus intent bucket." \
  --anchor RQ-2
```

The command is idempotent for the same question and answer.

### `create-delta`

Create a feature-local requirement delta instead of mutating a long-lived
requirement directly:

```bash
python3 .codestable/tools/codestable-spec-governance.py --root . --json create-delta \
  --unit .codestable/features/YYYY-MM-DD-source-query-coverage \
  --requirement source-discovery \
  --added "The system records query intent coverage before crawl." \
  --scenario "source scout records coverage gap" \
  --owner-decision approved
```

The file path is `{unit}/{slug}-req-delta.md`.

### `apply-delta`

Mechanically record an approved delta in the target requirement change log:

```bash
python3 .codestable/tools/codestable-spec-governance.py --root . --json apply-delta \
  --delta .codestable/features/YYYY-MM-DD-source-query-coverage/source-query-coverage-req-delta.md \
  --target .codestable/requirements/source-discovery.md
```

Unapproved deltas fail with `delta_not_approved`.

### `inventory`

Classify current spec documents as `current-trusted`,
`current-unreviewed`, `drift-suspected`, `historical`, `superseded`, or
`orphaned`:

```bash
python3 .codestable/tools/codestable-spec-governance.py --root . --json inventory
```

Old specs with `status: current` but no explicit `owner_review_state` are
classified as `current-unreviewed`, not trusted.

Write a human-readable rehabilitation artifact when the inventory needs to be
reviewed or handed to the owner:

```bash
python3 .codestable/tools/codestable-spec-governance.py --root . --json inventory \
  --output .codestable/spec-governance/YYYY-MM-DD-{slug}-inventory.md
```

The artifact lists classification counts, every spec item, and owner follow-up
entries for `current-unreviewed` or `drift-suspected` specs. Re-running with the
same state is content-aware and does not rewrite the file.

### `analyze`

Run a read-only acceptance/design consistency pass:

```bash
python3 .codestable/tools/codestable-spec-governance.py --root . --json analyze \
  --unit .codestable/features/YYYY-MM-DD-source-query-coverage
```

It blocks capability-boundary changes without an approved req delta and dirty
requirement rewrites without approved delta evidence. Drift-suspected specs are
reported for owner adjudication.

## Boundary

This tool is deterministic. It does not decide product intent, merge specs, or
rewrite old requirements. Human owner decisions still happen through owner
context, clarification, or approved deltas.
