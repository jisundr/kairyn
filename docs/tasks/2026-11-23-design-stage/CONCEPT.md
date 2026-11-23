---
task: 2026-11-23-design-stage
stage: grill
summary: "Concept for a kairyn design stage between requirements and code. Confirmed by the user."
---

## Concept
kairyn gets a required `design` stage after requirements, run by `/kairyn:design` on Opus. It reads the approved requirements and the code, then writes `DESIGN.md` with four sections: Approach, Options, Tasks and Test plan. It stops once: the user approves in chat or names another option, and the stage rewrites the file. Requirements now hands every task to design, and design approval marks the task `done` until a build stage exists. A two-scenario eval with the requirements gates proves it, and its new `grounded` check rejects plans that name missing files.

## Decisions
- D1: The task adds a real planning stage. The stage reads the approved requirements, proposes approaches, and writes `DESIGN.md` with tasks and a test plan. Requirements no longer marks the task `done` when design follows. (user accepted)
- D2: The stage name is `design`, not `plan`. The stage chooses an approach, and `plan` collides with Claude Code plan mode. Output is `DESIGN.md`, command is `/kairyn:design`. (user accepted)
- D3: The stage stops once. It writes the full `DESIGN.md` for its recommended approach and lists the other options with trade-offs. The user approves in chat, as for requirements, or names another option and the stage rewrites the file. (user)
- D4: Design is a required SDLC stage after requirements. Requirements always sets `stage: design` and never `status: done`. While no build stage exists, design is the last stage, so its approval sets `status: done` (rule from `task-lifecycle.md`). (user)
- D5: `DESIGN.md` has four sections: Approach (chosen option and why), Options (rejected options with cost and risk, one is the smallest thing), Tasks (ordered by dependency, each with a done condition), Test plan (each acceptance criterion to a task and a test). Standards impact waits for the gates stage. (user accepted)
- D6: The design skill runs on Opus. A move to Sonnet needs a 10-run eval pass first. (user accepted)
- D7: The design eval has two scenarios on a fixture task with approved requirements. Scenario 1 checks well_formed, traceable, options, grounded (each named file exists) and waits_for_approval, plus a judge for no_invention and plan quality. Scenario 2 checks that a non-approval is ignored, that "go with option B" makes a rewrite, and that approval sets `status: done`. Gates are as for requirements: 0.9 pass rate over 10 runs, judge mean 4. The requirements eval then expects `stage: design` after approval. (user accepted)

## Terms
| Term | Meaning |
|---|---|
| design stage | The required kairyn stage that runs after approved requirements and writes `DESIGN.md`. |
| option | One possible approach, with its cost and risk. One option is always the smallest thing. |
| test plan | The map from each acceptance criterion to a task and a test. |
| grounded | Each file path that `DESIGN.md` names exists in the repo. |

## Open branches
None
