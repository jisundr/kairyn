# 9. A script runs the AFK loop, and exit codes decide each step

Date: 2026-11-24

## Status
Accepted

## Context
Task 2026-11-23-build-stage. After design approval, code was written outside kairyn. Nothing proved that tests came first or that each task passed (D1). The build had to run AFK, with no user turns (D2). Three options were possible: `afk.py` calls `claude -p` per stage, a Stop hook keeps one session looping, or a Claude Agent SDK orchestrator. The Stop hook lets the model control the loop. The SDK adds a dependency.

## Decision
- `plugin/scripts/afk.py`, standard-library Python 3.9, runs the loop (D7). The model only runs stage files.
- Each slice gets one fresh `claude -p` in a task worktree on `kairyn/<task>` (D13).
- A slice is done only when its done command fails at its `test(T<n>)` commit and exits 0 at its `feat(T<n>)` commit (D1, D12). A gate is decided by its command's exit code (D9).
- `afk.py`, not each stage, writes `STATE.md`, `BUILD.md` and `GATES.md`. This is a change from D6, logged in the task.
- Limits in `.kairyn/afk.yml` cap cost per stage and per run, and minutes per stage (D8). A limit sets `status: blocked`.

## Consequences
- Order, checks, limits, git and resume are tested with a stub `claude`, at no token cost.
- A run resumes from `STATE.md`. Running `/kairyn:build` again continues it.
- `claude -p` has no turn cap, only a cost cap.
