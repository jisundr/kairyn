---
task: 2026-11-28-backlog-stage
stage: review
summary: "Each criterion has evidence. One finding: release-hashes.json changes the released 0.21.3 entry again, after review 2."
---

# Review: Backlog stage

## Criteria
| Criterion | Evidence |
|---|---|
| AC1 `BACKLOG.md` is an optional stage with the rules (R1) | BUILD.md T1: red c0509ba exit 1, green 763fa9e exit 0. `tests/test_static.py` stage checks and `test_backlog.py::test_stage_names_the_rules`. Gate testing: pass. |
| AC2 capture writes, creates the folder and README, never overwrites (R2-R5) | BUILD.md T1. `test_backlog.py::test_capture_*` (9 tests). Eval `idea_captured` 10/10 (need 9), run 20261128T114315Z. |
| AC3 triage lists, proposes, waits (R6, R7) | Eval `triage_listed` 9/10 (need 9) in run 20261128T114315Z, 10/10 in run 20261128T121248Z. |
| AC4 each decision sets status, date, log line, README row (R8-R11) | BUILD.md T2: red df246eb exit 1, green 5405d57 exit 0. `test_backlog.py::test_decide_*`. Eval `triage_applied` 10/10 in run 20261128T121248Z. It was 0/10 in run 20261128T114315Z; fix 29eef87 changed only the eval harness (python3 allowed on the owner's turn), not `plugin/`. |
| AC5 commit writes STATE.md and the two commands; refuses bad input (R12-R14) | BUILD.md T3: red ffa2416 exit 1, green db32b0e exit 0. `test_backlog.py::test_commit_*`. |
| AC6 grill and requirements take the idea (R15) | BUILD.md T4: red 5f88a41 exit 2, green 8586fba exit 0. Evals `grill_from_idea` 9/10 (need 9) and `requirements_from_idea` 10/10 (need 9), run 20261128T114315Z. |
| AC7 `TRIAGE.md` keeps only Next and Parked (R16) | BUILD.md T5: red 16424f6 exit 1, green f653fa4 exit 0. `test_static.py::test_triage_keeps_next_and_parked`. |

## Gates
- accessibility: not set. REQUIREMENTS.md says: not applicable.
- performance: not set. REQUIREMENTS.md says: not applicable.
- observability: not set. The need (each decision is a log line with who decided) has evidence in the `test_decide_*` and `test_commit_*` tests.
- security: not set. REQUIREMENTS.md says: not applicable.
- BUILD.md flag: test edit `tests/test_skills.py` in fix. The commits gate folded it into the `test(T2)` commit, and the gate passed.
- BUILD.md review 1 had six findings. Review 2 had none. F1 shows that one of them came back after review 2.

## Risky files
- `plugin/scripts/backlog.py`: it writes every idea file, README row and task folder in user repos. `decide` does not check the current status: `keep` on a `committed` or `dropped` idea sets it to `triaged` and adds a README row, and `renew` works on an idea that is not `parked`. No requirement asks for this check, so it is not a finding.
- `plugin/release-hashes.json`: upgrade uses these hashes to find user edits. A wrong hash can make upgrade keep an old file or replace a user's edit.
- `plugin/stages/GRILL.md` and `plugin/stages/REQUIREMENTS.md`: every task runs them. `grill_from_idea` passed at its threshold (9/10, need 9), with no margin.

## Findings
- F1: `plugin/release-hashes.json` changes the released `0.21.3` entry. At HEAD it adds `.kairyn/stages/BACKLOG.md` (3 hashes), `.kairyn/stages/_slices.md` (1 hash) and a second `.kairyn/stages/DESIGN.md` hash (`79ea380…`). `BACKLOG.md` did not ship in 0.21.3. Fix 5619f4a removed this change for review 1, but commit 09b2493 ("as evaluated, after the rebase onto main") put it back, after review 2. Two of the `BACKLOG.md` hashes (`37eb4f9…`, `92f7cc7…`) match no file at HEAD. The `0.21.5` entry also keeps `GRILL.md` `7546bd6…` and `running-stages.md` `a761158…` and `12a3365…`, which match no file at HEAD. DESIGN.md T4 and T5 say only "refresh `plugin/release-hashes.json`" for 0.21.5. This change is outside DESIGN.md.

Decision: pending
