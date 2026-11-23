---
task: 2026-11-23-eval-subagent
stage: requirements
summary: "A /run-evals agent skill in .claude/ runs evals in a forked eval-runner agent and returns a short report."
---

# Requirements: Evals run in the main session

## Problem statement
The agent runs `evals/run.py` in the main session and reads the results there. The logs and failure reasons fill the main session context. The user must ask for a subagent each time, because nothing makes it the default (D1).

## Scope
In: a `run-evals` skill and an `eval-runner` agent in this repo's `.claude/` (D2, D4).
In: eval lines in `CLAUDE.md`, `.harness/workflows/pull-request.md` and `.harness/workflows/testing-and-evals.md` that name `/run-evals` (D2, A1).
In: a report-only mode for an existing run id (D5).
In: one pytest static test and two real proof runs (D5).
Out: changes under `plugin/` (D4). Changes to `evals/run.py`. A model choice for the agent.

## Requirements
- R1: The `run-evals` skill shall set `context: fork` and `agent: eval-runner`. (D2)
- R2: The `eval-runner` agent shall have Bash and Read, and shall have no Edit or Write. (D2)
- R3: When `/run-evals` gets eval names, the `eval-runner` shall run `uv run python evals/run.py` with those names. (D2)
- R4: When `/run-evals` gets an existing run id, the `eval-runner` shall report on `evals/results/<run-id>/` and shall start no eval. (D5)
- R5: The `eval-runner` report shall give the run id, one PASS or FAIL line per eval and the total cost. (D3)
- R6: The `eval-runner` report shall give the reasons for each failing metric from `summary.md`. (D3)
- R7: Where a metric fails, the `eval-runner` report shall quote at most 3 lines from the evidence files that show the cause. (D3)
- R8: The `eval-runner` report shall leave out PASS metric rows. (D3)
- R9: The skill and the agent shall live in `.claude/`, and no file under `plugin/` shall change. (D4)
- R10: The eval lines in `CLAUDE.md` and `.harness/workflows/pull-request.md` shall name `/run-evals`. (D2)
- R11: When the agent starts `/run-evals` with new runs itself, `CLAUDE.md` shall tell it to ask first. (D6)
- R12: The ask shall name the evals, the run count and a cost estimate from the last `summary.md`. (D6)
- R13: When the agent has asked, the agent shall wait for a yes before the run starts. (D6)
- R14: The `CLAUDE.md` rule shall treat a `/run-evals` that the user types, or a report-only call, as needing no extra yes. (D6)

## Non-functional needs
State only what a source states. Else: not applicable: <reason>.
- Accessibility: not applicable: no user interface.
- Performance: The report shall have at most about 300 words. (D3)
- Security: The `eval-runner` cannot edit files, so it cannot change a file to pass an eval. (D2)
- Observability: not applicable: `summary.md` already records results and cost.

## Assumptions, risks and dependencies
| ID | Kind | Item | Owner |
|---|---|---|---|
| A1 | assumption | Repo rule: a workflow change updates its `.harness` doc in the same commit, so `testing-and-evals.md` names `/run-evals`. | build |
| A2 | assumption | Repo rule: every markdown file has a budget in `.harness/budgets.yml`, so the two new `.claude/` files get one. | build |
| A3 | assumption | `KAIRYN_EVAL_RUNS=2` sets the run count for the proof run of `check`. | build |
| A4 | assumption | Claude Code loads a new project skill and agent only in the next session, so the proof runs happen after a restart. | Jayson |
| P1 | dependency | Claude Code supports `context: fork`, `agent:` and a background fork, as its skills docs state. | design |
| K1 | risk | A background fork gets fewer tools. If it cannot wait for a 30-minute run, the skill needs `background: false`. | design |
| K2 | risk | `testing-and-evals.md` is at 992/1000 tokens. The new line needs a cut. | build |
| K3 | risk | The agent can still run `evals/run.py` directly. The `CLAUDE.md` line lowers this risk but does not block it. | Jayson |

## Acceptance criteria
- [ ] A pytest test reads `.claude/skills/run-evals/SKILL.md` and finds `context: fork` and `agent: eval-runner`. (R1)
- [ ] The same test reads `.claude/agents/eval-runner.md` and finds Bash and Read in `tools`, and no Edit or Write. (R2)
- [ ] One real `/run-evals check` with `KAIRYN_EVAL_RUNS=2` runs in a background fork and creates a new run folder. (R3)
- [ ] `/run-evals 20261123T035336Z` reports the grill FAIL with its reasons and creates no new run folder. (R4)
- [ ] Both reports give the run id, PASS or FAIL per eval and the total cost, and have at most about 300 words. (R5)
- [ ] The report on `20261123T035336Z` gives the reasons for the grill FAIL from its `summary.md`. (R6)
- [ ] The report on `20261123T035336Z` quotes at most 3 evidence lines per failing metric. (R7)
- [ ] Neither report lists a PASS metric row. (R8)
- [ ] `git diff main --stat` shows no file under `plugin/`. (R9)
- [ ] `CLAUDE.md` and `pull-request.md` name `/run-evals` in their eval lines. (R10)
- [ ] `CLAUDE.md` tells the agent to ask before a run it starts itself. (R11)
- [ ] The ask names evals, run count and a cost estimate, then waits for a yes. (R12, R13)
- [ ] `CLAUDE.md` exempts a user-typed or report-only call. (R14)

## Open questions and answers
None

Approval: Jayson De los Reyes, 2026-11-23T07:09:33Z, "Approve"
