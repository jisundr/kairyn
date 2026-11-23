---
task: 2026-11-23-eval-request-hedge
stage: design
summary: "Extend the hedge bullet in _template.md Writing to words copied from the request, bump to 0.7.1, prove it with five 10-run evals."
---

# Design: Requirements plain_language fails on hedges from the eval request

## Approach
Option D. Option A passed `plain_language` 10/10 in run `20261123T032454Z`, but 13 of 20 dry-run files still held `would` (R7). In 6, the stage used it in its own words; in 7, it quoted the request. Option D bans quoting too and gives a rewrite example. Three cuts in wording keep `_template.md` at 487/500.

## Options
| Option | What | Cost | Risk |
|---|---|---|---|
| A (smallest thing) | Extend the hedge bullet: the rule also covers words copied from the request. | About 10 tokens in one bullet: about 499/500. | Long sentences from the request still pass through (K2). |
| B | Add a new bullet: rewrite every word copied from the request in this style. | About 14 tokens. It also covers long sentences. | `_template.md` goes to about 503/500, over budget. The hedge link is less direct. |
| D | Extend the bullet: no hedge, not even quoted from the request, plus the example `it would print` becomes `it prints`. Cut wording in Time, State update and Learnings. | About 22 tokens added, 24 cut: 487/500. | Grill reads the same template. Grill `well_formed` was 9/10 and 8/10 after option A, against 10/10 before. |
| C | Add a step to each stage: lint the output with `checks.ste_problems` before the State update. | Edits to four stage files, two of them at 495 to 499 tokens. | Stages cannot import `evals/` in a user repo. Large cost for one word. |

## Tasks
- T1: Write option D in `plugin/stages/_template.md`. Done: the bullet bans quoted hedges and gives the example, and `plugin/scripts/budgets.py` reports the file within 500 tokens.
- T2: Keep `plugin/.claude-plugin/plugin.json` at 0.7.1 and run `scripts/release_hashes.py --write`. Done: `uv run pytest` passes.
- T3: Run `plugin/scripts/upgrade.py --root .` on this repo. Done: `.kairyn/stages/_template.md` is replaced, with no conflict.
- T4: In a subagent, run `evals/run.py` for requirements, design, grill, model-routing and exit with `--all-evals` at 10 runs. Done: the summary shows every gate passing.
- T5: Search the `requirements` and `requirements_approval` outputs of the T4 run for `would`. Done: no match in the 20 files.

## Test plan
| Criterion | Task | Test |
|---|---|---|
| AC1 Writing names copied words, budgets pass | T1 | Read the bullet; `plugin/scripts/budgets.py` |
| AC2 `REQUEST` unchanged | T1 | `git diff main -- evals/runner.py` is empty |
| AC3 newer version, current hashes | T2 | `uv run pytest` (`tests/test_release_hashes.py`) |
| AC4 five evals pass at 10 runs | T3, T4 | `summary.md` of the T4 run |
| AC5 `plain_language` 8/10 or more | T4 | The requirements `plain_language` row in that `summary.md` |
| AC6 no `would` in 20 dry-run files | T4, T5 | `grep -l` over the 20 `REQUIREMENTS.md` files of the T4 run |

Approval: Jayson De los Reyes, 2026-11-23T03:53:23Z, "yes, run the evals in a subagent"
