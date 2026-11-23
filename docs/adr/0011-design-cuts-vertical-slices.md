# 11. Design cuts tasks into vertical slices

Date: 2026-11-24

## Status
Accepted

## Context
Task 2026-11-23-build-stage. `DESIGN.md` split work into small tasks in dependency order. `afk.py` runs one session per `T<n>` and needs each done condition as a command (D1, D13).

## Decision
- T1 is the tracer bullet: the thinnest end-to-end path. Each later `T<n>` crosses every layer, or says why not (D13).
- Each `T<n>` names its blockers with `after: T<k>`, so the tasks form a graph. Each has `Done: `<command>``.
- `afk.py` runs the slices in sequence, in graph order (D13). Parallel worktrees are a later step.
- The design eval checks the `after:` lines, the done commands and T1.

## Consequences
- Each slice proves that the layers work together before the next slice starts.
- A one-layer `T<n>` needs a written reason (D13).
