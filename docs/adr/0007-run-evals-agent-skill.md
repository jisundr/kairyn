# 7. Evals run through a forked agent skill that cannot edit

Date: 2026-11-23

## Status
Accepted

## Context
Task 2026-11-23-eval-subagent. The agent ran `evals/run.py` in the main session. Eval logs and failure reasons filled the main session context. The user had to ask for a subagent each time, because nothing made it the default (D1). The knowledge base playbook says: build a separate agent only for isolated context, different permissions or parallel work. ADR 0004 already rejects a model choice as a reason.

## Decision
- A `run-evals` skill with `context: fork` runs in an `eval-runner` agent (D2). The fork gives the isolated context. The agent gives different permissions: no Edit or Write. It cannot change a file to pass an eval.
- The agent returns the run id, PASS or FAIL per eval, failure reasons, at most 3 quoted evidence lines per failing metric, and the cost. It leaves out PASS rows (D3).
- The skill and agent live only in this repo's `.claude/`, not in `plugin/` (D4).
- Before a run the agent starts itself, it names the evals, the run count and the cost, then waits for a yes. A typed `/run-evals` or a run id needs no yes (D6).

## Consequences
- Claude Code loads a new skill or agent only in a new session.
- `CLAUDE.md` and `testing-and-evals.md` are at their budgets after the eval lines changed.
- The report is model-written. The proof runs found a quoted PASS row and a misread flag, and the instructions now cover both.
- The agent can still run `evals/run.py` directly. The `CLAUDE.md` rule lowers this risk but does not block it.
