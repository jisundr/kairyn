---
title: Testing and evals
summary: "Tests versus evals, commands, thresholds, change-based selection and evidence."
read_when: "running, writing or interpreting tests or evals, or touching evals/"
load: on-demand
---

# Testing and evals

Two layers, kept apart because they behave differently.

| | Tests (`tests/`) | Evals (`evals/`) |
|---|---|---|
| Result | Same every time | A pass rate over N runs |
| Speed and cost | Under a second, free | About 3 to 7 minutes per eval, uses tokens |
| Runs | Always | Only when dependencies changed |
| Command | `uv run pytest` | `uv run python evals/run.py` |

## Tests

```bash
uv run pytest
```

Covers the plugin's static shape, the init scripts, the pure eval checks, the selector and the pass-rate gate. It never calls `claude`. Write the test first and watch it fail.

## Evals

Evals use promptfoo (needs Node; run via `npx`, version pinned in `evals/run.py`). Each eval is `evals/promptfoo/<name>.yaml`. promptfoo repeats every test N times (default 10). Each repeat calls `evals/promptfoo/provider.py`: one headless `claude` session in a fresh repo, evidence returned as JSON. Assertions check it:

- Deterministic checks are `python` assertions in `asserts.py`, built on `evals/checks.py`.
- Quality is scored 1 to 5 per criterion by a `claude` judge in `asserts.py` (no API key).

Each test declares its thresholds as `metadata.min_pass_rate: {metric: fraction}`, and each assertion names its `metric`. `evals/run.py` turns promptfoo's JSON into a pass rate per metric and fails when a metric is below its threshold.

| Eval | Metric | Pass when |
|---|---|---|
| init | verified_layout | at least 90% of repos pass `verify-init.sh` |
| init | never_overwrites | 100% leave `.kairyn/` unchanged, including user edits |
| init | keeps_claude_md | 100% keep the original text and add exactly one kairyn block |
| check | names_broken_doc | at least 90% of replies name the doc that lost its header |
| requirements | well_formed | at least 90% leave a valid task folder, `STATE.md` and `REQUIREMENTS.md` with real timestamps |
| requirements | quality | judge scores (verifiable, scope, no_invention) average at least 4, none below 3 |
| requirements | plain_language | 80% of runs have at most 1.0 ASD-STE100 violations per 100 words (`checks.ste_problems`) |

### Running only what changed

Each config starts with a header naming the plugin files it exercises:

```yaml
# depends: plugin/stages/REQUIREMENTS.md, plugin/stages/_template.md, plugin/templates/STATE.md
```

The selector hashes those files and compares with the hash saved when the eval last passed (`evals/results/passed.json`, local and git-ignored). Unchanged means skipped.

```bash
uv run python evals/run.py                      # only evals whose dependencies changed
uv run python evals/run.py init                 # a named eval
uv run python evals/run.py --all-evals          # everything, e.g. before a release
uv run python evals/run.py --concurrency 4      # parallel claude sessions
```

- A hash is recorded only when every metric met its threshold, and only at the full run count (`KAIRYN_EVAL_RUNS` below 10 never vouches).
- Add every plugin file an eval relies on to its `# depends:` header, or a change there will not trigger a re-run.

### Evidence and summary

Each run saves to `evals/results/<run-id>/`: promptfoo's `<name>.json`, per-run evidence and `summary.md`. Check these before claiming a result.

### Settings

`KAIRYN_EVAL_RUNS` (default 10), `KAIRYN_MODEL`, `KAIRYN_JUDGE_MODEL`. Evals cost tokens: never run `--all-evals` casually.

## Adding an eval

1. Write `evals/promptfoo/<name>.yaml` with a `# depends:` header, tests with `metadata.min_pass_rate`, and a named `metric` on every assertion.
2. Add a scenario function to `provider.py` and its checks to `asserts.py`.
3. Run it against the current instructions and confirm it can fail.
4. Reusable pure checks go in `evals/checks.py`, with tests in `tests/`.
