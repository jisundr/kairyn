---
task: 2026-11-23-design-stage
stage: design
summary: "Design for the design stage: copy the requirements stage pattern, add pure DESIGN.md checks, evals first. Written by hand."
---

# Design: Design stage between requirements and code

Written by hand from the playbook (`.harness/README.md`, principle 5). The design stage does not exist yet.

## Approach
Option A. The design stage copies the requirements pattern: a stage file, a template, a skill on Opus, one approval line. New checks for `DESIGN.md` are pure functions in `evals/checks.py` with unit tests. `approval_problems` already reads any text, so the design eval uses it as is. Only `structural_problems` gets a parameter for the next stage. A takes the least new code and keeps the requirements eval stable.

## Options
| Option | What | Cost | Risk |
|---|---|---|---|
| A (smallest thing) | Copy the requirements pattern. Add design checks. Change one structural check. | About 6 files changed, 5 new. | Some copy between requirements and design checks. |
| B | First make the checks generic for any gated stage, then add design on them. | A, plus a refactor of the requirements and grill checks. | The refactor can break the requirements eval. The backlog idea `approval-handoff` changes the same code later. |
| C | Add design sections to `REQUIREMENTS.md`. | Small. | D1, D2 and D5 reject it. The stage file is at 498/500 tokens. |

## Tasks
- T1: Add pure `DESIGN.md` checks to `evals/checks.py`. They check the four sections and at least two options, one the smallest thing. Each criterion needs a task and a test. Each path with a `/` exists or carries `(new)`. Tests in `tests/test_design_checks.py` (new). Done: `uv run pytest` passes, and the tests failed before the checks.
- T2: Give `structural_problems` a next stage. After approval, expect `stage: design` and `status: in-progress`. Update `tests/test_requirements_checks.py`. Done: unit tests pass, and `requirements_approval` fails on the current stage file.
- T3: Add the design eval: `evals/promptfoo/design.yaml` (new), `make_design_repo`, `run_design` and `run_design_approval` in `evals/runner.py`, asserts and a judge in `evals/promptfoo/asserts.py`, scenarios in `evals/promptfoo/provider.py`. The fixture is the report CLI with an approved `REQUIREMENTS.md`. `claude_session` accepts a callable prompt, so turn 2 names a rejected option from turn 0. Done: both scenarios run and fail, because no design stage exists.
- T4: Add `design: pending` to `plugin/templates/STATE.md`. Change the State update in `plugin/stages/REQUIREMENTS.md` to set `stage: design`. Add a stage-order test to `tests/test_static.py`. Done: `requirements_approval` passes at 10 runs.
- T5: Write `plugin/stages/DESIGN.md` (new) with `order: 2`, `plugin/templates/DESIGN.md` (new) and `plugin/skills/design/SKILL.md` (new) on Opus. Step 1 stops when `REQUIREMENTS.md` has no approval line. Add design to `tests/test_skills.py`. Done: both design scenarios pass their gates at 10 runs.
- T6: Update `.harness/workflows/running-stages.md`, `.harness/workflows/task-lifecycle.md` and `README.md`. Bump `plugin/.claude-plugin/plugin.json` and run `scripts/release_hashes.py --write`. Run `/kairyn:upgrade` on this repo. Done: `uv run pytest` and `claude plugin validate plugin` pass.

## Test plan
| Criterion | Task | Test |
|---|---|---|
| AC1 plugin validates, stage and skill accepted | T5 | `claude plugin validate plugin`, `tests/test_static.py`, `tests/test_skills.py` |
| AC2 requirements eval expects `stage: design` | T2, T4 | eval `requirements_approval`, assert `records_approval` |
| AC3 template lists `design: pending` | T4 | `tests/test_static.py`, stage-order test |
| AC4 design scenario 1 | T1, T3, T5 | eval `design`: well_formed, traceable, options, grounded, waits_for_approval, judge |
| AC5 design scenario 2 | T3, T5 | eval `design_approval`: approval_gate, rewrites_option, records_approval |
| AC6 approval check in step 1 | T5 | Review of `plugin/stages/DESIGN.md` (new) |
| AC7 pytest passes, docs name the stage | T6 | `uv run pytest`, a test that `README.md` and `.harness/workflows/running-stages.md` name `/kairyn:design` |

Approval: Jayson De los Reyes, 2026-11-23T01:31:30Z, "yes"
