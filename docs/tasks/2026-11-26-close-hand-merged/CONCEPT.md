---
task: 2026-11-26-close-hand-merged
stage: grill
summary: "A close.py command records a hand merge from the merged PR (who, when, which PR); the close stage runs it when STATE.md is not done."
---

# Concept: close records a hand merge from the merged pull request

## Concept
A task built and merged by hand keeps `status: in-progress` and has no `REVIEW.md` decision, so `close.py check` fails. A new `close.py` command records the merge: it sets `status: done` and `stage: review` in `STATE.md` and writes a `Decision:` line in `REVIEW.md`. The name, time and words of that line come from the merged pull request through `gh`: who merged it, when, and its number. The close stage runs the command when the task's pull request is merged and `STATE.md` is not done. If the command finds no merged pull request, it fails and names what is missing.

## Decisions
- D1: A `close.py` command records a hand merge. It sets `STATE.md` `status: done` and `stage: review`, and writes the `Decision:` line in `REVIEW.md` that `close.py check` expects. (user, 2026-11-26)
- D2: The name, time and words of the `Decision:` line come from the merged pull request through `gh`: who merged it, its merge time and its number. (user, 2026-11-26)
- D3: The close stage runs the command when the task's pull request is merged and `STATE.md` is not done. (user, 2026-11-26)
- D4: When `STATE.md` does not name the pull request, the command finds it in the merged pull requests by the task's branch name. (user, 2026-11-26)
- D5: If the command finds no merged pull request, it fails with a message that names what is missing. It does not prompt. (user, 2026-11-26)

## Terms
| Term | Meaning |
|---|---|
| hand merge | A task's pull request merged on GitHub by a person, not by `afk.py` (`/kairyn:review approve`). |
| the task's pull request | The merged pull request that holds the task's change. |

## Open branches
- None. Source: the owner's grill on 2026-11-26, relayed by an Orca coordinator. Backlog idea `20261126022052-close-fails-on-hand-merged-tasks`.

Approval: Jayson De los Reyes, 2026-11-26T04:07:06Z, "Grill approved: a close.py command records a hand merge (status done, stage review, REVIEW.md Decision line); the line's name, time and words come from the merged PR via gh; the close stage runs it when the PR is merged and STATE.md is not done; find the PR by branch name when STATE.md does not name it; no merged PR found: fail naming what is missing"
