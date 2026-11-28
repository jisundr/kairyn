---
task: 2026-11-28-union-merge-restores-learnings
stage: design
summary: "Option A: scripts/merge_learnings.py, a line-set merge driver with --install; .gitattributes names it; pytest runs real git merges."
---

# Design: A union merge restores learnings a retro removed

## Approach
Option A. One standard-library script is the driver and the installer, so it meets R1 to R10 with the fewest files. `.gitattributes` names `merge=learnings` in place of `union`. The driver runs as `python3 scripts/merge_learnings.py %O %A %B`. Git runs drivers at the top of the worktree, so the relative path works in each worktree. The driver writes `%A`: the lines of `%A` that neither side removed, then the lines that only `%B` adds. No plugin file changes, so no eval runs.

K1: the new Commands line costs about 24 tokens. The design cuts the CLAUDE.md rule "Stage files are upper case (`REQUIREMENTS.md`); stage names and `STATE.md` values lower case." `.harness/workflows/change-a-stage.md` line 39 states the same rule, and that doc loads when someone edits a stage. With the cut, `budgets.py` gives 700/700 for CLAUDE.md.

## Options
| Option | What | Cost | Risk |
|---|---|---|---|
| A (smallest thing) | `scripts/merge_learnings.py`: merge with `%O %A %B`, or `--install` writes `merge.learnings.name` and `merge.learnings.driver` with `git config`. | About 40 lines of script, 6 tests. | Low. If a clone has no config, git merges as text and conflicts (R7). |
| B | The driver as a one-line shell command in `git config`, no script. | About 10 lines of tests. | High. Shell quoting is hard to read and to test, and `--install` has no home. |
| C | Option A, plus a CLAUDE.md cut elsewhere, for example the `uv run pytest never runs evals` clause. | Same as A. | That clause repeats the pytest comment, but it also guards evals. The upper-case rule is a plain duplicate. |

## Tasks
- T1: Tracer bullet: the driver and the switch. `merge_learnings.py` merges three files (R1 to R4). `.gitattributes` uses `merge=learnings` and its comment says why. `test_gitattributes.py`: `check-attr` names `learnings`; a temp repo with the driver config runs a retro rebase and a parallel-append merge; the order test. Files: `scripts/merge_learnings.py` (new), `.gitattributes`, `tests/test_gitattributes.py`. Done: `uv run pytest tests/test_gitattributes.py` exits 0.
- T2: `--install` writes and prints the two config entries and gives the same result when run again (R5, R6). A test runs it twice in a temp repo. A test with no driver config gets a conflict on the retro case (R7). A test runs the driver under Python 3.9 when `uv` finds one. Files: `scripts/merge_learnings.py`, `tests/test_gitattributes.py`. after: T1. Done: `uv run pytest tests/test_gitattributes.py` exits 0.
- T3: Docs. CLAUDE.md: add the `--install` line, cut the upper-case rule. New inbox idea for a consumer driver. Run `--install` in this clone. Files: `CLAUDE.md`, `docs/backlog/<timestamp>-consumer-learnings-merge-driver.md` (new). after: T2. Done: `uv run pytest && uv run python plugin/scripts/budgets.py` exits 0.

## Test plan
| Criterion | Task | Test |
|---|---|---|
| AC1 a retro rebase keeps the removals and the branch's new line | T1 | `test_rebase_after_a_retro_keeps_its_removals` |
| AC2 two parallel appends keep both lines, exit 0, no markers | T1 | `test_two_branches_that_each_add_a_learning_merge_cleanly` |
| AC3 order: current side, then the other side's new lines | T1 | `test_driver_keeps_current_order_then_new_lines` |
| AC4 `--install` twice gives one entry, both exit 0 | T2 | `test_install_is_idempotent` |
| AC5 no driver config: the retro case conflicts | T2 | `test_without_driver_config_a_retro_case_conflicts` |
| AC6 `check-attr` names the driver, not `union` | T1 | `test_learnings_md_merges_by_the_driver` |
| AC7 CLAUDE.md names `--install` once; budgets pass | T3 | `uv run python plugin/scripts/budgets.py`; `grep -c -- '--install' CLAUDE.md` gives 1 |
| AC8 a new inbox idea names the consumer driver | T3 | `grep -l 'status: inbox' docs/backlog/*consumer-learnings-merge-driver.md` |

Approval: Jayson De los Reyes, 2026-11-28T11:06:38Z, "Approve" (relayed by Kairyn Steward)
