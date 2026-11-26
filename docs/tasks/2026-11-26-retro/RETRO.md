---
task: 2026-11-26-retro
stage: retro
summary: "Ten learnings: two moves, four drops, four to the backlog inbox. learnings.md goes to the empty header."
---

# Retro: 2026-11-26

learnings.md before: 565/1000. After approval: about 10/1000 (header only).

| Entry | Action | Home or path | Text or reason |
|---|---|---|---|
| L1 | backlog | `.harness/workflows/testing-and-evals.md` | OVER 22. A phone-width need gets a test that measures page width in a browser. |
| L2 | move | `.harness/workflows/change-a-stage.md` | - Move a skill to a cheaper model only after its eval passes there at 10 runs: retro failed on Haiku (5/10, 7/10). |
| L3 | backlog | `.harness/workflows/change-a-stage.md` | OVER 21 with L2. More sessions can cost more ($7.45 against $4.67 all on Opus). |
| L4 | drop | `.harness/workflows/task-lifecycle.md` | Stale: L8 replaces it, and task-lifecycle.md names `close.py record-merge`. |
| L5 | backlog | `.harness/workflows/testing-and-evals.md` | OVER 22. Headless Chrome keeps about 500 px: use a 390 px iframe. |
| L6 | drop | | Stale: the backlog page has its Sort select; the rule is for that one task. |
| L7 | backlog | `plugin/scripts/upgrade.py` | Script: `upgrade.py` takes no flags, so `--help` runs the upgrade. It needs a `--help` that prints usage and changes nothing. |
| L8 | drop | `.harness/workflows/task-lifecycle.md` | That file holds the rule: close step 1 runs `record-merge`. |
| L9 | move | `.harness/workflows/upgrade.md` | - Do not edit a plugin-owned file in this repo (`.harness/workflows/` docs from `plugin/harness/`, templates, the CLAUDE.md block): each upgrade replaces it and prints `SAVED <file>.kairyn-old`. Put the note in a file the repo owns. |
| L10 | backlog | `plugin/scripts/close.py` | Script: close removes a committed idea only if it links `tasks/<task>/`. It can also match the task name in plain text. |

Approval: pending
