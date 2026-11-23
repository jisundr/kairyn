# 10. Build, gates and review stop once, for the merge decision

Date: 2026-11-24

## Status
Accepted

## Context
Task 2026-11-23-build-stage. Build runs AFK, with no user turns (D2). Gates and review were in scope with build (D4). ADR 0006 made design the last stage, with one approval stop.

## Decision
- `build`, `gates` and `review` are three stages, each with its own output file and eval (D6). Design approval moves the task to `build`.
- The one planned stop is the merge decision. `/kairyn:review <task> approve "<words>"` writes `Decision:` in `REVIEW.md`, merges the pull request and sets `status: done` (D5, D11).
- The run stops early only for an approval gate, the fix-round cap, a limit or a wrong plan. Each stop sets `status: blocked` and writes the reason (D5).
- A slice that touches a path in `approval:` stops before it runs, until `/kairyn:build <task> approve T<n>` (D10).
- The AFK loop opens one pull request per task (D15).

## Consequences
- Design is no longer the last stage. A task is `done` only after the merge decision. `exit.py` accepts a `Decision:` line as the last approval.
- The human reads one diff and one `REVIEW.md` per task.
- With no remote or no `gh`, the run pushes nothing, and approve only records the decision (D11).
