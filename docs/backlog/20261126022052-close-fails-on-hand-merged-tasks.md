---
title: Close fails on hand-merged tasks until STATE.md is marked done
status: triaged
requester: Jayson De los Reyes
date: 2026-11-26
appetite: small batch
review_by:
---

# Close fails on hand-merged tasks until STATE.md is marked done

**Raw request:** capture close failing on hand-merged tasks until STATE.md is marked done as a backlog idea (owner, 2026-11-26, through Orca).

**Problem (confirmed by Jayson De los Reyes, 2026-11-26):** A task built and merged by hand, not by an AFK run, keeps `status: in-progress` and has no `REVIEW.md`. `close.py check` fails until the closing worker marks it done and writes a `REVIEW.md` with the merge decision. It happened in the last three closes: #49, #51 and #56.

**Evidence:**
- `close.py` `task_problem` (lines 53–65): `status:` in `STATE.md` must be `done`, and the output file of `stage:` must have a line matching `APPROVED_RE` (line 39): `Approval:` or `Decision:` with a name, a timestamp and quoted words, not `pending`.
- Only `afk.py` `decide` sets `status: done` after a build (line 1016, `/kairyn:review approve`), and it needs a `REVIEW.md` with `Decision: pending` (line 1006), which only the AFK review stage writes (`plugin/stages/REVIEW.md`, step 5). `_approval.md` sets `in-progress` after each approval. Nothing records a merge made outside `afk.py`.
- Before each close, `STATE.md` had `status: in-progress`: backlog-page at `stage: review` with the merge only as a log line (`Approval: Jayson De los Reyes, 2026-11-25T12:44:46Z, "approved PR #48"`) and no `REVIEW.md`; split-build-routing and close-changelog-double-name at `stage: build`, `build: pending`, with no `BUILD.md` approval line and no `REVIEW.md`.
- PR #49, #51 and #56 each say the worker set `status: done` and added a `REVIEW.md`; `.kairyn/learnings.md` has the note.

**Notes:** Inference, options: a `close.py` (or `afk.py`) command that records a hand merge (`status: done`, `stage: review`, a `Decision:` line from the merged PR); let `check` accept a merged PR as the approval; or a step in the close stage for hand-built tasks.

# Log

- 2026-11-26T02:20:52Z [capture] Created from the owner's request through Orca. Status inbox, waiting for triage.
- 2026-11-26T02:38:49Z [triage] Kept. Status triaged. Problem confirmed. Not Next. Decided by Jayson De los Reyes.
- 2026-11-26T02:38:49Z [appetite] Set to small batch. Decided by Jayson De los Reyes.
