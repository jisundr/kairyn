---
title: Init
summary: "How /kairyn:init, init.sh and verify-init.sh work, and the never-overwrite rule."
read_when: "changing /kairyn:init, init.sh or verify-init.sh"
load: on-demand
---

# Init

`/kairyn:init` (`plugin/commands/init.md`) sets up kairyn in a user's repo. The command itself only runs two scripts, so the result does not depend on the model.

## Flow

1. `plugin/scripts/init.sh .` does the work:
   - If `.kairyn/` exists, it prints `ALREADY INITIALIZED`, changes nothing and exits 0.
   - Otherwise it creates `.kairyn/stages/`, `.kairyn/templates/` and `docs/tasks/`, copies every file from `plugin/stages/` and `plugin/templates/`, and writes `.kairyn/learnings.md` with the `# Learnings` heading.
   - It also installs the consumer harness: the files in `plugin/harness/.harness/` go to the repo's `.harness/` (an existing file is kept and reported as `KEPT`), and `plugin/harness/CLAUDE.block.md` is appended to `CLAUDE.md` between kairyn markers, once. If `CLAUDE.md` does not exist it is created. Nothing else in it is touched.
2. `plugin/scripts/verify-init.sh --fresh .` checks the result. The command must not report success until it prints `OK`.

## What verify-init.sh checks

Two modes. The default checks a repo in use. `--fresh` checks a repo right after init (the command, CI and the init eval use it).

- `.kairyn/`, `.kairyn/stages/`, `.kairyn/templates/` and `docs/tasks/` exist.
- Every shipped stage and template exists in `.kairyn/`. Templates (plugin-owned) match the plugin copy byte for byte. Stages (repo-owned) are compared only with `--fresh`.
- Every file shipped in `plugin/harness/.harness/` exists in the repo (existence only, since users may edit them).
- `CLAUDE.md` exists and has the kairyn block.
- `learnings.md` exists and starts with `# Learnings`.
- `--fresh` only: `docs/tasks/` is empty (init creates no tasks).

It exits 1 and prints a `FAIL:` line per problem.

## Rules

- **Never overwrite.** The copies in `.kairyn/` belong to the user and may be edited. Re-running init must leave them alone (an eval enforces this at 100%).
- **Keep the copy in the script.** The command used to copy files itself with `cp` and a glob, which headless mode blocked, so init failed 10 of 10 runs. Anything that must always work belongs in `init.sh`.
- Changing what init creates means changing `init.sh`, `verify-init.sh`, their tests in `tests/test_verify_init.py`, and the init eval together.

## Checking a change

```bash
uv run pytest                       # init.sh and verify-init.sh behavior
uv run python evals/run.py init  # init eval runs if init.md or scripts changed
```

## The consumer harness (`plugin/harness/`)

What a user's repo gets: generic workflow docs, `budgets.yml` (`strict: false`, so only listed files are checked) and the CLAUDE.md block. Keep it generic: kairyn's own dev docs (testing, evals, PRs) do not belong there.

Checkers are not copied. They ship in `plugin/scripts/` and run through `/kairyn:check`, using only `python3` (`simple_yaml.py` replaces PyYAML; a test keeps it in line with PyYAML).

The index tables inside these templates are generated. After editing a doc there, run `bash scripts/refresh-harness-templates.sh`; `test_installed_harness_passes_the_doc_and_budget_checkers` fails if they are stale.

Re-running init on a repo that already has `.kairyn/` changes nothing, so existing users do not get the harness until an upgrade path exists.
