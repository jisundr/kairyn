---
task: 2026-11-23-retro-stage
stage: design
summary: "A retro.py script measures sizes. Exit reads its RETRO line and follows RETRO.md in the same turn. A retro eval gates it."
---

# Design: Retro stage

## Approach
Option A. A script does each size check: the `learnings.md` budget (R2, R17) and a full home (R10). Exit does not start a second skill. It follows `.kairyn/stages/RETRO.md` (new) in the same turn, so K2 does not apply. The `/kairyn:retro` skill runs the same file when the user starts it. The exit eval proves the path from exit.

## Options
| Option | What | Cost | Risk |
|---|---|---|---|
| A (smallest thing) | `retro.py` with `size` and `fits`. `exit.py close` prints `RETRO:`. `EXIT.md` follows `RETRO.md` on that line. | 1 script, 1 stage, 1 template, 1 skill, 1 eval, 1 line in `EXIT.md` | Retro from exit runs on the exit model (Sonnet). The eval gates it. |
| B | Same script. Exit starts the `/kairyn:retro` skill with the Skill tool. | As A, plus the Skill tool in the exit skill | Unproven: the K2 question. It also blocks `approval-handoff`. |
| C | `exit.py close` prints the `RETRO:` line, and the user starts retro. | As A, less one line in `EXIT.md` | Fails R3: exit does not start retro. |

## Tasks
- T1: Write `retro.py`. `size` prints `learnings.md <used>/<budget>` from `.harness/budgets.yml` and the built-in budgets (A1). `fits <home> --add <text>` prints `FITS`, `OVER <n>` or `KAIRYN-OWNED` (from `kairyn_files.owner_of`). Files: `plugin/scripts/retro.py` (new), `tests/test_retro.py` (new), `plugin/scripts/budgets.py`, `plugin/scripts/kairyn_files.py`. Done: `uv run pytest` passes.
- T2: `exit.py close` prints `RETRO: learnings.md <used>/<budget>` past half the budget. Files: `plugin/scripts/exit.py`, `tests/test_exit.py`. Done: both cases tested.
- T3: Write the eval first. Scenarios: proposal, approval, and exit with a full `learnings.md`. Files: `evals/promptfoo/retro.yaml` (new), `evals/promptfoo/exit.yaml`, `evals/runner.py`, `evals/promptfoo/provider.py`, `evals/promptfoo/asserts.py`, `evals/checks.py`, `tests/test_retro_checks.py` (new). Done: the checks have tests, and the eval fails with no stage.
- T4: Write the stage, its template and the skill (`model: sonnet`, as exit). Files: `plugin/stages/RETRO.md` (new), `plugin/templates/RETRO.md` (new), `plugin/skills/retro/SKILL.md` (new), `tests/test_skills.py`. Done: `uv run pytest` and `claude plugin validate plugin` pass.
- T5: Add one step to `EXIT.md`: on a `RETRO:` line, follow `.kairyn/stages/RETRO.md`. Keep it under 500 tokens (K1). Files: `plugin/stages/EXIT.md`. Done: budget test passes.
- T6: Docs and release. Cut `testing-and-evals.md` to fit the retro row. Run `/kairyn:upgrade` here, so this repo gets the stage. Files: `README.md`, `plugin/harness/.harness/workflows/running-stages.md`, `.harness/workflows/running-stages.md`, `.harness/workflows/testing-and-evals.md`, `plugin/.claude-plugin/plugin.json`, `plugin/release-hashes.json`. Done: `uv run pytest` passes.
- T7: Run the retro and exit evals at 10 runs. Done: both pass their gates.

## Test plan
| Criterion | Task | Test |
|---|---|---|
| AC1 stage, template and skill exist | T4 | `test_static.py`, `test_skills.py` |
| AC2 `RETRO:` line over half, none under | T2 | `test_exit.py` |
| AC3 exit with full learnings makes a retro folder | T3, T5 | exit eval scenario |
| AC4 one action per entry | T3, T4 | retro eval, `retro_problems` |
| AC5 moves name an existing home, not kairyn-owned | T1, T3 | `test_retro.py`, retro eval |
| AC6 backlog for test, guarded stage, full home | T1, T3 | retro eval fixture with all three |
| AC7 drop and keep reasons | T3 | retro eval |
| AC8 before approval, changes only in the folder | T3 | retro eval: `git status` |
| AC9 after approval, only kept entries and an approval line | T3 | retro approval scenario |
| AC10 backlog ideas quote; kept text unchanged | T3 | retro approval scenario |
| AC11 kept over half: excess and a question | T1, T3 | retro eval fixture |
| AC12 `budgets.yml` unchanged | T3 | retro approval scenario |
| AC13 retro eval passes at 10 runs | T7 | `/run-evals retro` |

Approval: Jayson De los Reyes, 2026-11-23T10:26:01Z, "approved, commit and open a PR"
