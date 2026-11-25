---
title: Ship the review gates in plugin/scripts/afk.py
status: inbox
requester: Jayson De los Reyes
date: 2026-11-25
appetite:
review_by:
---

# Ship the review gates in plugin/scripts/afk.py

**Raw request:** "add a backlog idea for building the review gates into the shipped plugin/scripts/afk.py" (Jayson De los Reyes, 2026-11-25, through an Orca coordinator, on PR #33)

**Problem (AI draft, needs a human to confirm):** #30 built the review gates as `scripts/gates.py`, a repo-only script that this repo's `.kairyn/afk.yml` runs as `gates:` commands. Consumer repos get none of them. The retro (2026-11-25-retro-2) wanted them shipped.

**Evidence:**
- Closed ideas (deleted in #33; see git history and the CHANGELOG line for #30): gate-changes-outside-design and gate-fix-round-test-edits named `plugin/scripts/afk.py` as the place (retro L12, L13); gate-eval-pass-for-plugin-changes named `.kairyn/afk.yml` (L5).
- `scripts/gates.py`: checks `design`, `commits`, `evals` and `sessions`. Its `evals` check reads this repo's `evals/results/passed.json`, so a shipped version needs a consumer-side source of eval passes.

**Notes:** Inference: move the checks into afk.py as built-in gates, or ship gates.py under `plugin/scripts/` and add it to the `afk.yml` template. A `plugin/` change needs evals first.

# Log

- 2026-11-25T05:30:13Z [capture] Created from an owner request on PR #33. Status inbox, waiting for triage.
