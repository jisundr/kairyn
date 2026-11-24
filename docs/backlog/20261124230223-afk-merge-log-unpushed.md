---
title: afk.py commits its merge log line after the merge and never pushes it
status: dropped
requester: Jayson De los Reyes
date: 2026-11-25
appetite:
review_by: 2027-02-23
---

# afk.py commits its merge log line after the merge and never pushes it

**Raw request:** "yes, file the afk.py push gap as inbox" (Jayson De los Reyes, 2026-11-25, Claude Code session)

**Problem (AI draft, needs a human to confirm):** `decide()` in `plugin/scripts/afk.py` merges the pull request, then commits "Merged with gh pr merge --merge" to `STATE.md`. It does not push that commit. The merged branch on GitHub lacks the line, and the local `kairyn/<task>` branch shows as not fully merged. `git branch -d` then refuses to delete it.

**Evidence:** Task 2026-11-24-multi-repo: commit 65d2a97 "kairyn(2026-11-24-multi-repo): merge" changed only `STATE.md` and was on no remote branch. The cleanup needed `git branch -D`.

# Log

2026-11-24T23:02:23Z [capture] Created after the cleanup of 2026-11-24-multi-repo. Status inbox, waiting for triage.
2026-11-24T23:07:13Z [triage] Dropped: merged into approve-retry, same function. Decided by Jayson De los Reyes.
