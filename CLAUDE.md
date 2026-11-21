# kairyn

A Claude Code plugin: an agentic SDLC that grows with the user's repo. Shipped code: `plugin/`. Verified by `tests/` and `evals/`.

## Commands

```bash
uv run pytest                       # fast tests, no LLM, always safe
claude plugin validate plugin       # manifest and component validation
uv run python evals/run.py         # promptfoo evals: real claude runs, slow, costs tokens
```

## Rules that always apply

- **Evals cost real tokens (3 to 7 minutes each).** Run them only when asked or when `plugin/` changes; `--all-evals` only for a release. `uv run pytest` must never run them.
- **Tests before code, evals before instructions.** Write the failing test or eval first and watch it fail.
- **Script what must always work.** Steps that need to be reliable go in `plugin/scripts/`, not in model instructions.
- **Init never overwrites** anything in a user's `.kairyn/`.
- **Report evidence, not claims.** Quote numbers from `evals/results/<run-id>/summary.md`.
- Stage files and their outputs are upper case (`REQUIREMENTS.md`); stage names and `STATE.md` values are lower case (`requirements`).
- **Keep files lean.** Every markdown file needs a token budget in `.harness/budgets.yml` (`plugin/scripts/budgets.py` checks). Over budget: cut or split, never raise the limit.
- The remote is GitHub, so it is a pull request, not a merge request.

If you change a workflow, update the matching `.harness` doc in the same commit. After adding or editing a `.harness` doc, run `uv run python plugin/scripts/harness_docs.py --write`. The doc index is in the kairyn block (this repo uses its own plugin).

<!-- kairyn:start -->
## kairyn

Work runs through stages. Instructions: `.kairyn/stages/`. Task state and outputs: `docs/tasks/<YYYY-MM-DD>-<slug>/`. Learnings: `.kairyn/learnings.md`. Timestamps come from `date`, never from memory.

Read a doc only when the task matches; `head -6 <file>` shows its header.

<!-- harness-docs:start -->
| When you are... | Read |
|---|---|
| looking for the repo layout or principles | `.harness/README.md` |
| editing or adding a stage in plugin/stages/ | `.harness/workflows/change-a-stage.md` |
| changing /kairyn:init, init.sh or verify-init.sh | `.harness/workflows/init.md` |
| adding or editing a harness doc, or when /kairyn:check fails | `.harness/workflows/keeping-docs-lean.md` |
| committing, or opening or updating a pull request | `.harness/workflows/pull-request.md` |
| running a stage, or editing or adding stage instructions | `.harness/workflows/running-stages.md` |
| changing STATE.md, task folders or timestamps | `.harness/workflows/task-lifecycle.md` |
| running, writing or interpreting tests or evals, or touching evals/ | `.harness/workflows/testing-and-evals.md` |
<!-- harness-docs:end -->
<!-- kairyn:end -->
