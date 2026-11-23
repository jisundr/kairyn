---
task: 2026-11-23-grill-on-sonnet
stage: grill
summary: "A CONCEPT.md template fixes the grill heading failures; one 10-run pass on Sonnet proves it."
---

# Concept: Grill on Sonnet has never passed a 10-run gate

## Concept
Grill fails its 10-run gate because 2 in 10 outputs write `# Concept` where the check needs `## Concept`. Grill has no `CONCEPT.md` template, so the model picks the format. A new `plugin/templates/CONCEPT.md` with the four `##` sections fixes it, and the GRILL.md Output section points to it. Guessed timestamps and the model choice stay out of scope. One 10-run pass of grill, init and upgrade on Sonnet proves the fix.

## Decisions
- D1: The problem is that grill fails its 10-run gate, whatever the cause. The model choice is a separate decision, and only if grill still fails after a fix. (user)
- D2: Add `plugin/templates/CONCEPT.md` with the four `##` sections, as requirements and design have. The GRILL.md Output section points to it instead of listing the sections. (user accepted)
- D3: This task does not try to stop guessed timestamps. One run in 30 guessed one, which is within the 9/10 gate. If they recur in the proof runs, that is a model question for a separate decision (D1). (user)
- D4: One `/run-evals grill init upgrade --all-evals` at 10 runs, grill on Sonnet, proves the fix: every gate passes and no `# Concept` failure. About $4. If grill fails for another reason, the task stops and the model choice becomes its own decision. (user accepted)

## Terms
| Term | Meaning |
|---|---|
| gate | The pass rates and judge scores in `evals/promptfoo/grill.yaml` that a 10-run eval must meet. |

## Open branches
None
