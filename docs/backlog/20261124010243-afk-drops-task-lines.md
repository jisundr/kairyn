---
title: afk.py drops a malformed task line with no error
status: inbox
requester: Jayson De los Reyes
date: 2026-11-24
appetite:
review_by:
---

# afk.py drops a malformed task line with no error

**Raw request:** Found in task 2026-11-24-public-ready. The user approved the fix of T6 by hand.

**Problem (AI draft, needs a human to confirm):** `task_graph` in `plugin/scripts/afk.py` reads only lines that match `^- (T\d+):`. The design line `- T6 (approval): ...` did not match. The build skipped T6 and its approval stop, and reported no error. An approval slice can so skip its human gate.

**Evidence (checked 2026-11-24):**
- `BUILD.md` of the task has rows for T1 to T5 only. The reviewer found T6 open (F1).
- `DESIGN.md` step 6 says "Mark `(approval)`" but does not say where on the line.

**Notes:** Inference: fail when a line starts with `- T<n>` but does not match, or when the test plan names a task that `task_graph` does not return.

# Log

2026-11-24T01:02:43Z [capture] Created by Claude from the T6 skip. Status inbox, waiting for triage.
