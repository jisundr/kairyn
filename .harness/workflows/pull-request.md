---
title: Pull request
summary: "Pre-flight checks, opening and updating a PR, commit conventions and what not to do."
read_when: "committing, or opening or updating a pull request"
load: on-demand
---

# Pull request

The repo is on GitHub (`jisundr/kairyn`), so changes go through pull requests, not merge requests. Branches are named `feat/<short-description>`.

## Before opening

```bash
uv run pytest                       # tests, fast
claude plugin validate plugin       # manifest and component validation
/run-evals                         # evals whose dependencies changed, in a subagent
```

- If you changed a file that init installs (stages, templates, `plugin/harness/`), run `uv run python scripts/release_hashes.py --write`. A test fails until `plugin/release-hashes.json` has the new hashes. It needs full git history.
- If you changed anything under `plugin/`, run the evals that depend on it with `/run-evals`. Skipped evals are fine only when the selector says the dependencies are unchanged.
- Before a release, run everything with `/run-evals --all-evals`.
- Put the eval summary in the PR description when evals ran. Quote numbers, not "passed".

## CI

`.github/workflows/ci.yml` runs on every PR and on pushes to `main`:
- `tests`: `uv run pytest` on Linux and macOS (catches shell portability bugs)
- `consumer install`: init and the checkers with plain Python 3.9 (the minimum; macOS's `/usr/bin/python3`) and 3.13, from uv, no dependencies, as a user would run them
- `shellcheck`: the shell scripts

If push or pull request events start no Actions run, test a trigger first (`workflow_dispatch`, a draft pull request). On the new public repo the cause was not billing.

## Protection of `main`

`main` takes changes only through a pull request, with 0 approvals required. The merge waits for these checks: `tests (ubuntu-latest)`, `tests (macos-latest)`, `consumer install (plain python3 3.9)`, `consumer install (plain python3 3.13)`, `version-bump`, `shellcheck`. The rules apply to admins. `main` blocks force push and deletion. `python3 scripts/github_settings.py --check` compares the live settings with these rules.

Every change, also a `STATE.md` log line, goes on a branch and merges by pull request.

Evals are **not** in CI: they need credentials and cost tokens. Run them locally and put the summary in the PR.

## Opening

1. Branch from `main`, commit, push.
2. Open the PR with `gh pr create --base main`. The title says what changed. The body has a short summary and a test plan with the commands above.
3. Keep the title and description current. If the scope grows, update them.

## Commits

One logical change per commit, message in the imperative. Commits made with Claude Code end with a `Co-Authored-By` trailer, and PR descriptions end with the Claude Code attribution line.

## Feature branches and reverts

A large change merges in slices into one feature branch, then one pull request takes it to `main`. Every merge is a merge commit, never a squash. Then one `git revert -m 1 <merge>` undoes a slice or the whole feature.

After you revert a merge, git counts its commits as merged. To merge that work again, first revert the revert, then merge the fixes.

## Do not

- Commit `evals/results/`, `.venv/` or caches (all git-ignored).
- Merge with failing tests or a failing eval you have not explained.
- Rename or move `plugin/` files without updating the `# depends:` headers in `evals/promptfoo/*.yaml` and the README layout.
