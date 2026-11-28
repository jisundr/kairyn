---
task: 2026-11-28-split-design-stage
stage: requirements
summary: "Move the slice and test-plan rules of the design stage to plugin/stages/_slices.md so DESIGN.md is at most 350 tokens."
---

# Requirements: Split the design stage

## Problem statement
`plugin/stages/DESIGN.md` is at 456 of 500 tokens. It was 420 after the `_approval.md` slice. The next rule fits only with cuts, and cuts that no eval checks get lost. The design stage needs room under its budget without a change to its shape.

## Scope
In: move steps 6 and 7 of `plugin/stages/DESIGN.md` to a new `plugin/stages/_slices.md`. (D6, D7)
In: tests and eval `# depends:` lines that follow the move. (D8)
In: version bump, release hashes and this repo's upgrade to the new version. (A2)
In: at close, close the backlog idea and write an ADR on the rejected full split. (D9)
Out: a plan stage or a test-plan stage with own `STATE.md` entries or outputs. (D2)
Out: `MODEL-ROUTING.md`, `RETRO.md`, `CLOSE.md` and other stage files. (D5)
Out: a new eval case. (D8)

## Requirements
- R1: The design stage file `plugin/stages/DESIGN.md` shall be at most 350 tokens, as `plugin/scripts/budgets.py` counts them. (D4)
- R2: The plugin shall ship `plugin/stages/_slices.md` with each rule of the current steps 6 and 7: slices `T<n>`, T1 the tracer bullet, each slice crosses every layer, `after:`, `Done: `<command>``, the `(approval)` mark, `AC<n>` numbers, one Test plan row for each criterion, and `Manual:` tests. (D6, D7)
- R3: When the design stage cuts the chosen option into tasks, `DESIGN.md` shall tell the agent to follow `_slices.md`. (D2)
- R4: The design stage shall stay one stage with one `DESIGN.md` output and one approval stop. (D2, D3)
- R5: The plugin shall not change `plugin/templates/STATE.md`, `plugin/templates/DESIGN.md`, `plugin/scripts/afk.py` or `evals/checks.py`. (D2)
- R6: The design eval `# depends:` line and `change-a-stage.md` shall name `_slices.md`. (A3)
- R7: When `plugin/` changes, the plugin version shall go up and `plugin/release-hashes.json` shall match it. (A2)
- R8: When the task closes, the backlog idea shall close and an ADR shall record that the full split was rejected. (D9)

## Non-functional needs
State only what a source states. Else: not applicable: <reason>.
- Accessibility: not applicable: no user interface.
- Performance: `DESIGN.md` at most 350 tokens. (D4)
- Security: not applicable: no source states a need.
- Observability: not applicable: no source states a need.

## Assumptions, risks and dependencies
| ID | Kind | Item | Owner |
|---|---|---|---|
| A1 | assumption | `_slices.md` falls under the `plugin/stages/*.md` budget of 500 tokens. | design |
| A2 | assumption | The `upgrade.md` bump rule applies: a patch bump, 0.21.2 to 0.21.3, and this repo takes it with `/kairyn:upgrade`. | design |
| A3 | assumption | `_slices.md` follows the `_approval.md` pattern: init copies it, and evals that read it list it in `# depends:`. | design |
| K1 | risk | The agent skips `_slices.md` and writes a weaker task plan. The 3 design eval scenarios at 10 runs show it. | build |
| K2 | risk | The eval selector also picks the `init` eval (`plugin/stages/*`) and the `upgrade` eval (`release-hashes.json`). | Steward |

## Acceptance criteria
- [ ] A new pytest fails before the move and passes after it: `DESIGN.md` is at most 350 tokens and names `_slices.md`. (R1, R3)
- [ ] A pytest shows that `_slices.md` holds the words `tracer bullet`, `after:`, `Done: ``, `(approval)`, `approval:`, `AC<n>`, `Test plan` and `Manual:`. (R2)
- [ ] `git diff main` shows no change to `plugin/templates/STATE.md`, `plugin/templates/DESIGN.md`, `plugin/scripts/afk.py` or `evals/checks.py`. (R4, R5)
- [ ] The design eval scenarios `design`, `design_approval` and `design_child_repo` meet each `min_pass_rate` at 10 runs. (R2, R3, R4)
- [ ] `evals/promptfoo/design.yaml` `# depends:` and `.harness/workflows/change-a-stage.md` name `_slices.md`. (R6)
- [ ] `plugin/.claude-plugin/plugin.json` has a newer version, `uv run pytest` passes and `claude plugin validate plugin` passes. (R7)
- [ ] After close, the idea file and its README row are gone and a new ADR names the rejected full split. (R8)

## Open questions and answers
- Q1: Which rules move? A: Steps 6 and 7. (Jayson De los Reyes, D6)
- Q2: Name of the helper? A: `_slices.md`. (Jayson De los Reyes, D7)

Approval: Jayson De los Reyes, 2026-11-28T01:38:42Z, "Approve"
