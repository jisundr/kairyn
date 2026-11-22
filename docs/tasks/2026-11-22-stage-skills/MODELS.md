---
task: 2026-11-22-stage-skills
stage: build
summary: "Grill and model-routing run on Sonnet (53 to 59% cheaper). Requirements stays on Opus: Sonnet failed its 10-run gate."
---

# Models per stage: smoke evidence

Smoke runs, 2 per test, so they do not vouch for a pass. Before: skills `model: inherit`, which is the session model `opus[1m]`. After: skills `model: sonnet`. The judge is Opus in both. Runs: `evals/results/20261122T124227Z` in this checkout (after) and in a worktree with the skills set to `inherit` (before). Cost is `total_cost_usd`, an estimate.

## Stage cost without the judge, 2 runs

| Scenario | Route | Before (Opus) | After (Sonnet) | Change | Quality, before → after |
|---|---|---|---|---|---|
| `requirements` | skill | $0.75 | $0.35 | -53% | 4.3 → 4.2 |
| `model_routing` | skill | $0.81 | $0.33 | -59% | 4.8 → 4.8 |
| `grill` | skill, then 3 turns on the session model | $1.15 | $0.54 | -53% | 5.0 → 4.3; `challenges` 5.0 → 4.0 (gate 4) |
| `requirements_with_concept` | stage file | $0.85 | $0.90 | none | no judge |
| `requirements_approval` | stage file | $0.98 | $1.07 | none | no judge |

Every metric passed in both runs. Plain language for `requirements` went from 1/2 to 2/2.

## Other costs (after)

- `init`, `check` and `upgrade` on Haiku: $0.005 per run. No Opus baseline ran.
- The Opus judge: $0.16 per run, about a third of a stage eval.
- All six evals at 2 runs: $4.21. At 10 runs: about $21.

## Choices

- `model-routing`, `grill`: `sonnet`. Both pass the 10-run gate.
- `requirements`: `opus`. On Sonnet it failed the 10-run gate (K2).
- K2 follow-up: scripted timestamps and plainer wording could let `requirements` move to Sonnet later.
- K1: the model applies to the skill's turn only. Turns after it (grill answers, approval) and the stage-file route cost the same as before. `running-stages.md` tells users to set `/model`.

## 10-run gate

| Eval | Model | Result | Run |
|---|---|---|---|
| `grill` | sonnet | pass; `challenges` 4.0 (gate 4), `recommends` 4.2, min 3 | `20261122T130058Z` |
| `model-routing` | sonnet | pass; `well_formed` 9/10, quality 4.7, min 4 | `20261122T204013Z` |
| `requirements` | sonnet | fail; `well_formed` 8/10 (guessed `updated:` times), `plain_language` 6/10 ("would", long lines) | `20261122T204013Z` |
| `requirements` | opus | pass after two fixes: EARS subject in step 5 (`specified` 7/10 → 10/10), judge told the run's no-questions instruction; quality 4.4, min 4 | `20261122T230826Z` |
| `upgrade` | haiku | pass, 10/10 | `20261122T223407Z` |
