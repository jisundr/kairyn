---
task: 2026-11-23-eval-request-hedge
stage: requirements
summary: "One Writing rule in _template.md: rewrite hedges copied from the request. Prove it with one 10-run pass of five evals."
---

# Requirements: Requirements plain_language fails on hedges from the eval request

## Problem statement
The requirements stage copies `would` from a request into `REQUIREMENTS.md`, against its own writing rule. Requirements `plain_language` then fails its gate: 7/10 in run `20261123T014549Z`, 6/10 in run `20261122T204013Z`.

## Scope
In: one line in the Writing section of `plugin/stages/_template.md` (D2).
In: one 10-run pass of the five evals that depend on `_template.md` (D3).
Out: changes to the eval request (D1). Changes to `checks.ste_problems`. Changes to `plugin/stages/REQUIREMENTS.md`.

## Requirements
- R1: The Writing section of `plugin/stages/_template.md` shall state that the hedge rule also applies to words copied from the request. (D2)
- R2: The eval request `REQUEST` in `evals/runner.py` shall stay unchanged. (D1)
- R3: The `_template.md` file shall stay within its 500-token budget. (A1)
- R4: The plugin shall carry a newer version and current release hashes. (A2)
- R5: The requirements, design, grill, model-routing and exit evals shall each pass every gate at 10 runs. (D3)
- R6: The requirements eval shall show `plain_language` at 8/10 or more. (D3)
- R7: Where an eval run uses the dry-run request, its `REQUIREMENTS.md` shall contain no `would`. (D3, A3)

## Non-functional needs
State only what a source states. Else: not applicable: <reason>.
- Accessibility: not applicable: no user interface.
- Performance: not applicable: no source states a time limit.
- Security: not applicable: no new input.
- Observability: not applicable: eval summaries already show results and cost.

## Assumptions, risks and dependencies
| ID | Kind | Item | Owner |
|---|---|---|---|
| A1 | assumption | Repo rule: over budget, cut text; never raise the limit. | build |
| A2 | assumption | Repo rule (`upgrade.md`): a change under `plugin/` bumps the version and regenerates `plugin/release-hashes.json`. | build |
| A3 | assumption | The dry-run request runs in the `requirements` and `requirements_approval` scenarios: 20 `REQUIREMENTS.md` files. | build |
| A4 | assumption | This repo's `.kairyn/stages/_template.md` takes the change through `/kairyn:upgrade`. | build |
| K1 | risk | The new line changes how grill, design, model-routing or exit write. The five evals catch it. | build |
| K2 | risk | `plain_language` still fails on long sentences with no hedge. | Jayson |
| K3 | risk | The five 10-run evals cost about $45 to $50. | Jayson |

## Acceptance criteria
- [ ] `plugin/stages/_template.md` Writing names words copied from the request, and budgets pass. (R1, R3)
- [ ] `git diff` shows no change to `REQUEST` in `evals/runner.py`. (R2)
- [ ] `plugin.json` has a newer version, and `uv run pytest` passes with current release hashes. (R4)
- [ ] One `evals/run.py` summary shows all five evals passing every gate at 10 runs. (R5)
- [ ] That summary shows requirements `plain_language` at 8/10 or more. (R6)
- [ ] A search of the 20 dry-run `REQUIREMENTS.md` files finds no `would`. (R7)

## Open questions and answers
- Q1: Run `20261123T035336Z` left `would` in 10 of 20 dry-run files: 1 in the stage's own words, 10 matches that quote the request. Does R7 block the change? A: No. The writing rule asks for ASD-STE100 about 80% of the way, and `plain_language` passed 10/10. R7 is met in spirit, not in full. (Jayson, after build)

Approval: Jayson De los Reyes, 2026-11-23T03:01:46Z, "approved"
