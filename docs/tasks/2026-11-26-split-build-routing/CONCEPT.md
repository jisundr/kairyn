---
task: 2026-11-26-split-build-routing
stage: grill
summary: "Opus makes each critical decision; Sonnet writes build code to a red Opus test; close and retro go to Haiku. One routing, no switch."
---

# Concept: Opus makes each critical decision, cheaper models carry it out

## Concept
kairyn has one standard model routing. Each step that makes a critical decision runs on Opus: requirements, design, the test commit of each build slice, the AFK reviewer and the final review. Each step that only carries decisions out runs on a cheaper model. In each AFK build slice, an Opus session writes the `test(T<n>)` commit, which fixes the interface, the data shapes and the test cases. A Sonnet session then writes the `feat(T<n>)` commit that makes the test pass, and the red and green checks of `afk.py` enforce the split.

## Decisions
- D1: No bot or solo switch. One standard routing for every repo and run. (user)
- D2: Each step that makes a critical decision stays on Opus. (user)
- D3: Build splits per slice: Opus writes the failing-test commit `test(T<n>)`, which fixes the interface, data shapes and test cases. Sonnet writes the code that makes it green, `feat(T<n>)`. The existing red and green checks enforce the split. (user)
- D4: Skills: requirements Opus, design Opus, grill Sonnet, model-routing Sonnet, close Haiku, retro Haiku. The build and review launchers and the commands stay on Haiku. (user)
- D5: `afk.py` roles: build-tests Opus, build-code Sonnet, reviewer Opus, gate Sonnet, review Opus. (user)
- D6: The reason to record: the orchestrating bot reviews and approves the human-gated steps, so the steps that only carry decisions out get cheaper. Scope, design, the test commit, the review findings and the final review stay on Opus, because a mistake there costs the most. (user)
- D7: Drop the first fixed-routing work where it conflicts: requirements stays on Opus, and the reviewer stays on Opus. Keep close and retro on Haiku. (user)

## Terms
| Term | Meaning |
|---|---|
| build-tests | The `afk.py` session that writes the `test(T<n>)` commit of one slice. |
| build-code | The `afk.py` session that writes the `feat(T<n>)` commit of one slice. |
| critical decision | A choice that later steps take as given: scope, design, test cases and interface, review findings, the final review. |
| routing | The model of each skill (`model:` front matter) and of each `afk.py` role (`MODELS`). |

## Open branches
- None from the grill. Related to the triaged idea split-design-stage (design split for its token budget). That idea stays open.

Approval: Jayson De los Reyes, 2026-11-25T22:35:13Z, "Grill done: routing with split build (option D)"
