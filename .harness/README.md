---
title: Harness overview
summary: "Principles and repo layout for developing kairyn."
read_when: "looking for the repo layout or principles"
---

# .harness

How work gets done in this repo: the workflows for developing kairyn itself. Read these before changing the plugin, tests or evals. This is about building kairyn, not about using it (the README covers that).

<!-- harness-docs:start -->
| Workflow | Use it when |
|---|---|
| [Change a stage](workflows/change-a-stage.md) | editing or adding a stage in plugin/stages/ |
| [Init](workflows/init.md) | changing /kairyn:init, init.sh or verify-init.sh |
| [Pull request](workflows/pull-request.md) | committing, or opening or updating a pull request |
| [Task lifecycle](workflows/task-lifecycle.md) | changing STATE.md, task folders or timestamps |
| [Testing and evals](workflows/testing-and-evals.md) | running, writing or interpreting tests or evals, or touching evals/ |
<!-- harness-docs:end -->

## Principles

1. **Deterministic first.** If a step can be a script, make it a script (`init.sh`, `verify-init.sh`). Leave the model only what needs judgment. A command that asks the model to copy files by hand failed 10 out of 10 runs in headless mode.
2. **Tests before code, evals before instructions.** Write the failing test or eval first, then make it pass.
3. **Evidence over claims.** A passing eval leaves its outputs and scores in `evals/results/`. Don't report a pass you can't point to.
4. **Never trust the model with the clock or with overwriting user files.** Timestamps come from `date`. Init never overwrites.
5. **Lean files.** What an AI reads has a size budget (`budgets.yml`, estimated tokens). Tests fail when a file is over or has no budget.

## Doc format

Every doc here starts with a header an agent can read without opening the body:

```yaml
---
title: <name>
summary: "<one line, at most 160 characters>"
read_when: "<the task that makes this doc relevant>"
---
```

Read only those first lines (`head -6 <file>`) to decide whether a doc matters. The tables above and in `CLAUDE.md` are generated from these headers:

```bash
uv run python tools/harness_docs.py --write   # regenerate the index tables
uv run python tools/harness_docs.py --check   # verify headers and indexes
```

`uv run pytest` runs the same check, so a missing header or a stale index fails the tests.

## Layout

```
.claude-plugin/marketplace.json   marketplace entry
plugin/                           the shipped plugin
  commands/init.md                /kairyn:init
  scripts/                        init.sh, verify-init.sh (run by the command)
  stages/                         stage definitions (_template.md, REQUIREMENTS.md)
  templates/STATE.md              per-task state file
tests/                            fast tests (pytest)
evals/                            BDD evals that run real claude sessions
tools/harness_docs.py             checks doc headers and builds the index tables
tools/budgets.py                  checks file sizes against budgets.yml
  features/*.feature              scenarios, each with a `# depends:` header
  selector.py                     runs an eval only if its dependencies changed
.harness/                         these docs
CLAUDE.md                         loaded every session; points here on demand
```
