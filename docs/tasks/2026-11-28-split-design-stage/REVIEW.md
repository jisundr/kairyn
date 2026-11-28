---
task: 2026-11-28-split-design-stage
stage: review
summary: "All 7 criteria have evidence or a close-time check. One finding: the AC3 command reads a stale local main."
---

# Review: Split the design stage

## Criteria
| Criterion | Evidence |
|---|---|
| AC1 `DESIGN.md` at most 350 tokens and names `_slices.md` | `test_design_stage_fits_350_tokens_and_points_to_slices` (`tests/test_static.py`). BUILD.md T1: red 1 at 099df9f, green 0 at 2a2b11c. |
| AC2 `_slices.md` holds the moved rule words | `test_slices_holds_the_moved_rules` (`tests/test_static.py`) checks all 8 words. BUILD.md T1 row. The diff moves steps 6 and 7 word for word. |
| AC3 no change to the 4 protected files | `git diff --quiet 2c943dc..HEAD` on the 4 files exits 0. The planned command `git diff --quiet main` exits 1 in this worktree: see F1. |
| AC4 3 design scenarios meet `min_pass_rate` at 10 runs | Gate `evals` pass. `evals/results/20261128T104808Z/summary.md`: `design`, `design_approval` and `design_child_repo` pass each check at 10/10; quality mean 4.0 (need 4). Cost $17.15 with init and upgrade. |
| AC5 `design.yaml` depends and `change-a-stage.md` name `_slices.md` | The two `grep -q` commands joined by `&&` exit 0. |
| AC6 newer version, pytest and plugin validate pass | `plugin.json` 0.21.3 to 0.21.4. `test_this_repo_takes_the_design_split_at_0_21_4_or_later`. BUILD.md T2: red 1 at 7c7b97e, green 0 at 7a1dda5. Gate `testing` pass. At review: `uv run pytest` 843 passed; `claude plugin validate plugin` passed. `DESIGN.md` is 346 tokens, `_slices.md` 142. |
| AC7 after close, idea gone and an ADR names the rejected split | Not yet: checked by `/kairyn:close` after merge (DESIGN.md amended, Steward approved 2026-11-28T11:07:26Z). |

## Gates
- accessibility: not set
- performance: not set. R1 (at most 350 tokens) is the performance need; AC1's test covers it.
- observability: not set
- security: not set

Flag in BUILD.md: test edit, `tests/test_dev_harness.py` in the fix round. Review 1 findings (0.21.3 record, weak version bound) are fixed: the 0.21.3 block is not in the diff, and the test bound is `>= (0, 21, 4)`. Review 2: no findings.

## Risky files
- `plugin/stages/_slices.md`: the design agent must open it. If it skips the file, task plans lose slices, `Done:` and the Test plan (K1). Only the design eval catches this.
- `plugin/stages/DESIGN.md`: step 6 is now one pointer line. A cut here removes the only link to `_slices.md`.
- `plugin/release-hashes.json`: a wrong hash breaks upgrades for every user repo on 0.21.4.

## Findings
- F1: The AC3 test in DESIGN.md is `git diff --quiet main -- ...`. In this worktree, local `main` is at 2f972dc, behind `origin/main` (2c943dc). The command exits 1 because `evals/checks.py` changed on `origin/main`, not in this change. The criterion holds against the true base, but the test result depends on the state of local `main`. Use the merge base or `origin/main` in such tests.

Decision: pending
