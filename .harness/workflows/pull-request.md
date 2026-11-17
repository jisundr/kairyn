# Pull request

The repo is on GitHub (`jisundr/kairyn`), so changes go through pull requests, not merge requests. Branches are named `feat/<short-description>`.

## Before opening

```bash
uv run pytest                       # tests, fast
claude plugin validate plugin       # manifest and component validation
uv run pytest -m eval               # only evals whose dependencies changed
```

- If you changed anything under `plugin/`, run the evals that depend on it. Skipped evals are fine only when the selector says the dependencies are unchanged.
- Before a release, run everything with `uv run pytest -m eval --all-evals`.
- Put the eval summary in the PR description when evals ran. Quote numbers, not "passed".

## Opening

1. Branch from `main`, commit, push.
2. Open the PR with `gh pr create --base main`. The title says what changed. The body has a short summary and a test plan with the commands above.
3. Keep the title and description current. If the scope grows, update them.

## Commits

One logical change per commit, message in the imperative. Commits made with Claude Code end with a `Co-Authored-By` trailer, and PR descriptions end with the Claude Code attribution line.

## Do not

- Commit `evals/results/`, `.venv/` or caches (all git-ignored).
- Merge with failing tests or a failing eval you have not explained.
- Rename or move `plugin/` files without updating the `# depends:` headers in `evals/features/` and the README layout.
