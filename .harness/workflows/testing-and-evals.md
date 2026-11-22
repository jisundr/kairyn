---
title: Testing and evals
summary: "Tests versus evals, commands, thresholds, change-based selection and evidence."
read_when: "running, writing or interpreting tests or evals, or touching evals/"
load: on-demand
---

# Testing and evals

Two separate layers.

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

Covers the plugin's shape, init scripts, pure eval checks, selector and gates. It never calls `claude`.

## Evals

Evals use promptfoo (needs Node; run via `npx`, version pinned in `evals/run.py`). Each eval is `evals/promptfoo/<name>.yaml`. promptfoo repeats every test N times (default 10). Each repeat calls `evals/promptfoo/provider.py`: one headless `claude` session in a fresh repo, evidence returned as JSON. Assertions check it:

- Deterministic checks are `python` assertions in `asserts.py`, built on `evals/checks.py`.
- Quality is scored 1 to 5 per criterion by a `claude` judge in `asserts.py` (no API key).

Each test declares thresholds as `metadata.min_pass_rate: {metric: fraction}`, and each assertion names its `metric`. `evals/run.py` fails when a metric's pass rate is below its threshold.

Judge gate: criterion scores average at least 4, none below 3. Plain language: at most 1.0 ASD-STE100 violations per 100 words.

| Eval | Pass when |
|---|---|
| init | 90% pass `verify-init.sh --fresh`; 100% leave `.kairyn/` unchanged and keep `CLAUDE.md` with one kairyn block |
| check | 90% of replies name the doc that lost its header |
| requirements | 90%: `well_formed` (task folder, real timestamps), `traceable` (criteria tagged `(request)`, `(A<n>)`, `(D<n>)`), `uses_concept` (on the grill folder, cites `D<n>`); 80% plain language; judge, `no_invention` at least 4 |
| model-routing | 90%: `well_formed`, `starts_with_baseline` (stage 0), `waits_for_human` (open `D<n>`); 80% plain language; judge |
| grill | 90% over 4 scripted turns: `well_formed`, `one_question` (with a recommendation), `records_answers`, `waits_for_answer`, `hands_off` (names the folder); 80% plain language; judge |
| upgrade | 90% upgrade a v0.1.0 repo and name its conflict |

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
- List every plugin file an eval relies on in its `# depends:` header.

### Evidence and summary

Each run saves promptfoo's `<name>.json`, per-run evidence and `summary.md` to `evals/results/<run-id>/`. Read them before you claim a result.

### Settings

`KAIRYN_EVAL_RUNS` (default 10), `KAIRYN_MODEL`, `KAIRYN_JUDGE_MODEL`.

## Adding an eval

1. Write `evals/promptfoo/<name>.yaml`: `# depends:` header, thresholds, a `metric` per assertion.
2. Add a scenario function to `provider.py` and its checks to `asserts.py`.
3. Run it against the current instructions and confirm it can fail.
4. Pure checks go in `evals/checks.py`, tested in `tests/`.
