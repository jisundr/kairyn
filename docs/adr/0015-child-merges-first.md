# 15. Approve merges the child repo first, then the home repo

Date: 2026-11-25

## Status
Accepted

## Context
Task 2026-11-24-multi-repo. A child-repo task has two branches: code in the child repo, task files in the home repo (D4). Each repo gets its own push and pull request (D6, A4). A home merge with unmerged child code records a merge that did not happen.

## Decision
- Approve merges the child branch first. Only then does it merge the home branch (D6, R12).
- If the child merge fails, the run blocks and the home branch stays unmerged (R13).
- If the child repo has no `origin` remote, the run blocks with "merge it by hand". The home branch stays unmerged (review F1).
- On a retry, a child pull request that is already merged is skipped (review F3).
- `REVIEW.md` goes on the child pull request (D6).

## Consequences
- The home repo never shows a task as merged while its code is not.
- A retry after a failed merge needs `Decision: pending` reset in `REVIEW.md` by hand (review F5).
