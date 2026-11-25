---
title: Write log sections as bullet lists
status: triaged
requester: Jayson De los Reyes
date: 2026-11-25
appetite: small batch
review_by:
---

# Write log sections as bullet lists

**Raw request:** "make logs bullet list" (Jayson De los Reyes, 2026-11-25, Claude Code session)

**Problem (AI draft, needs a human to confirm):** `STATE.md` and backlog files keep their `# Log` as plain lines, one per entry, with no blank line between them. Markdown joins such lines into one paragraph, so a rendered log (GitHub, VS Code preview, a pull request) is one long block of text.

**Evidence:**
- `afk.py` `update()` appends `\n{stamp} [{at}] {log}\n`; `.kairyn/templates/STATE.md` and `plugin/templates/STATE.md` show the same form.
- Stages that write log lines by hand (grill, requirements, design, close) and backlog captures follow it.

**Notes:** Inference: write each entry as `- <timestamp> [<stage>] <text>`. Readers that parse log lines (afk.py, close.py, tests, evals) must accept both forms, so old task folders still work.

# Log

- 2026-11-25T01:42:55Z [capture] Created from a user request in a Claude Code session. Status inbox, waiting for triage.
- 2026-11-25T04:18:32Z [triage] Kept. Status triaged. Decided by Jayson De los Reyes.
- 2026-11-25T04:18:32Z [appetite] Set to small batch. Decided by Jayson De los Reyes.
