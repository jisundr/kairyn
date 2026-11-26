---
title: Write log sections as bullet lists
status: committed
requester: Jayson De los Reyes
date: 2026-11-25
effort: low
impact: medium
review_by: 2027-02-23
---

# Write log sections as bullet lists

**Raw request:** "make logs bullet list" (Jayson De los Reyes, 2026-11-25, Claude Code session)

**Problem (confirmed by Jayson De los Reyes, 2026-11-25):** `STATE.md` keeps its `# Log` as plain lines with no blank line between them. Markdown joins them into one paragraph, so a rendered log is one block of text.

**Evidence:**
- `afk.py` `update()` appends `\n{stamp} [{at}] {log}\n`; the `STATE.md` templates and the `_template.md` rule show the same form.
- No script reads `STATE.md` log lines; only test regexes do. Backlog files already use bullets.

**Decided (2026-11-26, grill):** New `STATE.md` log entries are bullets: `afk.py` `update()`, the `_template.md` rule and the `STATE.md` template (plugin and `.kairyn/`). Old entries and the milestones log stay. Details: the task's `CONCEPT.md`.

**Task:** [docs/tasks/2026-11-26-logs-as-bullet-lists/](../tasks/2026-11-26-logs-as-bullet-lists/)

# Log

- 2026-11-25T01:42:55Z [capture] Created from a user request in a Claude Code session. Status inbox, waiting for triage.
- 2026-11-25T04:18:32Z [triage] Kept. Status triaged. Decided by Jayson De los Reyes.
- 2026-11-25T04:18:32Z [appetite] Set to small batch. Decided by Jayson De los Reyes.
- 2026-11-25T08:49:41Z [triage] Parked until 2027-02-23: 7 evals for a rendering fix; ride along the next `_template.md` change. Decided by Jayson De los Reyes.
- 2026-11-26T03:01:29Z [triage] Effort low, impact medium confirmed by Jayson De los Reyes.
- 2026-11-26T06:45:30Z [grill] Grilled on 2026-11-26: D1-D3 in the task's CONCEPT.md. Decided by Jayson De los Reyes.
- 2026-11-26T06:45:30Z [commit] Committed to task 2026-11-26-logs-as-bullet-lists. Decided by Jayson De los Reyes.
