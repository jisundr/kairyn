# Testing and evals

Two layers, kept apart because they behave differently.

| | Tests (`tests/`) | Evals (`evals/`) |
|---|---|---|
| Result | Same every time | A pass rate over N runs |
| Speed and cost | Under a second, free | About 3 to 7 minutes per feature, uses tokens |
| Runs | Always | Only when dependencies changed |
| Command | `uv run pytest` | `uv run pytest -m eval` |

## Tests

```bash
uv run pytest
```

Covers the plugin's static shape (manifests, stage front matter and required sections, the `STATE.md` template), `verify-init.sh` and `init.sh` against good and broken layouts, the timestamp checker, and the eval selector. Evals are deselected by default (`addopts = -m 'not eval'`), so this never calls `claude`.

Write the test first and watch it fail before writing the code. The selector was built this way.

## Evals

An eval runs real headless `claude` sessions N times (default 10) and checks a pass rate. Each is a BDD feature in `evals/features/<name>.feature` with its steps in `evals/test_<name>.py` (the filename convention is how they are paired).

Current evals and thresholds:

| Feature | Check | Pass when |
|---|---|---|
| init | verified layout | at least 90% of repos pass `verify-init.sh` |
| init | never overwrites | 100% leave `.kairyn/` unchanged, including user edits |
| requirements | well-formed | at least 90% leave a valid task folder, `STATE.md` and `REQUIREMENTS.md` with real timestamps |
| requirements | quality | LLM judge mean at least 4, no score below 3 |

### Running only what changed

Each feature starts with a header naming the plugin files it exercises:

```gherkin
# depends: plugin/stages/REQUIREMENTS.md, plugin/stages/_template.md, plugin/templates/STATE.md
```

The selector hashes those files and compares with the hash saved when the feature last passed (`evals/results/passed.json`, local and git-ignored). Unchanged means skipped.

```bash
uv run pytest -m eval                # only evals whose dependencies changed
uv run pytest -m eval --all-evals    # everything, e.g. before a release
```

Rules the selector follows:
- A hash is recorded only when every scenario in the feature passed.
- It is recorded only at the full run count. Smoke runs (`KAIRYN_EVAL_RUNS` below 10) never vouch for a feature.
- Add every plugin file an eval relies on to its `# depends:` header, or a change there will not trigger a re-run.

### Evidence and summary

Every run prints a short summary and saves its evidence to `evals/results/<run-id>/`: task folders per run, `problems.txt`, `window.txt`, judge outputs and `scores.json`, plus `summary.md`. Check these before claiming a result.

### Settings

`KAIRYN_EVAL_RUNS` (default 10), `KAIRYN_MODEL`, `KAIRYN_JUDGE_MODEL`.

### Cost warning

A full requirements eval takes about 7 minutes. Never run plain `pytest -m eval --all-evals` casually, and never remove the default `-m 'not eval'`: an unmarked eval will call `claude` on every test run.

## Adding an eval

1. Write `evals/features/<name>.feature` with a `# depends:` header.
2. Write `evals/test_<name>.py` with `scenarios("features/<name>.feature")` and the steps.
3. Run it against the current instructions and confirm it can fail.
4. Put reusable pure checks in `evals/checks.py` and give them tests in `tests/`.
