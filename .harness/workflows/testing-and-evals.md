---
title: Testing and evals
summary: "Tests versus evals, commands, thresholds, change-based selection and evidence."
read_when: "running, writing or interpreting tests or evals, or touching evals/"
load: on-demand
---

# Testing and evals

| | Tests (`tests/`) | Evals (`evals/`) |
|---|---|---|
| Result | Same every time | A pass rate over N runs |
| Speed and cost | Under a second, free | 3 to 7 minutes per eval, uses tokens |
| Runs | Always | Only when dependencies changed |
| Command | `uv run pytest` | `/run-evals` |

## Tests

```bash
uv run pytest
```

Plugin shape, scripts, eval checks, selector, gates. No `claude` calls.

## Evals

Evals use promptfoo (via `npx`, pinned in `evals/run.py`), one `evals/promptfoo/<name>.yaml` each, each test repeated N times. Each repeat calls `provider.py`: one headless `claude` session in a fresh repo, evidence as JSON. `asserts.py` checks it with `evals/checks.py` and a `claude` judge (1 to 5 per criterion).

Each test sets `metadata.min_pass_rate: {metric: fraction}`; `evals/run.py` fails a metric below it.

Judge gate: criterion scores average at least 4, none below 3. Plain language: at most 1.0 ASD-STE100 violations per 100 words.

| Eval | Pass when |
|---|---|
| init | 90% pass `verify-init.sh --fresh`; 100% keep `.kairyn/` and `CLAUDE.md` (one kairyn block) |
| check | 90% name the doc that lost its header |
| requirements | 90%: `well_formed` (ends blocked on approval, real timestamps), `traceable` (criteria cite `request`, `A<n>`, `D<n>` or `R<n>`), `specified` (EARS, non-functional needs, owners), `waits_for_approval`, `uses_concept`; over 3 turns `approval_gate` and `records_approval`; 80% plain language; judge, `no_invention` at least 4 |
| design | 90%: `design_` well_formed, traceable, options, grounded (paths exist or say `(new)`), waits; over 4 turns approval_gate, `rewrites_option`, records_approval; judge |
| model-routing | 90%: `well_formed`, `starts_with_baseline` (stage 0), `waits_for_human` (open `D<n>`); 80% plain language; judge |
| grill | 90% over 4 scripted turns: `well_formed`, `one_question` (with a recommendation), `records_answers`, `waits_for_answer`, `hands_off` (names the folder); 80% plain language; judge |
| upgrade | 90% upgrade a v0.1.0 repo, name its conflict |
| exit | 90%: task and closed backlog gone, changelog line, ADR only when due |

### Running only what changed

Each config starts with a header naming the plugin files it exercises:

```yaml
# depends: plugin/stages/REQUIREMENTS.md, plugin/stages/_template.md, plugin/templates/STATE.md
```

The selector skips an eval when their hash equals the one saved at its last pass (`evals/results/passed.json`, git-ignored).

```bash
/run-evals                   # only evals whose dependencies changed
/run-evals init --runs 2     # one eval, 2 runs
/run-evals --all-evals       # everything (a release)
/run-evals 20261123T035336Z  # report on a past run
```

`/run-evals` forks into `.claude/agents/eval-runner.md` (no Edit or Write), runs `evals/run.py` in the background and returns failures, evidence, cost.

A hash is saved only when every metric passed at 10 runs. List every plugin file an eval uses in `# depends:`.

### Evidence and summary

Each run saves `<name>.json`, evidence and `summary.md` to `evals/results/<run-id>/`. Read them before you claim a result.

`summary.md` ends with cost per scenario and a total, from each run's `cost.jsonl` (`total_cost_usd`, an estimate). A session records its last turn only: on `--resume` the value is cumulative.

### Settings

`KAIRYN_EVAL_RUNS` (default 10), `KAIRYN_EVAL_CONCURRENCY` or `--concurrency` (default 4), `KAIRYN_MODEL`, `KAIRYN_JUDGE_MODEL`.

## Adding an eval

1. Write `evals/promptfoo/<name>.yaml`: `# depends:` header, thresholds, a `metric` per assertion.
2. Add a scenario function to `provider.py` and its checks to `asserts.py`.
3. Run it on current instructions; confirm it can fail.
4. Pure checks: `evals/checks.py`, tested in `tests/`.
