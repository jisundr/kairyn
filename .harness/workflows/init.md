---
title: Init
summary: "How /kairyn:init, init.sh and verify-init.sh work, and the never-overwrite rule."
read_when: "changing /kairyn:init, init.sh or verify-init.sh"
---

# Init

`/kairyn:init` (`plugin/commands/init.md`) sets up kairyn in a user's repo. The command itself only runs two scripts, so the result does not depend on the model.

## Flow

1. `plugin/scripts/init.sh .` does the work:
   - If `.kairyn/` exists, it prints `ALREADY INITIALIZED`, changes nothing and exits 0.
   - Otherwise it creates `.kairyn/stages/`, `.kairyn/templates/` and `docs/tasks/`, copies every file from `plugin/stages/` and `plugin/templates/`, and writes `.kairyn/learnings.md` with the `# Learnings` heading.
2. `plugin/scripts/verify-init.sh .` checks the result. The command must not report success until it prints `OK`.

## What verify-init.sh checks

- `.kairyn/`, `.kairyn/stages/`, `.kairyn/templates/` and `docs/tasks/` exist.
- Every shipped stage and template exists in `.kairyn/` and is byte-identical to the plugin copy.
- `learnings.md` exists and starts with `# Learnings`.
- `docs/tasks/` is empty (init creates no tasks).

It exits 1 and prints a `FAIL:` line per problem.

## Rules

- **Never overwrite.** The copies in `.kairyn/` belong to the user and may be edited. Re-running init must leave them alone (an eval enforces this at 100%).
- **Keep the copy in the script.** The command used to copy files itself with `cp` and a glob, which headless mode blocked, so init failed 10 of 10 runs. Anything that must always work belongs in `init.sh`.
- Changing what init creates means changing `init.sh`, `verify-init.sh`, their tests in `tests/test_verify_init.py`, and the init eval together.

## Checking a change

```bash
uv run pytest                       # init.sh and verify-init.sh behavior
uv run pytest -m eval               # init eval runs if init.md or scripts changed
```
