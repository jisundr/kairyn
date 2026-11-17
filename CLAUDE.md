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

Open the doc only when the task matches. Do not read them all up front.

| If you are about to... | Read |
|---|---|
| run, write or interpret tests or evals, or touch `evals/` | `.harness/workflows/testing-and-evals.md` |
| edit or add a stage in `plugin/stages/` | `.harness/workflows/change-a-stage.md` |
| change `/kairyn:init`, `init.sh` or `verify-init.sh` | `.harness/workflows/init.md` |
| change `STATE.md`, task folders or timestamps | `.harness/workflows/task-lifecycle.md` |
| commit, open or update a PR | `.harness/workflows/pull-request.md` |
| need the repo layout or principles | `.harness/README.md` |

If you change a workflow, update the matching `.harness` doc in the same commit.
