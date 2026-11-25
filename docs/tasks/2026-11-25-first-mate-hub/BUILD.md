---
task: 2026-11-25-first-mate-hub
stage: build
summary: "Red and green evidence for each T<n>, written by afk.py."
---

# Build

`afk.py` writes one row per `T<n>`: the test commit and its exit (not 0), the feat commit and its exit (0).

| Task | Test commit | Red exit | Feat commit | Green exit |
|---|---|---|---|---|
| T1 | f75b743 | 1 | 687f6ca | 0 |
| T2 | b279515 | 1 | e9d4fb3 | 0 |
| T3 | a9ae614 | 1 | 4dc648b | 0 |
| T4 | 77d9cce | 1 | 43d8af4 | 0 |
| T5 | e8f9f57 | 1 | 6397edf | 0 |

## Flags
- test edit: `tests/test_milestones.py` in fix

## Review
- Review 1: AC13 ("In one real cerna-hq session... the user asks 'status?' 0 times") has no automated test. DESIGN.md's test plan makes it a manual check after merge. The eval `evals/promptfoo/milestones.yaml` only checks that the session starts Monitor and names the missed lines, so the criterion itself stays unverified until Jayson runs that session.; `plugin/hooks/hooks.json` adds a `PostToolUseFailure` hook. DESIGN.md (Approach and T2) names only PostToolUse, Stop and SessionStart. The addition is reasonable, because a failed Bash command may not fire PostToolUse, and AC1 depends on it for `exit 1`. But neither REQUIREMENTS.md nor DESIGN.md records it.; `tests/test_afk.py` is changed (3 new tests), but no task's Files list in DESIGN.md names it. T1 and T2 only run it in their Done commands.; `plugin/harness/.harness/README.md` (new index row) and `plugin/release-hashes.json` (new 0.11.0 hashes) are changed, but neither is in any task's Files list in DESIGN.md. Both look like generated output from required steps (`harness_docs.py --write` and `scripts/release_hashes.py --write` in `.harness/workflows/pull-request.md`), so this is a gap in the design's file lists, not unplanned work.
