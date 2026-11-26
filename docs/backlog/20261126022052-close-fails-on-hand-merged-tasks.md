---
title: Close fails on hand-merged tasks until STATE.md is marked done
status: inbox
requester: Jayson De los Reyes
date: 2026-11-26
appetite:
review_by:
---

# Close fails on hand-merged tasks until STATE.md is marked done

**Raw request:** capture close failing on hand-merged tasks until STATE.md is marked done as a backlog idea (owner, 2026-11-26, through Orca).

**Problem (AI draft, needs a human to confirm):** When a task's pull request is built and merged by hand, not through an AFK run, its `STATE.md` still says `status: in-progress` and the task has no `REVIEW.md`. `close.py check` then fails, and the closing worker marks `STATE.md` done and writes a `REVIEW.md` that copies the owner's merge decision by hand. This happened in the last three closes: PR #49 (backlog-page), PR #51 (split-build-routing) and PR #56 (close-changelog-double-name).

**Evidence:**
- `close.py` `task_problem` (lines 53–65) has two blocks. First, `status:` in `STATE.md` must be `done`, else `FAIL: <task> has status in-progress, not done`. Second, the output file of `stage:` (upper case, `.md`) must have a line that matches `APPROVED_RE` (line 39): `Approval:` or `Decision:` with a name, a timestamp and quoted words, not `pending`.
- Only `afk.py` `decide` sets `status: done` after a build (line 1016, `/kairyn:review approve`), and it needs a `REVIEW.md` with `Decision: pending` (line 1006), which only the AFK review stage writes (`plugin/stages/REVIEW.md`, step 5). `_approval.md` sets `status: in-progress` after each approval, and `_template.md:51` sets `done` only after the last stage. No stage or script records a merge made outside `afk.py`.
- Before each close, `STATE.md` had `status: in-progress`: backlog-page at `stage: review` with the merge only as a log line (`Approval: Jayson De los Reyes, 2026-11-25T12:44:46Z, "approved PR #48"`) and no `REVIEW.md`; split-build-routing and close-changelog-double-name at `stage: build`, `build: pending`, with no `BUILD.md` approval line and no `REVIEW.md`.
- PR #49, #51 and #56 each say the worker set `status: done` and added a `REVIEW.md` with the owner's decision so `close.py check` passes. `.kairyn/learnings.md` has the same note from the #56 close.

**Notes:** Inference, options: a `close.py` (or `afk.py`) command that records a hand merge (`status: done`, `stage: review`, a `Decision:` line from the merged PR); let `check` accept a merged PR as the approval; or a step in the close stage for hand-built tasks.

# Log

- 2026-11-26T02:20:52Z [capture] Created from the owner's request through Orca. Status inbox, waiting for triage.
