---
task: 2026-11-22-grill-me
stage: requirements
summary: "kairyn's own grilling: one hard question at a time until user and agent share one concept. Optional grill stage plus /kairyn:grill."
---

# Requirements: Grilling before the spec

## Problem statement

The user asked for kairyn's own version of the "grill me" technique. The agent interviews the user with hard questions, one at a time, until both hold the same concept. This happens before a spec exists. Today requirements step 4 asks only what the repo cannot answer, in one batch. So misalignment reaches the spec unseen. The user also asked where in kairyn's SDLC grilling runs.

Sources: knowledge-base topic `Grilling Session` and its source note, playbook SDLC 00 (step 6, shape) and SDLC 01 (steps 3 and 4).

## Grilling compared with requirements step 4

| | Requirements step 4 | Grilling |
|---|---|---|
| Goal | Close gaps the repo cannot close | One shared concept |
| Questions | Few, in one batch | One at a time, down every branch of the decision tree |
| Agent | Asks | Proposes an answer, challenges vague terms and solution-first requests |
| Ends when | No open questions | The user confirms the agent's restated concept |
| Output | Answers in `REQUIREMENTS.md` | Decisions and terms in their own file |

## Where it runs: options

| Option | For | Against |
|---|---|---|
| A. A step in `requirements` | Runs on every task. No new stage. | Long interview for small tasks. Stage budget is 500 tokens. Changes the requirements eval. |
| B. Optional stage `grill`, like `MODEL-ROUTING` | Opt-in. Own eval. Writes a file that requirements reads. | Runs before requirements, so it must create the task folder (A7). The user must remember it. |
| C. Command `/kairyn:grill` | Easy to find. Runs on any topic, also mid-task. | The instructions still need a stage file. A command alone keeps no task state. |
| D. Backlog shaping (SDLC 00, step 6) | The playbook links grilling to shaping. | No backlog stage exists yet ([backlog-stage](../../backlog/20261122080759-backlog-stage.md)). Shaping fixes the problem and appetite, not spec detail. |

**Decision (user, Q1): B + C.** One optional stage keeps small tasks short, and `/kairyn:grill` makes it easy to find. Later, the backlog stage runs the same stage in its shaping step (D).

## Scope

**In**
- `plugin/stages/GRILL.md`, installed to `.kairyn/stages/`, our own text.
- Output `docs/tasks/<YYYY-MM-DD>-<slug>/CONCEPT.md` (A6).
- `plugin/commands/grill.md`, a thin command that runs the stage (A10).
- Requirements step 4 reads `CONCEPT.md` when it exists.
- An eval for the stage, version bump, `release-hashes.json`, harness docs and budgets.

**Out**
- A project-wide `GLOSSARY.md` (A8).
- The backlog stage, and the other gaps in [requirements-gaps](../../backlog/20261122080759-requirements-gaps.md) (EARS, approval line).
- Text copied from another project's skill.

## Assumptions

- A1: The agent reads the repo before each question. It never asks what the code answers.
- A2: Each question carries the agent's recommended answer and the reason. The user accepts, changes or rejects it.
- A3: The agent writes each answer to `CONCEPT.md` at once, so a fresh context can continue the interview.
- A4: Each term gets one meaning, recorded in `CONCEPT.md` (ASD-STE100: same term, same thing).
- A5: The interview ends when the user confirms the concept, restated in at most 5 sentences. The user can also stop it; open branches stay listed.
- A6: Stage name `grill`, output `CONCEPT.md`: concept, decisions `D1`, `D2`, terms, open branches.
- A7: If the task folder does not exist, the stage creates it and `STATE.md`, as requirements step 1 does.
- A8: Terms stay in the task. A project glossary is a later idea.
- A9: Repo rules apply: the eval fails first, and `plugin.json` gets a new version.
- A10: `/kairyn:grill` takes a topic or a task folder. A topic starts a new task. A folder continues that task.

## Acceptance criteria

- [ ] The agent asks no question that a repo file answers. (A1)
- [ ] Each message asks one question and gives a recommended answer with a reason. (request, A2)
- [ ] The agent challenges each vague term and each request that names a solution but no problem. (request)
- [ ] After each answer, `CONCEPT.md` holds the decision. (A3)
- [ ] `CONCEPT.md` has a concept, decisions, terms with one meaning each, and open branches. (A4, A6)
- [ ] The interview ends only on the user's confirmation or stop. (A5)
- [ ] When `CONCEPT.md` exists, requirements asks no question it answers. (A6)
- [ ] The stage has `optional: true` and adds `grill` to the task's `stages`. (request, Q1)
- [ ] `/kairyn:grill <topic>` starts the stage in a new task folder. `/kairyn:grill <task folder>` continues that task. (request, A10)
- [ ] No sentence in the stage comes from another project's skill. (request)
- [ ] The stage eval fails before the stage exists and passes after. `uv run pytest` and `claude plugin validate plugin` pass. (A9)

## Open questions and answers

1. Where does grilling run: A, B, C or D? **Answered (user):** B + C, an optional stage and a command that runs it.
