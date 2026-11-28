---
task: 2026-11-28-split-design-stage
stage: grill
summary: "Make room under the design stage's 500-token budget; the backlog idea names a split into plan and test-plan stages."
---

# Concept: Split the design stage

## Concept
The design stage gets room under its 500-token budget without a change to the stage shape. Steps 6 and 7 of `plugin/stages/DESIGN.md`, the slices and the test plan, move to a new shared file `plugin/stages/_slices.md` that `DESIGN.md` tells the agent to follow. Design stays one stage with one `DESIGN.md` output and one approval, so `STATE.md`, `afk.py` and the eval structure do not change. After the move `DESIGN.md` is at most 350 tokens; a pytest that fails first proves it, and the 3 existing design eval scenarios at 10 runs prove the behaviour did not change. At close the backlog idea closes and an ADR records the rejected full split.

## Decisions
- D1: Do the change now. `DESIGN.md` is at 456/500. (user)
- D2: Split the instructions only. Design stays one stage with one output and one approval. Rules move to a helper file that `DESIGN.md` loads, as `_approval.md` does. No change to `STATE.md` stages, `afk.py` or the eval structure. (user)
- D3: One approval stop. D2 makes this moot. (user)
- D4: After the change, `DESIGN.md` is at most 350 tokens. (user)
- D5: Scope is the design stage only. `MODEL-ROUTING.md`, `RETRO.md` and `CLOSE.md` stay as they are. (user)
- D6: Steps 6 and 7 of `DESIGN.md` move to the helper: slices `T<n>` and the test plan. Steps 1-5 stay. (user)
- D7: The helper is `plugin/stages/_slices.md`. The name `plan` collides with Claude Code plan mode (ADR 6). (user)
- D8: Proof: a pytest that fails first, then the 3 existing design eval scenarios at 10 runs. No new eval. The Steward approves the eval cost first. (user)
- D9: Close the backlog idea at the end. The ADR records that the full plan and test-plan split was rejected. (user)

## Terms
| Term | Meaning |
|---|---|
| design stage | `plugin/stages/DESIGN.md` and its output `DESIGN.md` |
| full split | two stages with own `STATE.md` entries, outputs and evals (rejected, D2) |
| helper file | a shared `_*.md` file in `plugin/stages/` that a stage follows |

## Open branches
- None

Approval: Jayson De los Reyes, 2026-11-28T01:36:36Z, "Approve"
