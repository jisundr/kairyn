# 19. Hands-on stages run on cheaper models

Date: 2026-11-26

## Status
Accepted. Amends 0004 and 0008.

## Context
The owner asked for cheaper model routing. An orchestrating session on Opus now reviews and approves requirements and judges the reviewer's findings. So the agents that do the hands-on work can run on cheaper models. ADR 0004 put `requirements` on Opus because it failed the 10-run gate on Sonnet.

## Decision
- Skills: `requirements` on Sonnet, `close` and `retro` on Haiku. `design` stays on Opus; `grill` and `model-routing` stay on Sonnet; the build and review launchers and the commands stay on Haiku.
- `afk.py` `MODELS`: build and reviewer on Sonnet, gate on Haiku. The final review stays on Opus.
- Design and the final review stay on Opus, because a mistake there costs the most.

## Consequences
- The Opus orchestrator is the check on Sonnet requirements and on reviewer findings.
- Retro from close runs on Haiku (amends 0008).
- `tests/test_skills.py` and `tests/test_afk.py` pin each model.
