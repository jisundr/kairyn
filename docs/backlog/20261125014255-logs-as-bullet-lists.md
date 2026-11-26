---
title: Write log sections as bullet lists
status: parked
requester: Jayson De los Reyes
date: 2026-11-25
effort: low
impact: medium
review_by: 2027-02-23
---

# Write log sections as bullet lists

**Raw request:** "make logs bullet list" (Jayson De los Reyes, 2026-11-25, Claude Code session)

**Problem (confirmed by Jayson De los Reyes, 2026-11-25):** `STATE.md` and backlog files keep their `# Log` as plain lines, one per entry, with no blank line between them. Markdown joins such lines into one paragraph, so a rendered log (GitHub, VS Code preview, a pull request) is one long block of text.

**Evidence:**
- `afk.py` `update()` appends `\n{stamp} [{at}] {log}\n`; `.kairyn/templates/STATE.md` and `plugin/templates/STATE.md` show the same form.
- Stages that write log lines by hand (grill, requirements, design, close) and backlog captures follow it.

- No script reads `STATE.md` log lines: not afk.py, not close.py. The writer is `afk.py` `update()` (one f-string). The rule is `_template.md` "Log". Only tests read lines (`tests/test_afk.py` regex). Backlog files already use bullets.

**Notes:** Write each entry as `- <timestamp> [<stage>] <text>`. Readers accept both forms (`^(- )?<timestamp>`), so old task folders work. The diff is small, but `_template.md` is a `# depends:` of 7 eval suites. Parked: ride along the next change that edits `_template.md` for another reason. An afk.py and template-only slice mixes two forms in one log.

# Log

- 2026-11-25T01:42:55Z [capture] Created from a user request in a Claude Code session. Status inbox, waiting for triage.
- 2026-11-25T04:18:32Z [triage] Kept. Status triaged. Decided by Jayson De los Reyes.
- 2026-11-25T04:18:32Z [appetite] Set to small batch. Decided by Jayson De los Reyes.
- 2026-11-25T08:49:41Z [triage] Parked until 2027-02-23: 7 evals for a rendering fix; ride along the next `_template.md` change. Decided by Jayson De los Reyes.
- 2026-11-26T03:01:29Z [triage] Effort low, impact medium confirmed by Jayson De los Reyes.
