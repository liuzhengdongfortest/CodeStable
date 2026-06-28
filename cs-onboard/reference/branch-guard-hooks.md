# Branch Guard Hooks

`codestable-ai-branch-guard.py` protects the stable coordinator checkout. It is
meant to run before AI tool calls, and it can also install Git hook fallbacks.

## Policy

- AI must not run `git switch` or `git checkout` in an existing checkout.
- AI must not edit implementation files on `main` or `master`.
- AI must use a linked execution worktree on a typed branch (`feat/` / `fix/` / `refactor/`) for code work.
- Planning files such as `.codestable/**` can still be edited in the coordinator
  checkout when the agent hook payload names those files directly.

Git cannot stop branch switches before they happen, so command-hook enforcement
is the primary guard. Git hooks only catch commit, merge, rebase, and push
fallbacks.

## Agent Hook

Configure the agent's pre-tool command hook to run:

```bash
python3 .codestable/tools/codestable-ai-branch-guard.py --root "$PWD"
```

The hook reads JSON from stdin. It recognizes common `tool_name` /
`tool_input.command` payloads for shell tools and common `file_path` fields for
edit tools. A blocked action exits with status `2` and prints the reason to
stderr.

For shell tools, the guard blocks known Git write commands (`git add`,
`commit`, `merge`, `push`, etc.) and branch switches. It does not parse arbitrary
shell programs such as `python -c 'open("app.py", "a")...'`; direct file writes
must be caught by Edit/Write tool payload paths or by the implementation review
and worktree gates after the command.

## Git Hook Fallback

Install local Git hook fallbacks from a project that has been onboarded:

```bash
python3 .codestable/tools/codestable-ai-branch-guard.py --root . --install-git-hooks
```

Installed fallbacks:

- `pre-commit`: blocks staged implementation files on `main` / `master`.
- `pre-merge-commit`: blocks protected-branch merge commits.
- `pre-rebase`: blocks protected-branch rebases.
- `pre-push`: blocks protected-branch pushes.

Use `--force` only when replacing an existing local hook is intentional.

## Owner-Intent Main Publish

Protected-branch merge and push are allowed only during a short owner-approved
publish window. Start the window from a clean `main` checkout that matches
`origin/main`:

```bash
python3 .codestable/tools/codestable-main-publish.py --root . --json begin \
  --owner-intent "owner approved publishing branch X to main" \
  --branch feat/example
```

Then run the merge / validation / push. The guard allows `git merge`,
merge-conflict resolution commits, and `git push` while the intent is active.
It still blocks `git switch` / `git checkout`.

Finish by removing the intent:

```bash
python3 .codestable/tools/codestable-main-publish.py --root . --json end
```

## Recovery

If work has already started in the coordinator checkout, stop and create a
linked execution worktree from the current target baseline. Move or recreate the
work there, then run the normal CodeStable start / commit gates.
