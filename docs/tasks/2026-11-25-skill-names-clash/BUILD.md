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
- test edit: `tests/test_dev_harness.py` in fix
- test edit: `tests/test_skills.py` in fix
- test edit: `tests/test_static.py` in fix
- test edit: `tests/test_upgrade.py` in fix
- test edit: `tests/test_dev_harness.py` in fix

## Review
- Review 1: These files changed but no task in DESIGN.md lists them: `plugin/harness/.harness/workflows/running-stages.md`, `.harness/workflows/running-stages.md` and `plugin/skills/retro/SKILL.md`. Each edit only renames exit to close, which R5 covers ("shipped harness docs", "retro texts"). T2 lists `plugin/scripts/retro.py` instead, and that file did not change. The fix is to update the design's file lists, not the code.; `tests/test_dev_harness.py` gets a new test, `test_this_repo_kairyn_is_upgraded_to_the_plugin_version`, but no task's files and no test-plan row in DESIGN.md list it. It checks A5 (this repo was upgraded to 0.11.0 and has `CLOSE.md` and no `EXIT.md`), so it has a purpose, but the design does not record it.
- Review 2, after the fix round: Findings: none
