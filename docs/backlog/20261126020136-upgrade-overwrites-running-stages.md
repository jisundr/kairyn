---
title: Upgrade overwrites this repo's edited running-stages.md
status: committed
requester: Jayson De los Reyes
date: 2026-11-26
effort: low
impact: medium
review_by:
---

# Upgrade overwrites this repo's edited running-stages.md

**Raw request:** capture the running-stages.md overwrite on upgrade as a backlog idea (owner, 2026-11-26, through Orca).

**Problem (confirmed by Jayson De los Reyes, 2026-11-26):** Each upgrade of this repo's `.kairyn/` replaces `.harness/workflows/running-stages.md` with the shipped copy and drops this repo's one-line edit. Workers restored it by hand three times: PR #48 (0.16.0), PR #50 (0.17.0) and PR #54 (0.17.1).

**Evidence:**
- The edit is step 3's note that `.gitattributes` merges `.kairyn/learnings.md` by `union` (added in cb1f43f with that `.gitattributes` line). The shipped copy lacks it.
- `kairyn_files.py:66` lists the file in `_KAIRYN_HARNESS_DOCS`, so `owner_of` returns `plugin`, and `.kairyn/manifest.json` records `"owner": "plugin"`.
- `upgrade.py:140`: a plugin-owned file in a repo with a manifest is always `REPLACED`. An edited copy goes to `<file>.kairyn-old` (line 142). Only repo-owned files reach `git merge-file` and `CONFLICT`. `.harness/workflows/upgrade.md:25` documents this, so upgrade works as designed.
- A `REPLACED` with a `.kairyn-old` exits 0 and prints no warning, unlike `CONFLICT`. `.kairyn-old` is not in `.gitignore`, so it shows up as an untracked file.

**Notes:** Shaped in task `2026-11-26-upgrade-overwrites-running-stages`: see its `CONCEPT.md`.

# Log

- 2026-11-26T02:01:36Z [capture] Created from the owner's request through Orca. Status inbox, waiting for triage.
- 2026-11-26T02:38:49Z [triage] Kept. Status triaged. Problem confirmed. Not Next. Decided by Jayson De los Reyes.
- 2026-11-26T02:38:49Z [appetite] Set to small batch. Decided by Jayson De los Reyes.
- 2026-11-26T03:01:29Z [triage] Effort low, impact medium confirmed by Jayson De los Reyes.
- 2026-11-26T06:37:19Z [shaping] Status shaping. Grill started in task 2026-11-26-upgrade-overwrites-running-stages.
- 2026-11-26T06:44:29Z [commit] Concept approved ("Approve"). Status committed. Decided by Jayson De los Reyes.
