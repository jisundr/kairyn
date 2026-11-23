---
task: 2026-11-23-retro-stage
stage: requirements
summary: "Exit starts an optional retro stage that proposes a home, a drop, a backlog idea or a keep for each learning, then applies it on approval."
---

# Requirements: Retro stage

## Problem statement

Stages append to `.kairyn/learnings.md`, and nothing removes an entry. A durable rule helps only in the file an agent reads at the right time. This repo's `learnings.md` is at 994 of 1000 tokens. Solved when each learning goes to its home or goes, and `learnings.md` stays at most half its budget.

## Scope
In: a `retro` stage and skill that exit starts, with a proposal and approval. (D1, D2, D6)
In: a `retro` eval, the README layout and the harness docs that list stages. (A3)
Out: writing tests or scripts, and cutting or splitting a home. (D3, D10)

## Requirements
- R1: The kairyn plugin shall ship an optional `retro` stage in `plugin/stages/RETRO.md` and a `/kairyn:retro` skill. (D1)
- R2: When `exit.py close` finds `learnings.md` over half its budget, it shall print a `RETRO:` line with the size and the budget. (D6, A1)
- R3: When `exit.py close` prints a `RETRO:` line, the exit stage shall start `/kairyn:retro`. (D5, D6)
- R4: When retro starts, it shall create `docs/tasks/<date>-retro/` with a `STATE.md` and a `RETRO.md`. (D9, A2)
- R5: The retro stage shall give each entry in `learnings.md` exactly one action in `RETRO.md`: move, drop, backlog or keep. (request, D3, D4)
- R6: Where the action is move, `RETRO.md` shall name the home and the text to add. (request)
- R7: The retro stage shall move a learning only into a file that the repo owns or that kairyn never touches. (D7)
- R8: If the home of a learning is a test, a script or a kairyn-owned file, the retro stage shall give it the backlog action. (D3, D7)
- R9: If the repo's `CLAUDE.md` requires an eval before the home changes, the retro stage shall give the learning the backlog action. (D8)
- R10: If a move puts its home over budget, the retro stage shall give the backlog action and name the overflow. (D10)
- R11: Where the action is drop, `RETRO.md` shall give the path that already holds the rule, or why the entry is stale. (request)
- R12: Where the action is keep, `RETRO.md` shall give a one-line reason. (D4)
- R13: While `RETRO.md` has `Approval: Jayson De los Reyes, 2026-11-23T10:19:36Z, "approved, run design"`, the retro stage shall not change a file outside its task folder. (D2)
- R14: When the user approves, the retro stage shall apply each action, remove each entry that is not kept, and record the approval line. (D2)
- R15: Where the action is backlog, the retro stage shall write a `docs/backlog/` idea with status `inbox` that quotes the learning word for word. (D3)
- R16: The retro stage shall not rewrite the text of an entry that it keeps. (request)
- R17: If the kept entries use more than half the `learnings.md` budget, `RETRO.md` shall state the excess and ask the user. (D4, A1)
- R18: The retro stage shall not raise a budget limit. (D10)
- R19: The repo shall have a `retro` eval that checks R4 to R17. (A3)

## Non-functional needs
State only what a source states. Else: not applicable: <reason>.
- Accessibility: not applicable: no source states a need.
- Performance: not applicable: no source states a need.
- Security: not applicable: no source states a need.
- Observability: each retro run logs to its `STATE.md`, like every stage. (A2)

## Assumptions, risks and dependencies
| ID | Kind | Item | Owner |
|---|---|---|---|
| A1 | assumption | The `learnings.md` budget comes from `.harness/budgets.yml`. If no pattern matches, the built-in budget applies (2000 tokens). | design |
| A2 | assumption | The retro `STATE.md` lists only the `retro` stage. Approval sets `status: done`, and `/kairyn:exit` closes the folder after its PR merges. | design |
| A3 | assumption | The `retro` eval uses the gate of the other stage evals: 90% of 10 runs. | Jayson De los Reyes |
| K1 | risk | `EXIT.md` is at 469 of 500 tokens. The step that starts retro must fit, or other text must go. | design |
| K2 | risk | The exit skill has no tool to start a skill, and a started skill can run on the wrong model. Same question as `approval-handoff`. | design |
| K3 | risk | In this repo, the first retro sends most learnings to the backlog: `testing-and-evals.md` is at 1000 of 1000 tokens. | Jayson De los Reyes |
| K4 | dependency | `exit.py` and `budgets.py` in `plugin/scripts/`. | design |

## Acceptance criteria
- [ ] `plugin/stages/RETRO.md` has `optional: true` and the required sections, and `tests/test_static.py` passes. A `/kairyn:retro` skill exists. (R1)
- [ ] A test runs `exit.py close` with `learnings.md` over half its budget and sees a `RETRO:` line. Under half, it sees none. (R2)
- [ ] In the retro eval, exit with a full `learnings.md` ends with a new `docs/tasks/<date>-retro/` folder. (R3, R4)
- [ ] Each `learnings.md` entry appears in `RETRO.md` with one action. (R5)
- [ ] Each move names an existing home that is not kairyn-owned, and the text to add. (R6, R7)
- [ ] The eval gets the backlog action for a test home, a stage that `CLAUDE.md` guards, and a full home. (R8, R9, R10)
- [ ] Each drop names a path or a stale reason. Each keep has a reason. (R11, R12)
- [ ] Before approval, `git status` shows changes only in the retro task folder. (R13)
- [ ] After approval, `learnings.md` holds only the kept entries, and `RETRO.md` has an approval line with the user's name and words. (R14)
- [ ] Each backlog action makes one `inbox` idea that quotes the learning. Kept entries keep their text. (R15, R16)
- [ ] With kept entries over half the budget, `RETRO.md` states the excess and asks the user. (R17)
- [ ] After a run, `.harness/budgets.yml` has no change. (R18)
- [ ] `evals/promptfoo/retro.yaml` exists and passes its gates at 10 runs. (R19)

## Open questions and answers
- None: see D1 to D10 in `CONCEPT.md`.

Approval: Jayson De los Reyes, 2026-11-23T10:19:36Z, "approved, run design"
