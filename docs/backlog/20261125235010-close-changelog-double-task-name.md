---
title: Close writes the task name twice in the changelog line
status: committed
requester: Jayson De los Reyes
date: 2026-11-26
appetite: small batch
review_by:
---

# Close writes the task name twice in the changelog line

**Raw request:** capture the close.py double task name as a backlog idea (owner, 2026-11-26, through Orca).

**Problem (confirmed by Jayson De los Reyes, 2026-11-26):** The worker that closed 2026-11-26-split-build-routing (PR #51) had to delete a second `(<task>)` from its CHANGELOG line by hand.

**Evidence:**
- `plugin/scripts/close.py:150` (`cmd_close`) always writes `f"- {entry.strip()} ({task})"`. It never checks whether `--entry` already names the task.
- `plugin/stages/CLOSE.md` step 5 asks for "what changed", and step 6 passes it as `--entry`. Neither says close adds the task.
- Recent lines end `(<task>; closes <idea>)`. A model copies that into `--entry`, and close.py adds ` (<task>)` after it. Inference: b04a9b3 shows only the fixed line.
- `tests/test_close.py` passes only entries without a task name.

**Notes:** Inference: close.py skips the suffix when the entry names the task, or CLOSE.md says to leave it out. A failing test first.

**Decided (2026-11-26, grill):** The fix goes in `close.py`, not `CLOSE.md`. close.py skips ` (<task>)` when `--entry` already contains the task name. Details: the task's `CONCEPT.md`.

**Task:** [docs/tasks/2026-11-26-close-changelog-double-name/](../tasks/2026-11-26-close-changelog-double-name/)

# Log

- 2026-11-25T23:50:10Z [capture] Created from the owner's request through Orca. Status inbox, waiting for triage.
- 2026-11-26T00:55:43Z [triage] Kept. Status triaged. Problem confirmed. Next. Decided by Jayson De los Reyes.
- 2026-11-26T00:55:43Z [appetite] Set to small batch. Decided by Jayson De los Reyes.
- 2026-11-26T01:15:38Z [grill] Grilled on 2026-11-26: D1-D2 in the task's CONCEPT.md. Decided by Jayson De los Reyes.
- 2026-11-26T01:15:38Z [commit] Committed to task 2026-11-26-close-changelog-double-name. Decided by Jayson De los Reyes.
