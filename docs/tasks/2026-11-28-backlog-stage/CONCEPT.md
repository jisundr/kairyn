---
task: 2026-11-28-backlog-stage
stage: grill
summary: "Grill of the backlog-stage idea: what part of the idea backlog playbook kairyn still lacks."
---

# Concept: Backlog stage

## Concept
Not confirmed yet.

## Decisions
- D1: The problem: in a kairyn repo, ideas are captured, triaged, committed and pruned by hand from rules only this repo has (`TRIAGE.md`). Users of the plugin get no backlog rules, and requirements does not start from a committed idea. We know it improved when a user repo can capture an idea and carry it to requirements with shipped steps, and each decision is logged with who made it. (user accepted)
- D2: The first version covers capture, a triage digest, prune and commit. A batch step lists inbox ideas and parked ideas past `review_by`, proposes keep, park or drop, and writes the owner's decisions with the owner's name. No shape or pitch step: grill does the shaping. (user accepted)
- D3: One new stage file `BACKLOG.md` with two skills. `/kairyn:idea <request>` captures one idea. `/kairyn:triage` runs the digest, records keep, park or drop, prunes and commits. `/kairyn:backlog` stays the page. (user accepted)

## Terms
| Term | Meaning |
|---|---|
| idea | One file `docs/backlog/<YYYYMMDDHHMMSS>-<slug>.md`. |
| playbook | `03 Playbooks/SDLC/00 Managing the Idea Backlog.md` in the private knowledge base. |

## Open branches
- Where do the backlog rules live, and how does a user repo get `docs/backlog/`?
- How does requirements start from a committed idea?

Approval: pending
