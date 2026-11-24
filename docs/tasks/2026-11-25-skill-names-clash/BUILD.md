---
task: 2026-11-25-skill-names-clash
stage: build
summary: "Red and green evidence for each T<n>, written by afk.py."
---

# Build

`afk.py` writes one row per `T<n>`: the test commit and its exit (not 0), the feat commit and its exit (0).

| Task | Test commit | Red exit | Feat commit | Green exit |
|---|---|---|---|---|
| T1 | 9eaf38f | 1 | 24c24de | 0 |
| T2 | df7d733 | 1 | a264489 | 0 |
| T3 | 996dc3d | 2 | beea276 | 0 |
| T4 | 49b613d | 1 | ff20a78 | 0 |

## Flags
- escape hatch: `evals/promptfoo/asserts.py:14` `# noqa` in feat(T3)
- escape hatch: `evals/promptfoo/provider.py:17` `# noqa` in feat(T3)
- test edit: `tests/test_static.py` in feat(T4)

## Review
- Review 1: `plugin/release-hashes.json` changes the existing `0.10.0` entry. It adds the new hashes for `.harness/budgets.yml`, `running-stages.md`, `task-lifecycle.md` and `RETRO.md`, and adds `.kairyn/stages/CLOSE.md`, a file version 0.10.0 never shipped. REQUIREMENTS.md puts edits to `release-hashes.json` entries out of scope (D3). DESIGN.md T4 expected only a new `0.11.0` entry. The likely cause is `release_hashes.py --write` counting the T2/T3 commits under 0.10.0, because `plugin.json` still said 0.10.0 when they were made. The 0.10.0 entry should be restored, with only `0.11.0` added.; These changes are outside DESIGN.md's task file lists: `.harness/workflows/running-stages.md`, `plugin/harness/.harness/workflows/running-stages.md` and `plugin/skills/retro/SKILL.md`. R5's scope ("shipped harness docs", "retro texts") covers them, so this is a gap in the design's file lists, not unplanned work.; `tests/test_dev_harness.py` is changed in feat(T4) but is not in T4's file list. It gains two tests. `test_plugin_version_is_0_11_0_or_later` adds almost nothing: it only checks a version floor, which the dogfood test next to it already pins exactly through `plugin_version(PLUGIN)`.; The static guard in `tests/test_static.py:153` (`EXIT_ALLOWED`) skips whole files, not single lines: `tests/test_skills.py`, `tests/test_upgrade.py` and `tests/test_dev_harness.py`. A leftover stage name anywhere else in those files would pass AC5 unnoticed.
