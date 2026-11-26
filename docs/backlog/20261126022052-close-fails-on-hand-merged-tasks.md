---
title: Close fails on hand-merged tasks until STATE.md is marked done
status: committed
requester: Jayson De los Reyes
date: 2026-11-26
effort: medium
impact: high
review_by:
---

# Close fails on hand-merged tasks until STATE.md is marked done

**Raw request:** capture this as a backlog idea (owner, 2026-11-26, through Orca).

**Problem (confirmed by Jayson De los Reyes, 2026-11-26):** A task built and merged by hand, not by an AFK run, keeps `status: in-progress` and has no `REVIEW.md`. `close.py check` fails until the closing worker marks it done and writes a `REVIEW.md` with the merge decision. It happened in the last three closes: #49, #51 and #56.

**Evidence:**
- `close.py` `task_problem`: `STATE.md` must say `status: done`, and the output of `stage:` must have an `Approval:` or `Decision:` line (`APPROVED_RE`).
- Only `afk.py` `decide` (`/kairyn:review approve`) sets `status: done` after a build, and it needs a `REVIEW.md` with `Decision: pending`, which only the AFK review stage writes.
- Before each of the three closes, `STATE.md` had `status: in-progress` and the task had no `REVIEW.md`.

**Decided (2026-11-26, grill):** A `close.py` command records a hand merge: `status: done`, `stage: review`, a `Decision:` line from the merged PR through `gh` (merger, merge time, PR number). The close stage runs it when `STATE.md` is not done. It finds the PR from `STATE.md`, else by branch name; none found: it fails. Details: the task's `CONCEPT.md`.

**Task:** [docs/tasks/2026-11-26-close-hand-merged/](../tasks/2026-11-26-close-hand-merged/)

# Log

- 2026-11-26T02:20:52Z [capture] Created from the owner's request through Orca. Status inbox, waiting for triage.
- 2026-11-26T02:38:49Z [triage] Kept. Status triaged. Problem confirmed. Not Next. Decided by Jayson De los Reyes.
- 2026-11-26T02:38:49Z [appetite] Set to small batch. Decided by Jayson De los Reyes.
- 2026-11-26T03:01:29Z [triage] Effort medium, impact high confirmed by Jayson De los Reyes.
- 2026-11-26T04:07:06Z [grill] Grilled on 2026-11-26: five decisions, D1-D5 in the task's CONCEPT.md. Decided by Jayson De los Reyes.
- 2026-11-26T04:07:06Z [commit] Committed to task 2026-11-26-close-hand-merged. Decided by Jayson De los Reyes.
