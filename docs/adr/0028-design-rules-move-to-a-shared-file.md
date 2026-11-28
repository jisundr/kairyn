# 28. The design stage moves its slice and test-plan rules to a shared file, not to new stages

Date: 2026-11-28

## Status
Accepted. Keeps [ADR 6](0006-design-is-a-required-stage.md): one design stage with one approval stop.

## Context
Task 2026-11-28-split-design-stage. `plugin/stages/DESIGN.md` was at 456 of 500 tokens, up from 420 after the `_approval.md` slice. The next rule fit only with cuts. The backlog idea named a full split into a plan stage and a test-plan stage. That split changes `STATE.md` stages, `afk.py`, which reads the Tasks and Test plan of `DESIGN.md`, the eval checks and the design eval. ADR 6 rejected the name `plan` and a second approval stop.

## Decision
- Split the instructions only. Design stays one stage with one `DESIGN.md` output and one approval stop (D2, D3).
- The full split into a plan stage and a test-plan stage is rejected (D2).
- Steps 6 and 7 of `DESIGN.md` (slices `T<n>` and the Test plan) move word for word to `plugin/stages/_slices.md`. Step 6 says to follow it (D6, D7).
- `DESIGN.md` is at most 350 tokens. A test checks it (D4).
- No change to `templates/STATE.md`, `templates/DESIGN.md`, `afk.py` or `evals/checks.py` (R5).

## Consequences
- `DESIGN.md` is at 346 tokens and `_slices.md` at 142, in 0.21.4.
- The design eval at 10 runs passed every metric. Quality mean was 4.0, the gate exactly (run 20261128T104808Z).
- If the agent skips `_slices.md`, task plans lose slices and the Test plan (K1). Only the design eval shows it.
- A new design rule goes into `DESIGN.md` or `_slices.md`, whichever has room. A full split stays possible later.
