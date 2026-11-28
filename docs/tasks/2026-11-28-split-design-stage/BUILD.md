---
task: 2026-11-28-split-design-stage
stage: build
summary: "Red and green evidence for each T<n>, written by afk.py."
---

# Build

`afk.py` writes one row per `T<n>`: the test commit and its exit (not 0), the feat commit and its exit (0).

| Task | Test commit | Red exit | Feat commit | Green exit |
|---|---|---|---|---|
| T1 | 099df9f | 1 | 2a2b11c | 0 |
| T2 | 7c7b97e | 1 | 7a1dda5 | 0 |

## Flags
- test edit: `tests/test_dev_harness.py` in fix

## Review
- Review 1: `plugin/release-hashes.json` changes the 0.21.3 release record, which is outside DESIGN.md. Lines 2123–2150, inside the `"0.21.3"` block, now list the new `.kairyn/stages/DESIGN.md` hash `79ea380f…` and a `.kairyn/stages/_slices.md` entry `e1484f7b…`. 0.21.3 shipped from main without `_slices.md` or that DESIGN.md text. DESIGN.md T2 only asks for a 0.21.4 entry from `release_hashes.py --write`, so this looks left over from before the rebase from 0.21.3 to 0.21.4. The 0.21.3 block should be the same as on main.; The new test `test_this_repo_takes_the_design_split_at_0_21_3_or_later` (`tests/test_dev_harness.py:74`) checks for a version `>= (0, 21, 3)`. That passes on the old version 0.21.3, so it does not show the bump. AC6 wants a newer version in `plugin/.claude-plugin/plugin.json`, and its planned test (`uv run pytest && claude plugin validate plugin`) has no other check that the version went past 0.21.3. The bound should be `>= (0, 21, 4)` or a check against main's version.
- Review 2, after the fix round: Findings: none
