# Changelog

## 0.1.1

- Refined project and epic spec workflows around developer-facing usage narratives instead of code-layer structure.
- Reworked `cs-spec-explore` into a user-controlled alignment loop that creates exploratory issue workspaces with candidate spec articles.
- Split issue templates by scenario and removed the generic issue template.
- Clarified close behavior so confirmed exploratory articles graduate into project spec according to spec organization rules.

## 0.1.0

- Added the CodeStable LITE plugin distribution under `plugins/codestable-lite/`.
- Packaged the same skill set for Codex and Claude plugin installation.
- Added marketplace metadata and version manifests for release validation.
- Moved root `cs` / `cs-*` skill directories into `plugins/codestable-lite/skills/`.
- Folded `cs-test` into `cs-design`; detailed testing strategy now lives inside implementation design when needed.
