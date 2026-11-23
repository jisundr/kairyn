---
task: 2026-11-23-eval-subagent
stage: grill
summary: "Run evals through a forked /run-evals agent skill in .claude/ that returns a short report."
---

# Concept: Evals run in the main session

## Concept
Eval runs fill the main session context, and the user must ask for a subagent each time. An agent skill fixes both: `/run-evals` forks into an `eval-runner` agent that can run and read but not edit, and returns at most about 300 words. It lives only in this repo's `.claude/`, and `CLAUDE.md` and `pull-request.md` name it. The agent asks with a cost estimate before each run it starts itself. A static test, one 2-run `check` run and a report-only pass on a past run prove it.

## Decisions
- D1: Two problems. Eval logs and failure reasons fill the main session context. The user must ask for a subagent each time, because nothing makes it the default. A blocked main session is not a goal: a background subagent solves it. (user)
- D2: An agent skill. A `run-evals` skill with `context: fork` runs in an `eval-runner` agent. The agent has Bash and Read but no Edit or Write, so it cannot change files to pass an eval. The eval lines in `CLAUDE.md` and `pull-request.md` name `/run-evals`. Source: knowledge base `02 Writing Agent Instruction Files.md` (a separate agent only for isolated context, different permissions or parallel work) and the Claude Code skills docs. (user accepted)
- D3: The `eval-runner` returns the run id, one PASS or FAIL line per eval, each failing metric with its reasons from `summary.md`, and the total cost. For each failure it quotes at most 3 lines from the evidence files that show the cause. About 300 words at most (guess). It leaves out PASS rows. (user accepted)
- D4: The agent skill lives only in this repo's `.claude/`, not in `plugin/`. It drives `evals/run.py` and `summary.md`, which exist only here. No version bump or release hashes. (user)
- D5: Three proofs. A pytest static test checks `context: fork`, `agent: eval-runner` and no Edit or Write in the agent `tools`. One real `/run-evals check` at 2 runs shows the background fork and a report of at most about 300 words with the run id (about $1, guess). `/run-evals <run-id>` reports on an existing run without new evals, which proves the failure section on run `20261123T035336Z`. (user accepted)
- D6: Before each `/run-evals` that the agent starts itself, it names the evals, the run count and a cost estimate from the last `summary.md`, then waits for a yes. A `/run-evals` that the user types is the yes. Report-only mode needs no yes. The rule goes in the `CLAUDE.md` eval line. (user accepted)

## Terms
| Term | Meaning |
|---|---|
| agent skill | A skill that runs in a subagent: `context: fork` and `agent: <name>` in its front matter. |
| eval run | One `uv run python evals/run.py` call. Results go to `evals/results/<run-id>/summary.md`. |

## Open branches
None
