---
task: 2026-11-23-eval-subagent
stage: design
summary: "A forked run-evals skill and a read-and-run eval-runner agent in .claude/, with instructions only; CLAUDE.md asks before each run."
---

# Design: Evals run in the main session

## Approach
Option A. Two new files in `.claude/` meet R1 to R9 with instructions only. The Claude Code docs answer K1: a background fork keeps Bash, Read and Monitor. A Bash command with `run_in_background` runs up to 2 hours, so the agent waits out a 40-minute run. The proof runs (T7, T8) test the report format, and report-only mode makes a second try free. `evals/run.py` skips an eval whose dependencies are unchanged, so the `check` proof run needs `--all-evals`.

## Options
| Option | What | Cost | Risk |
|---|---|---|---|
| A (smallest thing) | `run-evals` skill with `context: fork`, `eval-runner` agent with `tools: Bash, Read, Grep, Glob, Monitor`. The agent reads `summary.md` and `<name>.json` and writes the report. | 2 new files, 1 test, 3 doc edits. | The agent formats the report by hand. A wrong format shows in T8. |
| B | Option A plus `evals/report.py` (new): it prints the FAIL rows, reasons and cost from a run folder. The agent only adds the evidence quotes. | A new script and its tests. | More code for a report that 2 proof runs can check. |
| C | Option A with `background: false`. | Same as A. | The main session waits up to 40 minutes. It fixes D1 (a) but blocks the user. |

## Tasks
- T1: Write the failing static test. Files: `tests/test_dev_harness.py` (new). Done: it fails because the two `.claude/` files do not exist.
- T2: Write the agent: `tools: Bash, Read, Grep, Glob, Monitor`, the run mode, the report-only mode and the D3 report format. Files: `.claude/agents/eval-runner.md` (new). Done: the T1 agent check passes.
- T3: Write the skill: `context: fork`, `agent: eval-runner`, `$ARGUMENTS`, and `--runs N` as `KAIRYN_EVAL_RUNS`. A run id selects report-only mode. Files: `.claude/skills/run-evals/SKILL.md` (new). Done: `uv run pytest` passes.
- T4: Add budgets for `.claude/skills/*/SKILL.md` and `.claude/agents/*.md`. Files: `.harness/budgets.yml`. Done: `plugin/scripts/budgets.py` reports both files within budget.
- T5: Name `/run-evals` and the ask rule in the eval lines. Cut text to stay in budget: `CLAUDE.md` is at 699/700 and `testing-and-evals.md` at 992/1000 (K2). Files: `CLAUDE.md`, `.harness/workflows/pull-request.md`, `.harness/workflows/testing-and-evals.md`. Done: `harness_docs.py --write` and `budgets.py` pass.
- T6: Check the diff. Done: `git diff main --stat` shows no file under `plugin/`.
- T7: Restart the session (A4). Run `/run-evals check --all-evals --runs 2`. Done: a new run folder exists and the report arrives in the background.
- T8: Run `/run-evals 20261123T035336Z`. Done: no new run folder, and the report shows the grill FAIL with reasons and quotes.

## Test plan
| Criterion | Task | Test |
|---|---|---|
| AC1 skill has `context: fork`, `agent: eval-runner` | T1, T3 | `tests/test_dev_harness.py` (new) |
| AC2 agent has Bash and Read, no Edit or Write | T1, T2 | `tests/test_dev_harness.py` (new) |
| AC3 real `check` run in a background fork | T7 | New folder in `evals/results/`; main session not blocked |
| AC4 report-only on `20261123T035336Z` | T8 | `ls evals/results` before and after |
| AC5 run id, PASS or FAIL per eval, cost, about 300 words | T7, T8 | Read both reports; `wc -w` |
| AC6 grill FAIL reasons from `summary.md` | T8 | Compare with `evals/results/20261123T035336Z/summary.md` |
| AC7 at most 3 evidence lines per failing metric | T8 | Read the T8 report |
| AC8 no PASS metric rows | T7, T8 | Read both reports |
| AC9 no file under `plugin/` | T6 | `git diff main --stat` |
| AC10 `CLAUDE.md` and `pull-request.md` name `/run-evals` | T5 | `grep -n run-evals` |
| AC11 ask before a run the agent starts | T5 | Read the `CLAUDE.md` eval rule |
| AC12 ask names evals, runs, cost, then waits | T5 | Read the `CLAUDE.md` eval rule |
| AC13 exempts user-typed and report-only calls | T5 | Read the `CLAUDE.md` eval rule |

Approval: Jayson De los Reyes, 2026-11-23T08:32:29Z, "proceed"
