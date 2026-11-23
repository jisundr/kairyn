# Backlog

Options, not commitments. Each file is one idea, named `<YYYYMMDDHHMMSS>-<slug>.md` from its capture time (UTC), following the playbook `knowledge-base/03 Playbooks/SDLC/00 Managing the Idea Backlog.md`. Status: `inbox` → `triaged` → `shaping` → `shaped` → `committed`, or `parked` / `dropped`. Agents capture and draft; a human triages, sets the appetite and commits.

## Triage digest (2026-11-22)

Twelve ideas are `inbox` and need a keep, park or drop decision. Closed ideas are in `CHANGELOG.md`.

| Idea | Playbook | Depends on | AI note |
|---|---|---|---|
| [Build stage](20261122080759-build-stage.md) | SDLC 03 | design (built, ADR 0006) | Next SDLC gap |
| [Quality gates stage](20261122080759-gates-stage.md) | SDLC 04 | build-stage | May need a CI-reading script |
| [Review and merge stage](20261122080759-review-stage.md) | SDLC 05 | gates-stage | Should own `status: done` |
| [Release and monitoring stage](20261122080759-release-stage.md) | SDLC 06 | review-stage | Maybe optional |
| [Backlog stage](20261122080759-backlog-stage.md) | SDLC 00 | | This file is a manual run of it |
| [Grill in rounds](20261122105739-grill-rounds.md) | Agents | | From Matt Pocock's grilling skill |
| [Approval gates hand off](20261123004258-approval-handoff.md) | Agents | | Grill concept gets an approval line |
| [Eval request hedge](20261123022801-eval-request-hedge.md) | Agents 02 | | Small: reword one eval request |
| [Plain-English outputs](20261122080759-plain-english-outputs.md) | Agents 01 | | |
| [Pointer-following checks](20261122080759-instruction-file-checks.md) | Agents 02 | | Partly done |
| [Skill checks](20261122103416-skill-checks.md) | Agents 02 | | Bears on the stage-skills task |
| [Multi-repo support](20261122080759-multi-repo.md) | Agents 03 | | Park candidate, no evidence yet |


Rechecked 2026-11-22 against knowledge-base `9b65dd9`: added skill-checks. The naming change (`bf874a0`) is already followed. The gate renumbering (`b5cc9bd`) changes no idea.
