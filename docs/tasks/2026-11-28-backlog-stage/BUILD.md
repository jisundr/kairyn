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
- Review 1: The diff carries a second task's changes that DESIGN.md does not cover. These are the grill-rounds work from PR #76: the rounds rewrite of `plugin/stages/GRILL.md` (step 4, step 5 and `purpose`), `grill_round_problems`, `round_decision_problems` and `finished_turn` in `evals/checks.py`, the `rounds` assert and the removal of `one_question` in `asserts.py`, the `docs/tasks/2026-11-28-grill-rounds/` folder, `grill-rounds` set to `committed`, and the grill-rounds line in `.kairyn/learnings.md`. STATE.md says the branch was rebased onto PR #76, so the diff base seems to be a main without #76. Review against a base that has #76, or merge #76 first.; The diff has backlog edits from a third task, 2026-11-28-init-ships-union-merge, that DESIGN.md does not cover. `init-ships-union-merge` is set to `dropped`, `union-merge-restores-learnings` gets a new Evidence block, its row leaves `docs/backlog/README.md`, and `TRIAGE.md` gets an "init-ships-union-merge was dropped" sentence.; Some changes to `README.md` and `.harness/README.md` are outside DESIGN.md. T5 says only "name the stage and skills", but `.harness/README.md` loses the line "Read only those first lines (`head -6 <file>`) to decide whether a doc matters". `README.md` also rewords "A session-start hook tells you when to run it." to "A hook says when." and shortens the skills tree comment. DESIGN.md allows budget cuts only for GRILL.md and REQUIREMENTS.md, in T4.; One GRILL.md cut changes what the stage does, which T4 does not allow; T4 adds only one Inputs line. Step 2 changes from "Read the repo before each question" to "Read the repo first". The stage now reads the repo once instead of before each question.; In `triage_digest_problems` (`evals/checks.py`), the check that a not-yet-due park is left out tests nothing in practice. It looks for the full file name `20261103000000-dark-mode.md` in the reply, but the due ideas are matched by slug. A reply that proposes "Dark mode" or "dark-mode" still passes, so the "only stale parked ideas" half of AC3 (R6) has no working test.; AC3 has no test for "each with a proposal and reason". `triage_digest_problems` passes if the word keep, park or drop appears once anywhere in the reply. It does not check for a proposal for each due idea, and it never checks for a reason (R6).
