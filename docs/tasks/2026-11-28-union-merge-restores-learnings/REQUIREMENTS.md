---
task: 2026-11-28-union-merge-restores-learnings
stage: requirements
summary: "A merge driver for this repo's learnings.md keeps parallel appends and a retro's removals; --install sets it up; a pytest proves it."
---

# Requirements: A union merge restores learnings a retro removed

## Problem statement
This repo's `.gitattributes` merges `.kairyn/learnings.md` by `union`. A union merge keeps the lines that one side deleted. A branch from before a retro thus restores the removed lines on a rebase, with no conflict. The 97e81eb retro lost 8 lines this way. A plain merge keeps the removals, but parallel appends then conflict.

## Scope
In: a merge driver script in `scripts/` with an `--install` flag (D2, D4)
In: the `.gitattributes` line and comment for `.kairyn/learnings.md` (D2)
In: `tests/test_gitattributes.py`, changed to test the driver (D3)
In: one line in the Commands block of `CLAUDE.md` (D4)
In: a new inbox idea in `docs/backlog/` for a consumer driver (D5)
Out: any change to `plugin/` (D5)
Out: a change to how GitHub merges pull requests (A2)

## Requirements
- R1: When git merges `.kairyn/learnings.md` in this repo, the merge driver shall keep each line that either side adds. (D2)
- R2: When git merges `.kairyn/learnings.md` in this repo, the merge driver shall drop each line of the base that either side removes. (D2)
- R3: The merge driver shall keep the line order of the current side and put the lines that only the other side adds after them. (A1)
- R4: The merge driver shall exit 0 and leave no conflict markers. (D2)
- R5: When a user runs the driver script with `--install`, the script shall write the `git config` driver entry for this repo and print it. (D4)
- R6: When the driver entry already exists, `--install` shall leave the same entry and exit 0. (D4)
- R7: If a clone has no driver entry, git shall do its normal text merge of `.kairyn/learnings.md`. (D2)
- R8: The test suite shall run a retro case and a parallel-append case through real git in a temp repo with the driver set up. (D3)
- R9: The `CLAUDE.md` Commands block shall name the `--install` command once. (D4)
- R10: The backlog shall hold a new idea, status inbox, for a merge driver in consumer repos. (D5)

## Non-functional needs
State only what a source states. Else: not applicable: <reason>.
- Accessibility: not applicable: no source states one.
- Performance: not applicable: no source states one.
- Security: not applicable: no source states one.
- Observability: not applicable: no source states one.
- Size: `CLAUDE.md` stays within its 700-token budget in `.harness/budgets.yml`. (CLAUDE.md)
- Compatibility: the script runs on Python 3.9 with the standard library only, because git runs it with the `python3` on `PATH`. (A3)

## Assumptions, risks and dependencies
| ID | Kind | Item | Owner |
|---|---|---|---|
| A1 | assumption | Line order: current side first, then the other side's new lines. Stages append at the end, so new lines stay at the end. | Jayson De los Reyes |
| A2 | assumption | GitHub does not run custom merge drivers. Branches are rebased locally before a merge, so the driver acts there. | Jayson De los Reyes |
| A3 | assumption | Git runs the driver with the `python3` on `PATH`, which can be macOS's 3.9. `tests/test_python39.py` covers only `plugin/scripts/`, so the new test runs the driver under 3.9 or the design extends it. | design |
| K1 | risk | `CLAUDE.md` is at 700 of 700 tokens. The new line needs a cut elsewhere in `CLAUDE.md`. | design |
| K2 | risk | The driver compares whole lines. Two branches that add the same line produce one line. A line that appears twice can lose a copy. | design |

## Acceptance criteria
- [ ] A pytest merges a branch from before a retro after the retro: the removed lines stay removed and the branch's new line stays. (R2, R8)
- [ ] A pytest merges two branches that each append a line: both lines are present, exit 0, no `<<<<<<<`. (R1, R4, R8)
- [ ] A pytest checks the result order: the current side's lines, then the other side's new lines. (R3)
- [ ] A pytest runs `--install` twice in a temp repo: `git config` holds one driver entry, and both runs exit 0. (R5, R6)
- [ ] A pytest merges with no driver entry and gets a conflict on the retro case, not a restored line. (R7)
- [ ] `git check-attr merge .kairyn/learnings.md` names the driver, not `union`. (R1, R2)
- [ ] `CLAUDE.md` names the `--install` command once, and `budgets.py` passes. (R9)
- [ ] A new file in `docs/backlog/` has `status: inbox` and names the consumer driver. (R10)

## Open questions and answers
- None.

Approval: Jayson De los Reyes, 2026-11-28T11:05:56Z, "Approve" (relayed by Kairyn Steward)
