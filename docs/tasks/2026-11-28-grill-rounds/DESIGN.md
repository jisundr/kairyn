---
task: 2026-11-28-grill-rounds
stage: design
summary: "Option A: GRILL.md steps 4-5 ask rounds of 1-3 numbered questions; a rounds check replaces one_question; cut the Optional line to fit 500 tokens."
---

# Design: Grill asks questions in numbered rounds

## Approach
Option A. It rewrites steps 4 and 5 of `GRILL.md` and swaps one eval check, so it meets R1 to R9 with the fewest changes. The draft is 490/500 tokens: it cuts the "Optional: run it before `requirements`…" line (K1). The skill `description` already says when to run grill, so the cut loses nothing.

## Options
| Option | What | Cost | Risk |
|---|---|---|---|
| A (smallest thing) | Rewrite `GRILL.md` steps 4-5 and `purpose`; cut the Optional line. In `evals/checks.py`, `grill_round_problems` replaces `grill_reply_problems`, and `round_decision_problems` counts decisions per question. `asserts.py`: `rounds` replaces `one_question`. | About 40 lines of checks and tests, 2 grill evals (about $11 to $14). | Low. Only grill and its eval change. |
| B | Option A, but move the round rules to a shared `_rounds.md`. | Option A, plus a new shipped file, its hashes and upgrade tests. | Only grill asks questions, so the split adds a file for one reader. |
| C | Option A, plus a second eval scenario with a partial numbered reply (R6). | Option A, plus about $6 per grill eval run. | The owner chose one scenario (D6). |

## Tasks
- T1: Tracer bullet: `grill_round_problems(reply, min_questions)` fails 0 or more than 3 `Q<n>` markers, fewer Recommended lines than questions, fewer than `min_questions`, and more than 2 question marks per question. Files: `tests/test_grill_checks.py`, `evals/checks.py`. Done: `uv run pytest tests/test_grill_checks.py` exits 0.
- T2: `round_decision_problems(turns)`: after each accepted round, `CONCEPT.md` gains at least one `D<n>` per question of that round. `asserts.py`: `rounds` (turn 0 needs 2) replaces `one_question`; `records_answers` uses the new check. `grill.yaml` lists `rounds`. Files: `tests/test_grill_checks.py`, `evals/checks.py`, `evals/promptfoo/asserts.py`, `evals/promptfoo/grill.yaml`. after: T1. Done: `uv run pytest` exits 0.
- T3: Run the grill eval on the old `GRILL.md` after the owner says yes to its cost; `rounds` must fail. Files: none. after: T2. Done: `/run-evals grill` reports `rounds` FAIL.
- T4: `plugin/stages/GRILL.md` steps 4-5, `purpose` and the Optional cut. `plugin/skills/grill/SKILL.md` `description`: rounds. Bump the plugin patch version, run `scripts/release_hashes.py --write` and `plugin/scripts/upgrade.py --root .` for this repo's `.kairyn/stages/GRILL.md`. Files: `plugin/stages/GRILL.md`, `plugin/skills/grill/SKILL.md`, `plugin/.claude-plugin/plugin.json`, `plugin/release-hashes.json`, `.kairyn/stages/GRILL.md`, `.kairyn/.base/.kairyn/stages/GRILL.md`, `.kairyn/manifest.json`. after: T3. Done: `uv run pytest && claude plugin validate plugin && uv run python plugin/scripts/budgets.py` exits 0.
- T5: Run the grill eval at 10 runs on the new `GRILL.md`. Files: none. after: T4. Done: `/run-evals grill` reports PASS.

## Test plan
| Criterion | Task | Test |
|---|---|---|
| AC1 GRILL.md asks 1 to 3 numbered questions from the settled frontier | T4 | Read `plugin/stages/GRILL.md` step 4; grill eval `rounds` |
| AC2 extra questions go under Open branches, most unblocking first | T4 | Read `plugin/stages/GRILL.md` step 4 |
| AC3 each question has a Recommended line | T1, T5 | `test_round_needs_a_recommendation_per_question`; grill eval `rounds` |
| AC4 numbers continue across rounds | T4 | Read `plugin/stages/GRILL.md` step 4 |
| AC5 one decision per accepted question | T2, T5 | `test_round_decisions_*`; grill eval `records_answers` |
| AC6 a partial reply leaves the skipped questions open | T4 | Read `plugin/stages/GRILL.md` step 5 |
| AC7 pytest covers 0, 1, 3, 4 questions, no recommendation, turn 0 with 1 | T1 | `tests/test_grill_checks.py` round tests |
| AC8 grill.yaml lists `rounds`, not `one_question`, same 4 replies | T2 | `uv run pytest`; read `evals/promptfoo/grill.yaml` |
| AC9 the eval fails on the old GRILL.md and passes on the new one | T3, T5 | `/run-evals grill` twice; numbers from `summary.md` |
| AC10 GRILL.md within budget | T4 | `uv run python plugin/scripts/budgets.py` |

Approval: Jayson De los Reyes, 2026-11-28T01:40:39Z, "Approve"
