# 22. Close records a hand merge from the merged pull request

Date: 2026-11-26

## Status
Accepted

## Context
Task 2026-11-26-close-hand-merged. A task built and merged by hand kept `status: in-progress` and had no `REVIEW.md` with a `Decision:` line. Only `afk.py` `decide` (`/kairyn:review approve`) recorded a merge. So `close.py check` failed until the closing agent edited both files by hand, as in #49, #51 and #56.

## Decision
- A `close.py` command, `record-merge <task> [--pr <n>]`, records a hand merge. It sets `status: done`, `stage: review` and `review: done` in `STATE.md`, and writes the `Decision:` line in `REVIEW.md`. `check` does not change: it does not accept a merged pull request in place of the line (D1).
- The name, time and words of the line come from the merged pull request through `gh`: who merged it, its merge time and its number (D2).
- The close stage runs the command at step 1, before `check`. On a done task the command changes nothing, so the stage needs no status check (D3, A7).
- The command finds the pull request from `--pr` (the owner's change, R10), else the last `PR #<n>` in `STATE.md`, else the one merged pull request from branch `kairyn/<task>` or a branch whose last `/` part is the task folder name or its slug (D4, A1, A5).
- If it finds no merged pull request, or more than one, it prints `FAIL: <cause>`, changes no file and does not prompt (D5, A6).

## Consequences
- `close.py` now needs `gh`, signed in to the repo's GitHub remote, to close a hand-merged task (K2). `KAIRYN_GH` overrides the path, as in `afk.py`.
- The name is the merger's GitHub name, which can differ from `git config user.name` (A4).
- If the last `PR #<n>` in `STATE.md` is another pull request, the wrong merge is recorded. The log line names it, so the user sees it (K1).
