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
- None

## Review
- Review 1: `tests/test_dev_harness.py` gets a new test, `test_this_repo_takes_the_design_split_at_0_21_3_or_later`, but `DESIGN.md` T2 does not list that file. T2 names only `plugin.json`, `release-hashes.json`, `.kairyn/manifest.json` and the `.kairyn/stages` and `.kairyn/.base` copies, so this is a change outside the design. The test does check real things (the version is at least 0.21.3, and this repo's copies of `DESIGN.md` and `_slices.md` match the plugin and appear in the manifest), so the fault is that the design leaves the file out, not the test itself.
