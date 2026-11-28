---
task: 2026-11-28-backlog-stage
stage: grill
summary: "Grill of the backlog-stage idea: what part of the idea backlog playbook kairyn still lacks."
---

# Concept: Backlog stage

## Concept
kairyn ships a `backlog` stage, `BACKLOG.md`, that holds the backlog rules now kept only in this repo's `TRIAGE.md`. `/kairyn:idea <request>` captures one idea: it writes the request word for word, a marked AI-draft problem, proposed effort and impact, `status: inbox` and a log line, and creates `docs/backlog/` and its README table if missing. `/kairyn:triage` lists inbox ideas and parked ideas past `review_by`, proposes keep, park or drop, and writes each owner decision with the owner's name. When the owner commits an idea, a script sets `status: committed`, creates the task folder from the idea slug with a `STATE.md` that links the idea, and prints the grill or requirements command. Grill and requirements read the linked idea as the request; there is no pitch step, and init does not change.

## Decisions
- D1: The problem: in a kairyn repo, ideas are captured, triaged, committed and pruned by hand from rules only this repo has (`TRIAGE.md`). Users of the plugin get no backlog rules, and requirements does not start from a committed idea. We know it improved when a user repo can capture an idea and carry it to requirements with shipped steps, and each decision is logged with who made it. (user accepted)
- D2: The first version covers capture, a triage digest, prune and commit. A batch step lists inbox ideas and parked ideas past `review_by`, proposes keep, park or drop, and writes the owner's decisions with the owner's name. No shape or pitch step: grill does the shaping. (user accepted)
- D3: One new stage file `BACKLOG.md` with two skills. `/kairyn:idea <request>` captures one idea. `/kairyn:triage` runs the digest, records keep, park or drop, prunes and commits. `/kairyn:backlog` stays the page. (user accepted)
- D4: The backlog rules move into the shipped `BACKLOG.md` stage. The `/kairyn:idea` script creates `docs/backlog/` and its README table on first capture, if missing. Init does not change. This repo's `TRIAGE.md` keeps only its Next and Parked notes. (user accepted)
- D5: When the owner commits an idea in `/kairyn:triage`, a script sets `status: committed` with the owner's name. It creates `docs/tasks/<date>-<idea slug>/STATE.md` that links the idea, and prints `/kairyn:grill <folder>` or `/kairyn:requirements <folder>`. Both stages read the linked idea's raw request and problem as the request. (user accepted)

## Terms
| Term | Meaning |
|---|---|
| idea | One file `docs/backlog/<YYYYMMDDHHMMSS>-<slug>.md`. |
| committed | Status the owner sets in triage; it starts a task. |
| playbook | `03 Playbooks/SDLC/00 Managing the Idea Backlog.md` in the private knowledge base. |

## Open branches
- None.

Approval: pending
