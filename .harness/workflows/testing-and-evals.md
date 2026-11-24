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
| Cost | Under a second, free | Minutes and tokens per eval |
| Runs | Always | Only when dependencies changed |
| Command | `uv run pytest` | `/run-evals` |

## Tests

```bash
uv run pytest
```

No `claude` calls.

- A stub `claude` that picks its action from words in the prompt breaks when two prompts share a word. Match a fixed marker, not a word.
- Test a new AFK path with one real run on a fixture built to hit it. Stub tests passed, but one real reviewer run found three defects.

## Evals

Evals use promptfoo (`npx`, pinned in `evals/run.py`), one `evals/promptfoo/<name>.yaml` each, each test repeated N times. Each repeat calls `provider.py`: one headless `claude` session in a fresh repo, evidence as JSON. `asserts.py` checks it with `evals/checks.py` and a `claude` judge (scores 1 to 5). The `build`, `gates` and `review` evals run `afk.py` with `evals/afk_claude.py` as its `claude`: it keeps each session's transcript and cost.

Each eval's gates live in its `evals/promptfoo/<name>.yaml`, the only source: `metadata.min_pass_rate: {metric: fraction}` per metric, `score_gate` for the judge. `evals/run.py` fails a metric below its rate, rounded up: a 2-run smoke needs 2 of 2.

Judge gate: criterion scores average at least 4, none below 3. Plain language: at most 1.0 ASD-STE100 violations per 100 words.

### Running only what changed

Each config starts with a header naming the plugin files it exercises:

```yaml
# depends: plugin/stages/REQUIREMENTS.md, plugin/stages/_template.md, plugin/templates/STATE.md
```

The selector skips an eval when their hash equals the one saved at its last pass (`evals/results/passed.json`, git-ignored).

```bash
/run-evals                   # every eval whose dependencies changed, at 10 runs
/run-evals init --runs 2     # a cheap smoke: one eval, 2 runs
/run-evals --all-evals       # everything (a release); with names, only those
/run-evals 20261123T035336Z  # report on a past run
```

`/run-evals` forks into `.claude/agents/eval-runner.md` (no Edit or Write), runs `evals/run.py` detached (`evals/bg.py`) and returns failures, evidence, cost.

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
4. The fixture must pass the repo's own checks. After adding a harness doc, run `harness_docs.py --write`, or the agent cannot find it.
5. Give an LLM judge every file the stage could read. A judge given only `report.py` scored true README facts as invented.
6. An eval runs every scenario in its yaml file. Put a new scenario in its own file for the watch-it-fail run, then merge it. When you move or rename an eval test, run its new file once before a release.

To lint a stage output by hand, import `evals/checks.py` with `evals` and `tests` on `sys.path`: it imports `tests/helpers.py`.
