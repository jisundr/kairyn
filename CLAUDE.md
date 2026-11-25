# kairyn

A Claude Code plugin: an agentic SDLC that grows with the user's repo. Shipped code: `plugin/`. Verified by `tests/` and `evals/`.

## Commands

```bash
uv run pytest                  # fast, no LLM, always safe
claude plugin validate plugin  # manifest and component validation
/run-evals <evals>             # evals in a subagent, costs tokens
```

## Rules that always apply

- **Evals cost real tokens.** Run them with `/run-evals`, only when asked or `plugin/` changes; `--all-evals` only for a release. Before you start one, name the evals, runs and cost (from the last `summary.md`) and wait for a yes; a typed `/run-evals` or a run id needs none. `uv run pytest` never runs evals.
- **Tests before code, evals before instructions.** Write the failing test or eval first and watch it fail.
- **Script what must always work.** Reliable steps go in `plugin/scripts/`, not model instructions.
- **Init never overwrites** a user's `.kairyn/`.
- **Report evidence, not claims.** Quote numbers from its `summary.md`.
- Stage files are upper case (`REQUIREMENTS.md`); stage names and `STATE.md` values lower case.
- **Keep files lean.** Each markdown file has a token budget in `.harness/budgets.yml`. Over it: cut or split, never raise it.

Change a workflow: update its `.harness` doc in the same commit, then run `uv run python plugin/scripts/harness_docs.py --write`.

<!-- kairyn:start -->
## kairyn

Work runs through stages. Instructions: `.kairyn/stages/`. Task state and outputs: `docs/tasks/<YYYY-MM-DD>-<slug>/`. Learnings: `.kairyn/learnings.md`. Timestamps come from `date`, never from memory.

Read a doc only when the task matches; `head -6 <file>` shows its header.

<!-- harness-docs:start -->
| When you are... | Read |
|---|---|
| looking for the repo layout or principles | `.harness/README.md` |
| running /kairyn:build or /kairyn:review, or editing afk.yml | `.harness/workflows/afk-run.md` |
| editing or adding a stage in plugin/stages/ | `.harness/workflows/change-a-stage.md` |
| changing /kairyn:init, init.sh or verify-init.sh | `.harness/workflows/init.md` |
| adding or editing a harness doc, or when /kairyn:check fails | `.harness/workflows/keeping-docs-lean.md` |
| setting up milestones.yml | `.harness/workflows/milestones.md` |
| committing, or opening or updating a pull request | `.harness/workflows/pull-request.md` |
| running a stage, or editing or adding stage instructions | `.harness/workflows/running-stages.md` |
| changing STATE.md, task folders or timestamps | `.harness/workflows/task-lifecycle.md` |
| running, writing or interpreting tests or evals, or touching evals/ | `.harness/workflows/testing-and-evals.md` |
| changing upgrades or the plugin version | `.harness/workflows/upgrade.md` |
<!-- harness-docs:end -->
<!-- kairyn:end -->
