---
title: The design stage has no room under its token budget
status: triaged
requester: Jayson De los Reyes
date: 2026-11-25
effort: high
impact: medium
review_by: 2027-02-23
---

# The design stage has no room under its token budget

**Problem (confirmed by Jayson De los Reyes, 2026-11-25):** `plugin/stages/DESIGN.md` is at 498 of 500 tokens. The `repo:` rule fit only after cuts to other steps, and the reviewer read those cuts as out of scope. A fix round then cut more text that no eval checked. The next rule needs a split, not more cuts.

**Evidence:** Task 2026-11-24-multi-repo, BUILD.md Review 1 and 2, and commit 8152acc that restored the eval-tested text. `DESIGN.md` 498/500, `REQUIREMENTS.md` 495/500, `_template.md` 487/500 tokens. Both stages repeat the same approval rules in "State update".

**Slice shipped (2026-11-25):** the shared approval rules moved to `plugin/stages/_approval.md` (0.12.7). Tokens: `DESIGN.md` 498 → 420, `REQUIREMENTS.md` 495 → 426, `_approval.md` 132, `_template.md` 487 (no change). No `STATE.md` stage and no `checks.structural_problems` change.

**Still open:** the full split (plan stage and test-plan stage). The slice did not make it unnecessary, only not urgent: do it when `DESIGN.md` nears 500 again. It touches `STATE.md` stages, `checks.structural_problems` and the design eval. approval-handoff can add grill's gate to `_approval.md`.

# Log

- 2026-11-24T22:43:54Z [capture] Created by the exit of 2026-11-24-multi-repo. Status inbox, waiting for triage.
- 2026-11-24T23:07:13Z [triage] Kept. Status triaged. Decided by Jayson De los Reyes.
- 2026-11-24T23:07:13Z [appetite] Set to small batch. Decided by Jayson De los Reyes.
- 2026-11-25T08:49:41Z [triage] Kept, problem confirmed. Next: the `_approval.md` slice only. Decided by Jayson De los Reyes.
- 2026-11-25T08:49:41Z [appetite] Set to big batch (was small) for the full split; the slice is small. Decided by Jayson De los Reyes.
- 2026-11-25T09:04:42Z [slice] The `_approval.md` slice shipped. The full split stays triaged, big. Done by Claude for Jayson De los Reyes.
- 2026-11-25T22:35:13Z [note] Related idea split-build-routing (2026-11-26) moves the technical decisions of each slice into an Opus test commit. This idea stays open. Noted by Claude for Jayson De los Reyes.
- 2026-11-26T03:01:29Z [triage] Effort high, impact medium confirmed by Jayson De los Reyes.
