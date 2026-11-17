# .harness

How work gets done in this repo: the workflows for developing kairyn itself. Read these before changing the plugin, tests or evals. This is about building kairyn, not about using it (the README covers that).

| Workflow | Use it when |
|---|---|
| [Testing and evals](workflows/testing-and-evals.md) | Running or writing tests and evals |
| [Change a stage](workflows/change-a-stage.md) | Editing a stage's instructions or adding a new stage |
| [Init](workflows/init.md) | Changing `/kairyn:init` or its scripts |
| [Task lifecycle](workflows/task-lifecycle.md) | Touching `STATE.md`, task folders or timestamps |
| [Pull request](workflows/pull-request.md) | Getting a change merged |

## Principles

1. **Deterministic first.** If a step can be a script, make it a script (`init.sh`, `verify-init.sh`). Leave the model only what needs judgment. A command that asks the model to copy files by hand failed 10 out of 10 runs in headless mode.
2. **Tests before code, evals before instructions.** Write the failing test or eval first, then make it pass.
3. **Evidence over claims.** A passing eval leaves its outputs and scores in `evals/results/`. Don't report a pass you can't point to.
4. **Never trust the model with the clock or with overwriting user files.** Timestamps come from `date`. Init never overwrites.

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
  features/*.feature              scenarios, each with a `# depends:` header
  selector.py                     runs an eval only if its dependencies changed
.harness/                         these docs
CLAUDE.md                         loaded every session; points here on demand
```
