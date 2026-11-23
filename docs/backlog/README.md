# Backlog

Options, not commitments. Each file is one idea, named `<YYYYMMDDHHMMSS>-<slug>.md` from its capture time (UTC), following the playbook `knowledge-base/03 Playbooks/SDLC/00 Managing the Idea Backlog.md`. Status: `inbox` → `triaged` → `shaping` → `shaped` → `committed`, or `parked` / `dropped`. Agents capture and draft; a human triages, sets the appetite and commits.

## Triage digest (2026-11-22)

Fourteen ideas are `inbox` and need a keep, park or drop decision. Closed ideas are in `CHANGELOG.md`.

| Idea | Playbook | Depends on | AI note |
|---|---|---|---|
| [Build stage](20261122080759-build-stage.md) | SDLC 03 | design (built, ADR 0006) | Next SDLC gap |
| [Quality gates stage](20261122080759-gates-stage.md) | SDLC 04 | build-stage | May need a CI-reading script |
| [Review and merge stage](20261122080759-review-stage.md) | SDLC 05 | gates-stage | Should own `status: done` |
| [Release and monitoring stage](20261122080759-release-stage.md) | SDLC 06 | review-stage | Maybe optional |
| [Backlog stage](20261122080759-backlog-stage.md) | SDLC 00 | | This file is a manual run of it |
| [Grill in rounds](20261122105739-grill-rounds.md) | Agents | | From Matt Pocock's grilling skill |
| [Approval gates hand off](20261123004258-approval-handoff.md) | Agents | | Grill concept gets an approval line |
| [Retro stage](20261123033554-retro-stage.md) | Agents | | learnings.md at 969/1000 |
| [Plain-English outputs](20261122080759-plain-english-outputs.md) | Agents 01 | | |
| [Pointer-following checks](20261122080759-instruction-file-checks.md) | Agents 02 | | Partly done |
| [Skill checks](20261122103416-skill-checks.md) | Agents 02 | | Bears on the stage-skills task |
| [Multi-repo support](20261122080759-multi-repo.md) | Agents 03 | | Park candidate, no evidence yet |
| [Post-incident review stage](20261123093900-pir-stage.md) | SDLC 07 | release-stage | Park candidate, maybe optional |
| [Parallel learnings conflicts](20261123093900-parallel-learnings.md) | Agents 05 | | Small, inferred, not seen yet |

Rechecked 2026-11-23 against knowledge-base `be5dbfa`: added pir-stage and parallel-learnings; notes on build, gates, review, release and retro. Agents 04 and 06 (loops, bots) add no idea yet: kairyn has no build stage to loop on.
