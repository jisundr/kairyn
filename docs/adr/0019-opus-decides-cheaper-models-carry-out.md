# 19. Opus makes each critical decision, cheaper models carry it out

Date: 2026-11-26

## Status
Accepted. Amends [ADR 4](0004-stage-skills-with-a-model-per-stage.md) and [ADR 8](0008-exit-runs-retro-on-a-full-learnings-file.md).

## Context
Task 2026-11-26-split-build-routing. One Opus session wrote both commits of each AFK build slice. The `test(T<n>)` commit holds the decisions: test cases, interface, data shapes. The `feat(T<n>)` commit only makes a red test green. An orchestrating bot now reviews and approves the human-gated steps, so the steps that only carry decisions out can get cheaper (D6). A mistake in scope, design, the test commit, the review findings or the final review costs the most.

## Decision
- One standard routing for every repo and run. No bot or solo switch (D1).
- Each critical decision stays on Opus: requirements, design, the test commit, the AFK reviewer and the final review (D2, D7).
- `afk.py` builds each slice in two sessions: build-tests on Opus writes `test(T<n>)`, then build-code on Sonnet writes `feat(T<n>)`. The red check runs between them. The fix round runs on Sonnet; the gate checks on Sonnet (D3, D5, A2).
- Skills: requirements and design on Opus; grill, model-routing, close and retro on Sonnet; the build and review launchers on Haiku (D4, D8).
- K1: retro failed its eval on Haiku (run 20261125T230159Z: `retro_proposes` 5/10, `retro_applies` 7/10). A retro that close starts runs on close's model (ADR 8), so close and retro both stay on Sonnet (D8).

## Consequences
- A bad test stops the slice before the Sonnet session starts.
- Two sessions read the slice context twice (K2). The `afk_build` eval cost $7.45 at 10 runs; the last all-Opus run cost $4.67.
- Retro on Sonnet passed its eval gate (run 20261125T232531Z).
- The triaged idea split-design-stage stays open.
