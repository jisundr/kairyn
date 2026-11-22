---
task: 2026-11-22-stage-skills
stage: build
summary: "Sonnet skills cut stage cost by 53 to 59% at the same pass rate in a 2-run smoke. Grill quality drops from 5.0 to 4.3."
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

- `requirements`, `model-routing`: `sonnet`. Same quality, half the cost.
- `grill`: `sonnet` passes, but `challenges` sits on its gate. The 10-run gate decides (K2).
- K1: the model applies to the skill's turn only. Turns after it (grill answers, approval) and the stage-file route cost the same as before. `running-stages.md` tells users to set `/model`.
