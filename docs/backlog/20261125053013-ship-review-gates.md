---
title: Ship the review gates in plugin/scripts/afk.py
status: triaged
requester: Jayson De los Reyes
date: 2026-11-25
appetite: big batch
review_by: 2027-02-23
---

# Ship the review gates in plugin/scripts/afk.py

**Raw request:** "add a backlog idea for building the review gates into the shipped plugin/scripts/afk.py" (Jayson De los Reyes, 2026-11-25, through an Orca coordinator, on PR #33)

**Problem (confirmed by Jayson De los Reyes, 2026-11-25):** #30 built the review gates as `scripts/gates.py`, a repo-only script that this repo's `.kairyn/afk.yml` runs as `gates:` commands. Consumer repos get none of them. The retro (2026-11-25-retro-2) wanted them shipped.

**Evidence:**
- Closed ideas (deleted in #33; see git history and the CHANGELOG line for #30): gate-changes-outside-design and gate-fix-round-test-edits named `plugin/scripts/afk.py` as the place (retro L12, L13); gate-eval-pass-for-plugin-changes named `.kairyn/afk.yml` (L5).
- `scripts/gates.py`: its `evals` check reads this repo's `evals/results/passed.json`.

**Decided (2026-11-25, slice 2 grill):** A person runs `Manual` checks; design marks the rows. The gate wants `Run AC<n>: <who>, <time>, "<what it showed>"`, all three parts, in a task file but `DESIGN.md`. A block prints the rows, the line format and the resume command. `evals` stays in `scripts/gates.py` until consumer repos record eval passes.

**Left after slice 2:** `evals`.

**Notes:** Shaped as built-in gates in afk.py. A `plugin/` change needs evals first.

# Log

- 2026-11-25T05:30:13Z [capture] Created from an owner request on PR #33. Status inbox, waiting for triage.
- 2026-11-25T05:38:06Z [triage] Kept. Status triaged. Problem confirmed. Not Next: shape first. Decided by Jayson De los Reyes.
- 2026-11-25T05:38:06Z [appetite] Set to big batch. Decided by Jayson De los Reyes.
- 2026-11-25T09:15:19Z [slice] Slice 1: afk.py runs `design` and `commits` built in, from an Orca coordinator dispatch. `evals` and `sessions` left.
- 2026-11-25T10:18:25Z [grill] Slice 2: a person runs Manual checks; design marks the rows; the gate checks who, time and text. Decided by Jayson De los Reyes.
- 2026-11-25T10:18:25Z [slice] Slice 2: afk.py runs `sessions` built in; the design stage marks `Manual` rows. Next by Jayson De los Reyes, from an Orca coordinator dispatch. `evals` left.
