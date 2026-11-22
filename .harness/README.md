---
title: Harness overview
summary: "Principles and repo layout for developing kairyn."
read_when: "looking for the repo layout or principles"
load: on-demand
---

# .harness

How work gets done in this repo: the workflows for developing kairyn itself. Read these before changing the plugin, tests or evals. This is about building kairyn, not about using it (the README covers that).

<!-- harness-docs:start -->
| Workflow | Use it when |
|---|---|
| [Change a stage](workflows/change-a-stage.md) | editing or adding a stage in plugin/stages/ |
| [Init](workflows/init.md) | changing /kairyn:init, init.sh or verify-init.sh |
| [Keeping docs lean](workflows/keeping-docs-lean.md) | adding or editing a harness doc, or when /kairyn:check fails |
| [Pull request](workflows/pull-request.md) | committing, or opening or updating a pull request |
| [Running stages](workflows/running-stages.md) | running a stage, or editing or adding stage instructions |
| [Task lifecycle](workflows/task-lifecycle.md) | changing STATE.md, task folders or timestamps |
| [Testing and evals](workflows/testing-and-evals.md) | running, writing or interpreting tests or evals, or touching evals/ |
<!-- harness-docs:end -->

## Principles

1. **Deterministic first.** If a step can be a script, make it a script (`init.sh`, `verify-init.sh`). Leave the model only what needs judgment. A command that asks the model to copy files by hand failed 10 out of 10 runs in headless mode.
2. **Tests before code, evals before instructions.** Write the failing test or eval first, then make it pass.
3. **Evidence over claims.** A passing eval leaves its outputs and scores in `evals/results/`. Don't report a pass you can't point to.
4. **Never trust the model with the clock or with overwriting user files.** Timestamps come from `date`. Init never overwrites.
5. **Playbooks guide kairyn's own work.** The SDLC playbooks in the author's knowledge base (`03 Playbooks/`) drive how this repo is built. They are not shipped to consumers. A stage that kairyn lacks, such as design, is done by hand from its playbook.
6. **Lean files.** What an AI reads has a size budget (`budgets.yml`, estimated tokens). Tests fail when a file is over or has no budget. For people, `uv run python plugin/scripts/budgets_html.py` builds a readable report (`.harness/budgets.html`, git-ignored) from `budgets.yml`.

## Doc format

Every doc here starts with a header an agent can read without opening the body:

```yaml
---
title: <name>
summary: "<one line, at most 160 characters>"
read_when: "<the task that makes this doc relevant>"
load: on-demand
---
```

`load` says when a file is read:

| Class | Meaning |
|---|---|
| `always` | loaded every session, so keep it tiny (`CLAUDE.md`) |
| `on-demand` | read only when the task matches `read_when` (these docs) |
| `runtime` | shipped in the plugin, read when a command or stage runs |

Classes are set per file pattern in `budgets.yml` and must match each doc's header. Only `on-demand` docs appear in the index tables.

Read only those first lines (`head -6 <file>`) to decide whether a doc matters. The tables above and in `CLAUDE.md` are generated from these headers:

```bash
uv run python plugin/scripts/harness_docs.py --write   # regenerate the index tables
uv run python plugin/scripts/harness_docs.py --check   # verify headers and indexes
```

`uv run pytest` runs the same check, so a missing header or a stale index fails the tests.

## Layout

See the layout in the root [README](../README.md).
