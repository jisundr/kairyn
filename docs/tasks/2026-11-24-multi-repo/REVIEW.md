---
task: 2026-11-24-multi-repo
stage: review
summary: "All 12 criteria have evidence; 579 tests pass. F1 and F3 are fixed with tests. Open: AC11 eval ran before its move to design.yaml; no doc says how to retry approve."
---

# Review: kairyn tasks in a home repo change code in child repos

## Criteria
| Criterion | Evidence |
|---|---|
| AC1 The current afk.py tests pass with no change | `tests/test_afk.py` has no diff. `uv run pytest`: 579 passed. Gate testing: pass. |
| AC2 Nested repos map and today's template parse | `test_t1_parse_repos`, `test_t1_parse_template` pass. The repo's own `.kairyn/afk.yml` also parses. BUILD.md T1. |
| AC3 Unknown name, missing path, non-git path block | `test_t1_bad_repo_blocks` (three cases) passes. Each checks the name and cause in the `Blocked:` log line. |
| AC4 Task files on home branch, code on child branch | `test_t2_branches_split`, `test_t3_red_green_child` pass. BUILD.md T2. |
| AC5 A second run reuses the child worktree | `test_t2_reuse_worktree` passes. It calls `Run.resolve_repo` two times, not `afk.py run` two times. |
| AC6 Stub records child cwd, `--add-dir`, full paths | `test_t3_session_cwd` passes; `test_t3_home_task_session_cwd_is_unchanged` checks R1. BUILD.md T3. |
| AC7 Red and green in the child; approval glob blocks | `test_t3_red_green_child`, `test_t3_flags_child`, `test_t3_backstop_child` pass. |
| AC8 Child gate runs in child; readiness blocks | `test_t4_child_gates`, `test_t4_child_gate_fails_blocks`, `test_t4_readiness_blocks` (three cases), `test_t4_readiness_needs_a_clean_child_worktree` pass. BUILD.md T4. |
| AC9 Push and PR per repo; REVIEW.md on child PR | `test_t5_publish_both` passes. BUILD.md T5. |
| AC10 Child then home merge; child fail blocks | `test_t5_merge_order`, `test_t5_child_merge_fails`, `test_t5_child_with_no_remote_blocks`, `test_t5_retry_skips_a_merged_child` pass. Fix commits eb5a28a (test) and fbbc9f3 (fix). See F5. |
| AC11 Design writes `repo:` | Eval run 20261124T045044Z: `design_names_repo` 10/10 (child scenario) and 10/10 (base scenario). Run 20261124T052325Z: base scenario 10/10, quality mean 4.2. Approval T6 in BUILD.md. Gap: see F2. |
| AC12 Template and afk-run.md name the map | `test_t6_docs_name_the_repos_map` and `tests/test_harness_docs.py` pass. `harness_docs.py`: "OK: harness docs verified". Gate contract: pass. |

## Gates
- accessibility: not set (REQUIREMENTS.md: not applicable).
- performance: not set (REQUIREMENTS.md: not applicable).
- observability: not set. REQUIREMENTS.md asks that each block names its cause in the `STATE.md` log. The T1, T4 and T5 tests check the log lines. The F1 fix adds a log line for a child with no remote.
- security: not set (REQUIREMENTS.md: not applicable).

Flags in BUILD.md:
- test edit: `evals/promptfoo/design-repo.yaml` in fix. The fix round deleted the file and moved its test into `design.yaml`. The reason is good, but see F2.
- test edit: `evals/promptfoo/design.yaml` in fix. Same move.

Reviewer findings in BUILD.md: Review 1: none.

## Risky files
- `plugin/scripts/afk.py` `decide()`: it merges real pull requests in two repos. A defect here merges the home task files while the child code stays unmerged.
- `plugin/scripts/afk.py` `parse_afk()` and `_block()`: each run reads every user's `afk.yml` with this parser (K1). It now rejects mixed indent in a section, which the old parser accepted.
- `plugin/scripts/afk.py` `resolve_repo()`: it creates a branch and worktree in a second repo.
- `plugin/stages/DESIGN.md`: the stage is at its 500-token budget, and model behavior depends on its words.

## Findings
- F1 (fixed): A child repo with no `origin` remote now blocks approve with "no origin remote: merge kairyn/<task> in <path> by hand". The home stays unmerged. `test_t5_child_with_no_remote_blocks` checks that no `pr merge` runs and checks the log line. A home repo with no remote is still skipped, as before.
- F2 (open): The AC11 eval passed in `design-repo.yaml` (run 20261124T045044Z, at a31efbd). Commit ecf14b8 moved the `design_child_repo` test into `design.yaml`. `evals/results/` has no run after 20261124T052325Z, so no run includes that test from `design.yaml`. The stage text and the scenario code are the same as at a31efbd, so the risk is low. Run `/run-evals design` once to get evidence for the shipped eval file.
- F3 (fixed): `pr_merged()` reads `gh pr view --json state`. On a retry, a child pull request in state `MERGED` is skipped with "Already merged.". `test_t5_retry_skips_a_merged_child` checks that the child merges one time. The gh stub prints `MERGED` only after a merge in that cwd. The test does not prove that real `gh` prints `MERGED` with `--jq .state`.
- F4 (minor, open): `plugin/release-hashes.json` adds two hashes for `.kairyn/stages/DESIGN.md`. One is the text of ecf14b8, which 8152acc reverted and no release shipped.
- F5 (minor): A retry of approve needs `Decision: pending` in `REVIEW.md`, but the blocked approve already wrote the decision line. `test_t5_retry_skips_a_merged_child` resets the line by hand. `afk-run.md` says "A retry skips a child that is already merged" but does not say how to start a retry. Add that step to `afk-run.md`, or let approve run again on a task with status `blocked` after a merge failure.

Decision: pending
