---
name: run-evals
description: Run kairyn's promptfoo evals in a background subagent, or report on a past run, and get back a short PASS/FAIL report with cost. Use whenever evals must run or a run's results must be read.
context: fork
agent: eval-runner
argument-hint: "<eval names> [--all-evals] [--runs N] | <run-id>"
---

Arguments: $ARGUMENTS

- If the arguments are one run id such as `20261123T035336Z`, report on `evals/results/<run-id>/`. Start no eval.
- Else run `uv run python evals/run.py` with the eval names and `--all-evals` if given. `--runs N` sets `KAIRYN_EVAL_RUNS=N`; it is not a `run.py` flag. `--all-evals` only ignores the last-pass record: the names still choose the evals.
- With no arguments, run every eval whose dependencies changed.

Follow your agent instructions for the run, the wait and the report.
