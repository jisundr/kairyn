---
title: Rule on the shared dev and consumer harness has no home
status: parked
requester: Jayson De los Reyes
date: 2026-11-23
effort: low
impact: low
review_by: 2027-02-23
---

# Rule on the shared dev and consumer harness has no home

**Raw request:** learning L1 from retro task `2026-11-23-retro`, quoted word for word:

> This repo installs its own plugin, so its dev harness and the consumer harness share `CLAUDE.md`, `.harness/README.md` and `budgets.yml`. Only one `harness-docs` marker pair may exist in a file (`harness_docs.py` updates the first). Keep kairyn's own `CLAUDE.md` text under budget so the plugin block fits.

**Problem (AI draft, needs a human to confirm):** The rule has no file an agent reads at the right time. Home: `.harness/README.md`. Reason: OVER 40. `CLAUDE.md` is OVER 40 too, and `keeping-docs-lean.md` is KAIRYN-OWNED.

# Log

2026-11-23T11:09:52Z [capture] Created by retro from `.kairyn/learnings.md` L1. Status inbox, waiting for triage.
2026-11-23T11:22:03Z [triage] Parked: only this repo hits it, and its homes are full. Status parked. Decided by Jayson De los Reyes.
2026-11-26T03:01:29Z [triage] Effort low, impact low confirmed by Jayson De los Reyes.
