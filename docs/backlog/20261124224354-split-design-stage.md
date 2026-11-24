---
title: The design stage has no room under its token budget
status: triaged
requester: Jayson De los Reyes
date: 2026-11-25
appetite: small batch
review_by: 2027-02-23
---

# The design stage has no room under its token budget

**Problem (AI draft, needs a human to confirm):** `plugin/stages/DESIGN.md` is at 498 of 500 tokens. The `repo:` rule fit only after cuts to other steps, and the reviewer read those cuts as out of scope. A fix round then cut more text that no eval checked. The next rule needs a split, not more cuts.

**Evidence:** Task 2026-11-24-multi-repo, BUILD.md Review 1 and 2, and commit 8152acc that restored the eval-tested text.

# Log

2026-11-24T22:43:54Z [capture] Created by the exit of 2026-11-24-multi-repo. Status inbox, waiting for triage.
2026-11-24T23:07:13Z [triage] Kept. Status triaged. Decided by Jayson De los Reyes.
2026-11-24T23:07:13Z [appetite] Set to small batch. Decided by Jayson De los Reyes.
