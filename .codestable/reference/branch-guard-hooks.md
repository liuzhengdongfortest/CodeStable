# Branch Guard Hooks

`codestable-ai-branch-guard.py` protects the stable coordinator checkout. It is
meant to run before AI tool calls, and it can also install Git hook fallbacks.

## Policy

- AI must not run `git switch` or `git checkout` in an existing checkout.
- AI must not edit implementation files on `main` or `master`.
- AI must use a linked execution worktree on a typed branch (`feat/` / `fix/` / `refactor/`) for code work.
- Planning files such as `.codestable/**` can still be edited in the coordinator
  checkout when the agent hook payload names those files directly.
- The guard judges each edited file (and each Bash command) by the branch of the
  file/command's **own git worktree**, not by the `--root` the hook passes. So a
  file in a linked typed-branch worktree is allowed even when the hook's `--root`
  is the `main` checkout (e.g. the worktree lives under `.codestable/`/`.claude/`
  worktrees of the main checkout). This makes the worktree execution flow usable
  with hosts whose project-dir env var does not follow `EnterWorktree`.

Git cannot stop branch switches before they happen, so command-hook enforcement
is the primary guard. Git hooks are only a commit-time fallback.

## Agent Hook

Configure the agent's pre-tool command hook to run:

```bash
python3 .codestable/tools/codestable-ai-branch-guard.py --root "$PWD"
```

The hook reads JSON from stdin. It recognizes common `tool_name` /
`tool_input.command` payloads for shell tools and common `file_path` fields for
edit tools. A blocked action exits with status `2` and prints the reason to
stderr.

For shell tools, the agent hook blocks known Git write commands (`git add`,
`commit`, `merge`, `push`, etc.) and branch switches before they run. It does
not parse arbitrary shell programs such as `python -c 'open("app.py", "a")...'`;
direct file writes must be caught by Edit/Write tool payload paths or by the
implementation review and worktree gates after the command.

## Git Hook Fallback

Install local Git hook fallbacks from a project that has been onboarded:

```bash
python3 .codestable/tools/codestable-ai-branch-guard.py --root . --install-git-hooks
```

Installed fallbacks:

- `pre-commit`: blocks staged implementation files on `main` / `master`.

This repository no longer installs Git hooks for protected-branch merge, rebase
or push. Publishing `main` remains an owner workflow, not a local hook gate.
Use `--force` only when replacing an existing local hook is intentional.

## Recovery

If work has already started in the coordinator checkout, stop and create a
linked execution worktree from the current target baseline. Move or recreate the
work there, then run the normal CodeStable start / commit gates.
