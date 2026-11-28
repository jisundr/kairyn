---
task: 2026-11-28-backlog-stage
stage: build
summary: "Red and green evidence for each T<n>, written by afk.py."
---

# Build

`afk.py` writes one row per `T<n>`: the test commit and its exit (not 0), the feat commit and its exit (0).

| Task | Test commit | Red exit | Feat commit | Green exit |
|---|---|---|---|---|
| T1 | 3a8caaf | 1 | 4a11423 | 0 |
| T2 | 266e2bd | 1 | f94439d | 0 |
| T3 | cdd7e2a | 1 | 0cde169 | 0 |
| T4 | 378c5db | 2 | 3080de0 | 0 |
| T5 | 4eff076 | 1 | e03bc9f | 0 |

## Flags
- None

## Review
- Review 1: `plugin/release-hashes.json` adds `.kairyn/stages/BACKLOG.md` to the released `0.21.3` entry, with three hashes. BACKLOG.md did not ship in 0.21.3, so this rewrites an old release. Two of those hashes, and the extra hashes under `0.21.5` (`running-stages.md` `a761158…`, `GRILL.md` `7546bd6…`), match no file in this diff. They look like in-progress versions. DESIGN.md T4/T5 says only "refresh `plugin/release-hashes.json`" for 0.21.5.; `docs/backlog/20261122080759-backlog-stage.md` gets a reworded Problem and a new `[problem]` log line. No DESIGN.md task lists this file. The source is grill D1, but the change is outside DESIGN.md.; `tests/test_triage_checks.py` is a new file. No DESIGN.md task lists it: T2's test files are only `tests/test_backlog.py` and `tests/test_skills.py`.; The `README.md` line for `.harness/` changes from "how we work on kairyn: dev workflows" to "dev workflows for kairyn itself". DESIGN.md T5 names only one README cut, "e.g. before a release". This one is not named.; `.harness/README.md` principle 5 is restructured ("Not shipped." moves into the parenthesis), on top of the one sentence cut that T5 names (the ending of "`uv run pytest` runs the same check"). The extra rewording is not in DESIGN.md.; `tests/test_skills.py::test_triage_skill_runs_digest_and_decide_and_waits_for_the_owner` does not check the waiting its name and docstring claim (R7). It only checks `allowed-tools` and that the body names `digest` and `decide`. R7 is covered only by the `triage_digest` eval.
