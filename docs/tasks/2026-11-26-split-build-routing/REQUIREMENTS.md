---
task: 2026-11-26-split-build-routing
stage: requirements
summary: "afk.py builds each slice in two sessions, an Opus test and Sonnet code; close and retro run on Haiku; each critical decision stays on Opus."
---

# Requirements: Opus makes each critical decision, cheaper models carry it out

## Problem statement
One Opus session writes both commits of each AFK build slice. The `test(T<n>)` commit holds the decisions; the `feat(T<n>)` commit only makes it green. close and retro only carry out decisions. A bot now reviews the human-gated steps (D6).

## Scope
In: two build sessions per slice in `afk.py`, build-tests on Opus and build-code on Sonnet (D3, D5)
In: `MODELS` in `afk.py`: reviewer Opus, gate Sonnet, review Opus (D5)
In: skill models: close and retro on Haiku; requirements, design, grill, model-routing, launchers and commands unchanged (D4, D7)
In: `BUILD.md` stage and the docs name the split; version bump and release hashes; at close, an ADR for D6 that amends ADR 0004 and 0008 (D3, request)
Out: a bot or solo switch, or a per-repo or per-run model (D1); a more technical design stage (split-design-stage stays open)

## Requirements
- R1: When `afk.py` builds a slice `T<n>`, it shall start a build-tests session on Opus. Its prompt names `T<n>`, the done command and its one commit, `test(T<n>)`. (D3, D5)
- R2: When the build-tests session ends, `afk.py` shall find the `test(T<n>)` commit and run the red check before it starts build-code. (D3)
- R3: If the build-tests session makes no `test(T<n>)` commit, or the done command exits 0 at it, then `afk.py` shall block the task with `T<n>` and the reason, and start no build-code session. (D3)
- R4: When the red check fails as expected, `afk.py` shall start a build-code session on Sonnet. The prompt names `T<n>`, its done command, the `test(T<n>)` commit, and the `feat(T<n>)` commit as the only commit to make. (D3, D5)
- R5: When the build-code session ends, `afk.py` shall run the green check at `feat(T<n>)` and write the `BUILD.md` row, as it does now. (D3)
- R6: If a slice has a `test(T<n>)` commit that fails its done command and no green `BUILD.md` row, then `afk.py` shall start only the build-code session for it. (A1)
- R7: The fix-round session shall run on the build-code model. (A2)
- R8: `afk.py` shall run the reviewer on Opus, each gate check on Sonnet and the review on Opus. (D5)
- R9: `plugin/stages/BUILD.md` shall tell each session its part: build-tests writes and commits the test, build-code writes the code and changes no test file. (D3)
- R10: The close and retro skills shall name `model: haiku`. The requirements and design skills shall keep `opus`, grill and model-routing `sonnet`, build and review `haiku`. (D4, D7)
- R11: The `afk.py` docstring, `.harness/workflows/afk-run.md` and `plugin/harness/.harness/workflows/afk-run.md` shall name the two build sessions and their models. (D3)

## Non-functional needs
State only what a source states. Else: not applicable: <reason>.
- Accessibility: not applicable: no user interface.
- Performance: not applicable: no source states a target.
- Security: not applicable: no new input, secret or permission.
- Observability: not applicable: no new log.

## Assumptions, risks and dependencies
| ID | Kind | Item | Owner |
|---|---|---|---|
| A1 | assumption | A resume does not write a red test again. | Jayson De los Reyes |
| A2 | assumption | The fix round runs on Sonnet: the Opus reviewer's findings are the decision. The `commits` gate flags a test change in a fix. | Jayson De los Reyes |
| A3 | assumption | The `MODELS` keys are `build-tests` and `build-code`, in place of `build`. | design |
| K1 | risk | Haiku fails the close or retro eval gate. Then that skill stays on Sonnet, and the owner decides. | Jayson De los Reyes |
| K2 | risk | Two sessions per slice read the context twice. The `build` eval cost shows the net saving. | design |
| K3 | risk | `plugin/harness/.harness/workflows/afk-run.md` is at 800 of 800 tokens, and `.harness/workflows/afk-run.md` at 989 of 1000. R11 needs cuts, not a higher budget. | design |
| K4 | risk | Sonnet fails to make a test green more often, and blocks more runs. The `build` eval shows it. | design |
| K5 | dependency | The owner approves these requirements, then the design, before build. | Jayson De los Reyes |

## Acceptance criteria
- [ ] With the stub `claude`, each slice gets two sessions in order: build-tests with `--model opus`, then build-code with `--model sonnet`. Each prompt names its one commit. (R1, R4)
- [ ] With the stub `claude`, a build-tests session that makes no `test(T<n>)` commit, and one whose test passes at that commit, each block the task with `T<n>` and start no build-code session. (R2, R3)
- [ ] With the stub `claude`, a build-code session with no `feat(T<n>)` commit, or a feat commit where the done command fails, blocks the task. A green slice gets its `BUILD.md` row. (R5)
- [ ] With the stub `claude`, a resumed run where `T<n>` has a red test commit and no green row starts only build-code for `T<n>`. (R6)
- [ ] With the stub `claude`, the fix round, reviewer, gate check and review sessions run with `--model sonnet`, `opus`, `sonnet` and `opus`. (R7, R8)
- [ ] A test reads `plugin/stages/BUILD.md` and finds the build-tests part and the build-code part, with the rule that build-code changes no test file. (R9)
- [ ] `tests/test_skills.py` pins the model of each skill as in R10. (R10)
- [ ] The `build` eval (`afk_build`) passes each metric at 0.9 or more with the split, and its `summary.md` reports the cost. The `close` and `retro` evals pass their gates on Haiku. (R1, R4, R5, R10)
- [ ] `/kairyn:check` passes, and the three docs of R11 name build-tests on Opus and build-code on Sonnet. (R11)
- [ ] `uv run pytest`, `claude plugin validate plugin` and `python3 scripts/check_version_bump.py origin/main` exit 0. (R1-R11)

## Open questions and answers
- None. The owner confirms A1 and A2 with the approval.

Approval: pending
