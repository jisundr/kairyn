---
task: 2026-11-23-retro-stage
stage: grill
summary: "Retro moves each learning to the file where an agent reads it at the right time, or drops it, after the user approves."
---

# Concept: Retro stage

## Concept
Retro is an optional plugin stage that keeps `.kairyn/learnings.md` under half its budget. It gives each learning one action: move it to its home, drop it, turn it into a backlog idea, or keep it with a reason. `exit.py close` starts retro when `learnings.md` passes half its budget, and each run gets its own task folder with `STATE.md` and a `RETRO.md` proposal. Retro changes nothing outside that folder until the user approves in chat. A home is a file the repo owns or kairyn never touches. Other homes become backlog ideas: tests, scripts, kairyn-owned files, stages in this repo and full homes.

## Decisions
- D1: Retro ships in the plugin as an optional stage with a `/kairyn:retro` skill, like exit. (user accepted)
- D2: Retro writes a proposal and waits for approval in chat. It changes no file outside the task folder before approval. (user accepted)
- D3: A learning whose home is a test or a script becomes a backlog idea. Retro writes no code. (user accepted)
- D4: A learning can stay when no home fits, with a one-line reason. After retro, `learnings.md` is at most half its budget. (user accepted)
- D5: Retro is part of the exit flow. The user does not need to remember to run it. (user)
- D6: Retro is a separate stage. When `exit.py close` finds `learnings.md` past half its budget, exit starts `/kairyn:retro`. (user accepted)
- D7: A home is a file the repo owns or kairyn never touches: `.kairyn/stages/*.md`, the user's own `.harness/` docs, `CLAUDE.md` outside the kairyn block. A learning whose home is a kairyn-owned file becomes a backlog idea. (user accepted)
- D8: Retro has no special case for the kairyn repo. It follows the repo's `CLAUDE.md`. Here, a learning whose home is a stage becomes a backlog idea, because a change to `plugin/` instructions needs an eval first. (user accepted)
- D9: Each retro run has its own task folder `docs/tasks/<date>-retro/` with `STATE.md` and `RETRO.md`. `/kairyn:exit` closes it after its PR merges. (user accepted)
- D10: Retro checks each home with `budgets.py`. If a move pushes the home over budget, the action becomes a backlog idea that names the home and the overflow. Retro never raises a limit. (user accepted)

## Terms
| Term | Meaning |
|---|---|
| learning | One `- <date> [<stage>] <text>` entry in `.kairyn/learnings.md` |
| home | The file where an agent reads a rule at the time it needs it |
| action | What retro does with one learning: move, drop, backlog or keep |

## Open branches
- None
