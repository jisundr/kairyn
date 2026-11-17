# kairyn

A Claude Code plugin: an agentic SDLC that grows with the user's repo. Shipped code is in `plugin/`; `tests/` and `evals/` verify it; `.harness/` documents how we work.

## Commands

```bash
uv run pytest                       # fast tests, no LLM, always safe
claude plugin validate plugin       # manifest and component validation
uv run pytest -m eval               # evals: real claude runs, slow, costs tokens
```

## Rules that always apply

- **Evals cost real tokens (3 to 7 minutes each).** Never run them unless asked or the change touches `plugin/`. Never remove `-m 'not eval'` from `pyproject.toml`. Use `--all-evals` only for a release check.
- **Tests before code, evals before instructions.** Write the failing test or eval first and watch it fail.
- **Script what must always work.** Steps that need to be reliable go in `plugin/scripts/`, not in model instructions.
- **Timestamps come from `date`**, never from memory.
- **Init never overwrites** anything in a user's `.kairyn/`.
- **Report evidence, not claims.** Quote numbers from `evals/results/<run-id>/summary.md`.
- Stage files and their outputs are upper case (`REQUIREMENTS.md`); stage names and `STATE.md` values are lower case (`requirements`).
- The remote is GitHub, so it is a pull request, not a merge request.

## Read on demand

Open a doc only when the task matches. Do not read them all up front. Each starts with a header (title, summary, read_when), so `head -6 <file>` is enough to judge relevance.

<!-- harness-docs:start -->
| When you are... | Read |
|---|---|
| looking for the repo layout or principles | `.harness/README.md` |
| editing or adding a stage in plugin/stages/ | `.harness/workflows/change-a-stage.md` |
| changing /kairyn:init, init.sh or verify-init.sh | `.harness/workflows/init.md` |
| committing, or opening or updating a pull request | `.harness/workflows/pull-request.md` |
| changing STATE.md, task folders or timestamps | `.harness/workflows/task-lifecycle.md` |
| running, writing or interpreting tests or evals, or touching evals/ | `.harness/workflows/testing-and-evals.md` |
<!-- harness-docs:end -->

If you change a workflow, update the matching `.harness` doc in the same commit. After adding or editing a `.harness` doc, run `uv run python tools/harness_docs.py --write`.
