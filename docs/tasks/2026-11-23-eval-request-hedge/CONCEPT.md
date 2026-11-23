---
task: 2026-11-23-eval-request-hedge
stage: grill
summary: "Concept for the requirements plain_language failures caused by 'would' in the eval request. Confirmed by the user."
---

## Concept
The requirements stage copies hedges such as "would" from a request into `REQUIREMENTS.md`, against its own writing rule. The fix is in the stage, not in the eval: the eval request stays as the test. One line in the Writing section of `_template.md` says the rule also applies to words copied from the request, so every stage gets it. One 10-run pass of the five dependent evals proves it, with requirements `plain_language` at 8/10 or more and no copied hedge.

## Decisions
- D1: The problem is the stage. It copies hedges from the request into `REQUIREMENTS.md` against its own writing rule. The eval request stays as it is: it is now the test. (user)
- D2: The rule goes in the Writing section of `plugin/stages/_template.md`: rewrite words copied from the request too. Every stage reads that section, so it covers design and grill. (user)
- D3: One 10-run pass of the five evals that depend on `_template.md` proves the fix: requirements, design, grill, model-routing and exit. Requirements `plain_language` passes at 8/10 or more, and no `REQUIREMENTS.md` holds a hedge copied from the request. (user accepted)

## Terms
| Term | Meaning |
|---|---|
| hedge | A word that `checks.ste_problems` flags: should, would, might, may. |
| eval request | The fixed request text `REQUEST` in `evals/runner.py` that the requirements eval sends. |

## Open branches
None
