---
title: The design stage has no room under its token budget
status: triaged
requester: Jayson De los Reyes
date: 2026-11-25
appetite: big batch
review_by: 2027-02-23
---

# The design stage has no room under its token budget

**Problem (confirmed by Jayson De los Reyes, 2026-11-25):** `plugin/stages/DESIGN.md` is at 498 of 500 tokens. The `repo:` rule fit only after cuts to other steps, and the reviewer read those cuts as out of scope. A fix round then cut more text that no eval checked. The next rule needs a split, not more cuts.

**Evidence:** Task 2026-11-24-multi-repo, BUILD.md Review 1 and 2, and commit 8152acc that restored the eval-tested text. `DESIGN.md` 498/500, `REQUIREMENTS.md` 495/500, `_template.md` 487/500 tokens. Both stages repeat the same approval rules in "State update".

**Next slice (small):** move the shared approval rules (pending, blocked, never approve for the user, the `Approval:` line format) into a new `plugin/stages/_approval.md`, read like `_template.md` (`init.sh` copies `stages/*`). Frees about 70 tokens in `DESIGN.md` and 50 in `REQUIREMENTS.md`. No new `STATE.md` stage, no `checks.structural_problems` change. Evals: design and requirements. approval-handoff can add grill's gate there.

**Notes:** Re-check the budget after the slice. A full split (plan stage and test-plan stage) only if `DESIGN.md` nears 500 again: that touches `STATE.md` stages, `checks.structural_problems` and the design eval.

# Log

- 2026-11-24T22:43:54Z [capture] Created by the exit of 2026-11-24-multi-repo. Status inbox, waiting for triage.
- 2026-11-24T23:07:13Z [triage] Kept. Status triaged. Decided by Jayson De los Reyes.
- 2026-11-24T23:07:13Z [appetite] Set to small batch. Decided by Jayson De los Reyes.
- 2026-11-25T08:49:41Z [triage] Kept, problem confirmed. Next: the `_approval.md` slice only. Decided by Jayson De los Reyes.
- 2026-11-25T08:49:41Z [appetite] Set to big batch (was small) for the full split; the slice is small. Decided by Jayson De los Reyes.
