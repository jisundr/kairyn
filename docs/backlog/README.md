# Backlog

Options, not commitments. Each file is one idea, named `<YYYYMMDDHHMMSS>-<slug>.md` from its capture time (UTC), following the playbook `knowledge-base/03 Playbooks/SDLC/00 Managing the Idea Backlog.md`. Status: `inbox` → `triaged` → `shaping` → `shaped` → `committed`, or `parked` / `dropped`. Agents capture and draft; a human triages, sets the appetite and commits.

## Triage digest (2026-11-22)

Eleven ideas are `inbox` and need a keep, park or drop decision. Requirements gaps is `committed` to task `2026-11-22-requirements-gaps`. Grill in requirements is `dropped`: #17 shipped it. Problem statements are AI drafts.

| Idea | Playbook | Depends on | AI note |
|---|---|---|---|
| [Design stage](20261122080759-design-stage.md) | SDLC 02 | | Named as next gap in learnings |
| [Build stage](20261122080759-build-stage.md) | SDLC 03 | design-stage | |
| [Quality gates stage](20261122080759-gates-stage.md) | SDLC 04 | build-stage | May need a CI-reading script |
| [Review and merge stage](20261122080759-review-stage.md) | SDLC 05 | gates-stage | Should own `status: done` |
| [Release and monitoring stage](20261122080759-release-stage.md) | SDLC 06 | review-stage | Maybe optional |
| [Backlog stage](20261122080759-backlog-stage.md) | SDLC 00 | | This file is a manual run of it |
| [Requirements gaps](20261122080759-requirements-gaps.md) | SDLC 01 | | Approval line first |
| [Grill in requirements](20261122104150-grill-requirements.md) | SDLC 01 | | Dropped |
| [Grill in rounds](20261122105739-grill-rounds.md) | Agents | | From Matt Pocock's grilling skill |
| [Plain-English outputs](20261122080759-plain-english-outputs.md) | Agents 01 | | |
| [Pointer-following checks](20261122080759-instruction-file-checks.md) | Agents 02 | | Partly done |
| [Skill checks](20261122103416-skill-checks.md) | Agents 02 | | Bears on the stage-agents task |
| [Multi-repo support](20261122080759-multi-repo.md) | Agents 03 | | Park candidate, no evidence yet |

Merged: "task is marked `done` after requirements only" into [design-stage](20261122080759-design-stage.md). Not added: `Inference/01 Adding Model Routing`, already the optional `MODEL-ROUTING` stage.

Rechecked 2026-11-22 against knowledge-base `9b65dd9`: added skill-checks. The naming change (`bf874a0`) is already followed. The gate renumbering (`b5cc9bd`) changes no idea.
